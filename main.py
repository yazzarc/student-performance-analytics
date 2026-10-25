"""Run with: python main.py"""

import argparse
from pathlib import Path
import sys

try:
    from functions import (
        build_report,
        calculate_results,
        class_summary,
        grade_distribution,
        load_students,
        save_reports,
        subject_analysis,
        top_performers,
    )
except ModuleNotFoundError as error:
    if error.name not in {"numpy", "pandas"}:
        raise
    print("Missing NumPy or Pandas. Run: python -m pip install -r requirements.txt", file=sys.stderr)
    raise SystemExit(1) from None


BASE_DIR = Path(__file__).resolve().parent


def positive_integer(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("Enter a positive integer.")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description="Calculate student results and save class reports.")
    parser.add_argument("--data", type=Path, default=BASE_DIR / "students.csv", help="CSV to analyse (default: bundled students.csv)")
    parser.add_argument("--output", type=Path, default=BASE_DIR / "reports", help="Folder for generated reports")
    parser.add_argument("--top", type=positive_integer, default=5, help="Number of top students, including ties (default: 5)")
    args = parser.parse_args(argv)

    try:
        # Do not allow a generated report to overwrite the source dataset.
        report_names = ["student_results.csv", "subject_analysis.csv", "class_summary.csv", "top_performers.csv", "grade_distribution.csv", "analysis_report.txt"]
        if args.data.resolve() in [(args.output / name).resolve() for name in report_names]:
            raise ValueError("Choose an output folder that will not overwrite the input dataset.")
        students = load_students(args.data)
        results = calculate_results(students)
        subjects = subject_analysis(results)
        summary = class_summary(results)
        top = top_performers(results, args.top)
        grades = grade_distribution(results)
        report = build_report(students, results, subjects, summary, top, grades, args.data.name, args.top)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(report)
    try:
        save_reports(args.output, results, subjects, summary, top, grades, report)
    except OSError as error:
        print(f"Analysis completed, but reports could not be fully saved: {error}", file=sys.stderr)
        return 1
    print(f"Reports saved in: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
