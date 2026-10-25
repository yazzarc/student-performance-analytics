"""Load student data and calculate the figures used in the report."""

import csv
from pathlib import Path

import numpy as np
import pandas as pd


SUBJECTS = ["Python", "Mathematics", "Statistics", "English", "Computer_Basics"]
REQUIRED_COLUMNS = ["Student_ID", "Name", "Department", *SUBJECTS, "Attendance"]
PASS_MARK = 40
MIN_ATTENDANCE = 75
GRADE_ORDER = ["A+", "A", "B", "C", "D", "E", "F"]


def load_students(file_path):
    """Read a CSV and reject incomplete, duplicate or invalid records."""
    file_path = Path(file_path)
    # Pandas can rename duplicate headers or treat an extra field as an index.
    # Check the CSV structure first so those mistakes are reported clearly.
    try:
        with file_path.open(encoding="utf-8-sig", newline="") as source:
            reader = csv.reader(source, strict=True)
            headers = next(reader, [])
            headers = [column.strip() for column in headers]
            if not headers:
                raise ValueError("The CSV file is empty.")
            if len(headers) != len(set(headers)):
                raise ValueError("The CSV contains duplicate column names.")
            missing = [column for column in REQUIRED_COLUMNS if column not in headers]
            if missing:
                raise ValueError("Missing columns: " + ", ".join(missing))
            for row in reader:
                if row and len(row) != len(headers):
                    raise ValueError(
                        f"CSV row ending at line {reader.line_num} has {len(row)} fields; "
                        f"expected {len(headers)}."
                    )
        students = pd.read_csv(file_path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except (UnicodeDecodeError, csv.Error, pd.errors.ParserError) as error:
        raise ValueError(f"Cannot read the CSV. Save it as UTF-8 with comma-separated columns. {error}") from error

    students.columns = headers
    students = students[REQUIRED_COLUMNS].copy()
    if students.empty:
        raise ValueError("The CSV needs at least one student record.")

    for column in REQUIRED_COLUMNS:
        students[column] = students[column].str.strip()
        empty_rows = students.index[students[column].eq("")].tolist()
        if empty_rows:
            positions = ", ".join(str(index + 1) for index in empty_rows)
            raise ValueError(f"{column} is blank in student record(s): {positions}.")

    duplicate_ids = students["Student_ID"].str.casefold().duplicated(keep=False)
    if duplicate_ids.any():
        ids = ", ".join(students.loc[duplicate_ids, "Student_ID"])
        raise ValueError(f"Student IDs must be unique. Repeated IDs: {ids}.")

    for column in [*SUBJECTS, "Attendance"]:
        values = pd.to_numeric(students[column], errors="coerce")
        invalid = ~np.isfinite(values) | ~values.between(0, 100)
        if invalid.any():
            ids = ", ".join(students.loc[invalid, "Student_ID"])
            raise ValueError(f"{column} must be a number from 0 to 100. Check: {ids}.")
        students[column] = values
    return students


def assign_grade(average, passed):
    """A failed subject overrides the grade calculated from the average."""
    if not passed:
        return "F"
    for minimum, grade in [(90, "A+"), (80, "A"), (70, "B"), (60, "C"), (50, "D"), (40, "E")]:
        if average >= minimum:
            return grade
    return "F"


def calculate_results(students):
    """Add calculated columns to validated data without changing the input."""
    results = students.copy()
    marks = results[SUBJECTS].to_numpy(dtype=float)
    results["Total"] = np.sum(marks, axis=1)
    results["Average"] = np.mean(marks, axis=1)
    passed = np.all(marks >= PASS_MARK, axis=1)
    results["Result"] = np.where(passed, "Pass", "Fail")
    # Use full precision here; rounding is only for display and CSV export.
    results["Grade"] = [assign_grade(average, status) for average, status in zip(results["Average"], passed)]
    results["Attendance_Status"] = np.where(results["Attendance"] >= MIN_ATTENDANCE, "Regular", "Low")
    results["Failed_Subjects"] = [
        ", ".join(subject for subject in SUBJECTS if row[subject] < PASS_MARK)
        for _, row in results.iterrows()
    ]
    return results


def subject_analysis(results):
    rows = []
    for subject in SUBJECTS:
        marks = results[subject].to_numpy(dtype=float)
        passed = int(np.count_nonzero(marks >= PASS_MARK))
        rows.append({
            "Subject": subject,
            "Highest": float(np.max(marks)),
            "Lowest": float(np.min(marks)),
            "Average": float(np.mean(marks)),
            "Passed": passed,
            "Failed": len(marks) - passed,
            "Pass_Percentage": passed / len(marks) * 100,
        })
    return pd.DataFrame(rows)


def class_summary(results):
    averages = results["Average"].to_numpy(dtype=float)
    passed = int(results["Result"].eq("Pass").sum())
    return {
        "Students": len(results),
        "Passed": passed,
        "Failed": len(results) - passed,
        "Pass percentage": passed / len(results) * 100,
        "Class average": float(np.mean(averages)),
        "Highest average": float(np.max(averages)),
        "Lowest average": float(np.min(averages)),
        "Median average": float(np.median(averages)),
        "Average attendance": float(np.mean(results["Attendance"].to_numpy(dtype=float))),
        "Low attendance count": int(results["Attendance_Status"].eq("Low").sum()),
    }


def top_performers(results, limit=5):
    """Rank by average, including everyone tied at the last selected place."""
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("The top-student count must be a positive integer.")
    ranked = results.copy()
    ranked.insert(0, "Rank", ranked["Average"].rank(method="min", ascending=False).astype(int))
    return ranked[ranked["Rank"] <= limit].sort_values(["Rank", "Student_ID"]).reset_index(drop=True)


def grade_distribution(results):
    return results["Grade"].value_counts().reindex(GRADE_ORDER, fill_value=0).rename_axis("Grade").reset_index(name="Students")


def build_report(students, results, subjects, summary, top, grades, source_name, limit):
    """Build the same readable report for the terminal and the text file."""
    lines = [
        "STUDENT PERFORMANCE ANALYTICS SYSTEM",
        "=" * 72,
        f"Dataset: {source_name}",
        "Sample data is fictional when using the supplied students.csv.",
        f"Pass: at least {PASS_MARK} in every subject. Marks are out of 100.",
        "Grades: A+ >=90, A >=80, B >=70, C >=60, D >=50, E >=40.",
        "Any failed subject gives grade F, even when the average is high.",
        f"Attendance below {MIN_ATTENDANCE}% is flagged separately; it does not change the result.",
        "Grades and ranking use unrounded averages. Display uses two decimals.",
    ]

    def section(title, body):
        lines.extend(["", title, "-" * len(title), body])

    def table(frame):
        return frame.to_string(index=False, float_format=lambda value: f"{value:.2f}")

    information = pd.DataFrame({"Column": students.columns, "Type": students.dtypes.astype(str).tolist()})
    section("DATASET CHECK", f"Student records: {len(students)}\nColumns: {len(students.columns)}\nMissing values: 0\n" + table(information))
    section("LOADED DATA", table(students))
    result_columns = ["Student_ID", "Name", "Department", "Total", "Average", "Grade", "Result", "Attendance", "Attendance_Status"]
    section("STUDENT RESULTS (TOTAL OUT OF 500)", table(results[result_columns]))
    summary_lines = [f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}" for key, value in summary.items()]
    section("CLASS SUMMARY (MARKS OUT OF 100; ATTENDANCE AND PASS RATE IN %)", "\n".join(summary_lines))

    highest = results.loc[results["Average"] == summary["Highest average"], ["Student_ID", "Name", "Average"]]
    lowest = results.loc[results["Average"] == summary["Lowest average"], ["Student_ID", "Name", "Average"]]
    section("HIGHEST AVERAGE", table(highest))
    section("LOWEST AVERAGE", table(lowest))
    section("SUBJECT ANALYSIS (MARKS OUT OF 100)", table(subjects))
    best = subjects.loc[subjects["Average"] == subjects["Average"].max(), "Subject"].tolist()
    lines.append("Best subject average: " + ", ".join(best))
    section(f"TOP {limit} STUDENTS BY AVERAGE (INCLUDING TIES)", table(top[["Rank", *result_columns]]))
    section("GRADE DISTRIBUTION", table(grades))

    failed = results.loc[results["Result"] == "Fail", ["Student_ID", "Name", "Failed_Subjects"]]
    section("STUDENTS WITH FAILED SUBJECTS", "None." if failed.empty else table(failed))
    low_attendance = results.loc[results["Attendance_Status"] == "Low", ["Student_ID", "Name", "Attendance", "Result"]]
    section("LOW ATTENDANCE", "None." if low_attendance.empty else table(low_attendance))
    return "\n".join(lines) + "\n"


def save_reports(output_dir, results, subjects, summary, top, grades, report):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "student_results.csv": results,
        "subject_analysis.csv": subjects,
        "class_summary.csv": pd.DataFrame(summary.items(), columns=["Metric", "Value"]),
        "top_performers.csv": top,
        "grade_distribution.csv": grades,
    }
    for name, frame in files.items():
        frame.to_csv(output_dir / name, index=False, float_format="%.2f", encoding="utf-8")
    (output_dir / "analysis_report.txt").write_text(report, encoding="utf-8")
