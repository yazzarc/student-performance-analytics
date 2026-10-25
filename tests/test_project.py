"""Run from the project folder with: python -m unittest discover -s tests -v"""

import csv
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import pandas as pd

from functions import (
    REQUIRED_COLUMNS, SUBJECTS, assign_grade, calculate_results,
    class_summary, grade_distribution, load_students, subject_analysis, top_performers,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]


def student(student_id="001", marks=None, attendance=75):
    if marks is None:
        marks = [80, 70, 60, 90, 50]
    return dict(zip(REQUIRED_COLUMNS, [student_id, "Test Student", "BCA", *marks, attendance]))


class DataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=PROJECT_DIR)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "data.csv"

    def write_rows(self, rows, columns=REQUIRED_COLUMNS):
        with self.path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)

    def test_ids_are_text_and_whitespace_is_trimmed(self):
        row = student()
        row["Name"] = "  Nisha, Rao  "
        self.write_rows([row])
        data = load_students(self.path)
        self.assertEqual(data.loc[0, "Student_ID"], "001")
        self.assertEqual(data.loc[0, "Name"], "Nisha, Rao")

    def test_empty_and_header_only_files(self):
        for content in ["", ",".join(REQUIRED_COLUMNS) + "\n"]:
            with self.subTest(content=content):
                self.path.write_text(content, encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_students(self.path)

    def test_missing_and_duplicate_columns(self):
        for headers in [REQUIRED_COLUMNS[:-1], REQUIRED_COLUMNS + ["Name"]]:
            with self.subTest(headers=headers):
                self.path.write_text(",".join(headers) + "\n", encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_students(self.path)

    def test_invalid_marks_and_attendance(self):
        for column in ["Python", "Attendance"]:
            for value in ["", "  ", "absent", "NaN", "inf", "-inf", -1, 101]:
                with self.subTest(column=column, value=value):
                    row = student()
                    row[column] = value
                    self.write_rows([row])
                    with self.assertRaisesRegex(ValueError, column):
                        load_students(self.path)

    def test_missing_identity_fields(self):
        for column in ["Student_ID", "Name", "Department"]:
            with self.subTest(column=column):
                row = student()
                row[column] = " "
                self.write_rows([row])
                with self.assertRaisesRegex(ValueError, column):
                    load_students(self.path)

    def test_duplicate_ids_ignore_case_and_spaces(self):
        self.write_rows([student("S001"), student(" s001 ")])
        with self.assertRaisesRegex(ValueError, "unique"):
            load_students(self.path)

    def test_extra_and_missing_csv_fields(self):
        for values in [list(student().values()) + ["extra"], list(student().values())[:-1]]:
            with self.subTest(values=values):
                self.path.write_text(",".join(REQUIRED_COLUMNS) + "\n" + ",".join(map(str, values)), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "fields"):
                    load_students(self.path)

    def test_bom_and_decimal_values(self):
        self.write_rows([student(marks=[0, 100, 40.5, 60, 70], attendance=74.9)])
        self.path.write_bytes(b"\xef\xbb\xbf" + self.path.read_bytes())
        data = load_students(self.path)
        self.assertEqual(data.loc[0, "Statistics"], 40.5)
        self.assertEqual(data.loc[0, "Attendance"], 74.9)

    def test_invalid_encoding_and_unclosed_quote(self):
        self.path.write_bytes(b"\xff\xfe\xfa")
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            load_students(self.path)
        self.path.write_text(",".join(REQUIRED_COLUMNS) + '\n001,"unfinished', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Cannot read"):
            load_students(self.path)


class CalculationTests(unittest.TestCase):
    def test_grade_boundaries_and_failed_subject_override(self):
        cases = [(100, "A+"), (90, "A+"), (89.999, "A"), (80, "A"),
                 (79.999, "B"), (70, "B"), (69.999, "C"), (60, "C"),
                 (59.999, "D"), (50, "D"), (49.999, "E"), (40, "E"), (39.999, "F")]
        for average, grade in cases:
            with self.subTest(average=average):
                self.assertEqual(assign_grade(average, True), grade)
                self.assertEqual(assign_grade(average, False), "F")

    def test_known_calculations_and_input_is_unchanged(self):
        data = pd.DataFrame([student()])
        original = data.copy(deep=True)
        result = calculate_results(data).iloc[0]
        self.assertEqual(result["Total"], 350)
        self.assertEqual(result["Average"], 70)
        self.assertEqual(result["Grade"], "B")
        self.assertEqual(result["Result"], "Pass")
        pd.testing.assert_frame_equal(data, original)

    def test_pass_and_attendance_boundaries(self):
        rows = [student("1", [40] * 5, 75), student("2", [100, 100, 39, 100, 100], 74.99)]
        result = calculate_results(pd.DataFrame(rows))
        self.assertEqual(result["Result"].tolist(), ["Pass", "Fail"])
        self.assertEqual(result["Grade"].tolist(), ["E", "F"])
        self.assertEqual(result["Attendance_Status"].tolist(), ["Regular", "Low"])
        self.assertEqual(result.loc[1, "Failed_Subjects"], "Statistics")
        low_attendance_pass = calculate_results(pd.DataFrame([student(attendance=0)]))
        self.assertEqual(low_attendance_pass.loc[0, "Result"], "Pass")

    def test_rounding_does_not_promote_grade(self):
        results = calculate_results(pd.DataFrame([student(marks=[89.999] * 5)]))
        self.assertEqual(round(results.loc[0, "Average"], 2), 90)
        self.assertEqual(results.loc[0, "Grade"], "A")

    def test_ties_at_cutoff_are_kept(self):
        rows = [student(str(index), [mark] * 5) for index, mark in enumerate([90, 80, 80, 70])]
        top = top_performers(calculate_results(pd.DataFrame(rows)), 2)
        self.assertEqual(top["Rank"].tolist(), [1, 2, 2])
        self.assertEqual(len(top), 3)

    def test_one_student_all_pass_and_all_fail(self):
        for mark, expected in [(100, 100), (0, 0)]:
            with self.subTest(mark=mark):
                results = calculate_results(pd.DataFrame([student(marks=[mark] * 5)]))
                summary = class_summary(results)
                self.assertEqual(summary["Pass percentage"], expected)
                self.assertEqual(summary["Class average"], mark)
                self.assertEqual(len(top_performers(results, 5)), 1)
                self.assertTrue((subject_analysis(results)["Pass_Percentage"] == expected).all())

    def test_sample_results(self):
        results = calculate_results(load_students(PROJECT_DIR / "students.csv"))
        summary = class_summary(results)
        self.assertEqual(summary["Students"], 24)
        self.assertEqual(summary["Passed"], 18)
        self.assertEqual(summary["Failed"], 6)
        self.assertAlmostEqual(summary["Class average"], 8321 / 120)
        self.assertEqual(summary["Highest average"], 94)
        self.assertEqual(summary["Lowest average"], 33)
        self.assertEqual(summary["Median average"], 73.5)
        self.assertEqual(summary["Low attendance count"], 6)
        self.assertEqual(grade_distribution(results)["Students"].tolist(), [3, 7, 3, 2, 1, 2, 6])
        self.assertEqual(top_performers(results)["Rank"].tolist(), [1, 2, 2, 4, 5, 5])
        subjects = subject_analysis(results).set_index("Subject")
        self.assertEqual(subjects.loc["English", "Passed"], 24)
        self.assertAlmostEqual(subjects.loc["English", "Average"], 73.625)
        self.assertEqual(subjects.loc["Mathematics", "Failed"], 4)


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=PROJECT_DIR)
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def run_cli(self, *arguments):
        return subprocess.run([sys.executable, str(PROJECT_DIR / "main.py"), *map(str, arguments)],
                              cwd=self.folder, capture_output=True, text=True, encoding="utf-8")

    def test_run_from_another_folder_and_export_contents(self):
        output = self.folder / "saved reports"
        completed = self.run_cli("--output", output)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(len(list(output.iterdir())), 6)
        self.assertIn("Class average: 69.34", completed.stdout)
        report = (output / "analysis_report.txt").read_text(encoding="utf-8")
        self.assertIn("Meera Nair", report)
        self.assertIn("Best subject average: English", report)
        self.assertEqual(len(pd.read_csv(output / "student_results.csv")), 24)
        self.assertEqual(len(pd.read_csv(output / "top_performers.csv")), 6)
        self.assertEqual(len(pd.read_csv(output / "subject_analysis.csv")), 5)
        summary = pd.read_csv(output / "class_summary.csv").set_index("Metric")["Value"]
        self.assertEqual(summary["Passed"], 18)
        self.assertEqual(summary["Class average"], 69.34)

    def test_missing_data_has_clear_error(self):
        completed = self.run_cli("--data", "missing.csv")
        self.assertEqual(completed.returncode, 1)
        self.assertIn("Error:", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_invalid_top_count(self):
        for count in ["0", "-1", "hello"]:
            with self.subTest(count=count):
                completed = self.run_cli("--top", count)
                self.assertEqual(completed.returncode, 2)
                self.assertNotIn("Traceback", completed.stderr)

    def test_output_path_is_a_file(self):
        target = self.folder / "file.txt"
        target.write_text("Keep this content", encoding="utf-8")
        completed = self.run_cli("--output", target)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("could not be fully saved", completed.stderr)
        self.assertEqual(target.read_text(encoding="utf-8"), "Keep this content")

    def test_input_cannot_be_overwritten_by_output(self):
        source = self.folder / "student_results.csv"
        original = (PROJECT_DIR / "students.csv").read_bytes()
        source.write_bytes(original)
        completed = self.run_cli("--data", source, "--output", self.folder)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("overwrite", completed.stderr)
        self.assertEqual(source.read_bytes(), original)

    def test_custom_data_and_more_top_places_than_students(self):
        source = self.folder / "one student.csv"
        pd.DataFrame([student(marks=[40] * 5)]).to_csv(source, index=False)
        output = self.folder / "results"
        completed = self.run_cli("--data", source, "--output", output, "--top", "10")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(len(pd.read_csv(output / "top_performers.csv")), 1)


if __name__ == "__main__":
    unittest.main()
