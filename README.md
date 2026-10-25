# Student Performance Analytics System

**Name:** YASH KUMAR  
**Course:** Python with AI

A small Python project that reads student marks from a CSV file and produces a
class report. It uses NumPy for calculations and Pandas to organise the data.

## Run the project

Python 3.11 or newer is required. Open a terminal in this folder and run:

```text
python -m venv .venv
```

On Windows:

```text
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

On macOS or Linux:

```text
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

Once setup is complete, Windows users can also double-click `run_project.bat`.
The batch file keeps the terminal open so the output can be read. With NumPy and
Pandas already installed in your active Python environment, `python main.py`
also works. No API key, internet connection at runtime, or extra test library is
needed.

## Dataset

`students.csv` contains 24 fictional students across BCA, BSc CS and BSc IT.
Names and marks are sample data, not actual student records. The nine columns are:

| Column | Meaning |
| --- | --- |
| Student_ID | Unique student identifier, kept as text |
| Name | Student name |
| Department | Course or department |
| Python | Python marks out of 100 |
| Mathematics | Mathematics marks out of 100 |
| Statistics | Statistics marks out of 100 |
| English | English marks out of 100 |
| Computer_Basics | Computer basics marks out of 100 |
| Attendance | Attendance percentage from 0 to 100 |

## Calculation rules

- Total is the sum of five subject marks, out of 500.
- Average is the total divided by five, out of 100. All subjects have equal weight.
- A student passes only if every subject mark is at least 40.
- A failed subject gives grade F, regardless of the average.
- Attendance below 75% is marked Low. Attendance does not affect the academic result.

| Average, when every subject is passed | Grade |
| --- | --- |
| 90 to 100 | A+ |
| 80 to below 90 | A |
| 70 to below 80 | B |
| 60 to below 70 | C |
| 50 to below 60 | D |
| 40 to below 50 | E |
| Any subject below 40 | F |

These are the rules chosen for this project; the assignment does not prescribe
specific cutoffs. Grades and ranking use unrounded averages. Displayed averages
are rounded to two decimal places, so a custom average of 89.999 displays as
90.00 but remains grade A. The ranking covers all students by average and shows
their pass/fail status. Equal averages share a rank; everyone tied at the cutoff
is included. This can produce more than five students in the top-five report.

## What the program produces

The terminal output includes the loaded dataset, its column types, student
results, class statistics, subject statistics, top performers, grade counts,
failed subjects and low-attendance records. The following files are also saved:

| File in `reports/` | Contents |
| --- | --- |
| analysis_report.txt | Complete readable report |
| student_results.csv | Original data plus each student's calculated results |
| subject_analysis.csv | Highest, lowest, average and pass rate for each subject |
| class_summary.csv | Class totals, averages and attendance figures |
| top_performers.csv | Highest averages, including tied places |
| grade_distribution.csv | Number of students in each grade |

Report files are replaced when the program is run again in the same output
folder. Use a different `--output` folder to keep reports from another dataset.
For example, with your Python environment active:

```text
python main.py --data "another class.csv" --output "another report" --top 3
```

The default input and output paths are relative to `main.py`, so the program also
works when launched from another directory. Paths supplied as arguments are
relative to the terminal's current directory. Custom files must use the same
nine required column names. Additional columns are ignored. At least one record
is needed for analysis; the supplied dataset exceeds the assignment minimum.

## Results from the supplied dataset

| Measure | Result |
| --- | --- |
| Students | 24 |
| Passed / failed | 18 / 6 |
| Pass percentage | 75.00% |
| Class average | 69.34 / 100 |
| Highest average | Meera Nair, 94.00 |
| Lowest average | Om Prakash, 33.00 |
| Best subject average | English, 73.62 |
| Median student average | 73.50 |
| Average attendance | 82.67% |
| Students with low attendance | 6 |

Dev Malhotra averages 80.60 but fails Mathematics with 39 marks, so his result is
Fail and his grade is F. Arjun Reddy passes with a Python score of exactly 40.
Vikram Patel and Kavya Iyer both average 86.00 and share fifth place.

## How the code is organised

| File | Purpose |
| --- | --- |
| main.py | Reads command options, runs analysis, displays and saves results |
| functions.py | Validation, calculations, summaries and report formatting |
| students.csv | Input dataset |
| requirements.txt | NumPy and Pandas versions |
| tests/test_project.py | Calculation, validation and command-line checks |
| Project_Documentation.md | Detailed project explanation and outcome |
| Project_Documentation.pdf | Printable copy of the documentation |
| run_project.bat | Windows launcher |

`load_students()` checks the CSV structure, required fields, duplicate IDs and
numeric ranges. NumPy calculates row totals and averages and checks whether all
subjects are passed. Pandas handles tables, filtering, sorting and grade counts.
Loops build subject summaries, assign grades and write the reports. Invalid data
stops the run with a message identifying the problem; marks are not silently
filled in or dropped.

## Tests

On Windows:

```text
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

With your environment active, use `python -m unittest discover -s tests -v`.
Tests cover hand-checked totals, grade boundaries, failed subjects, attendance,
ties, invalid CSVs and running the project from another folder.
All 22 tests passed on Python 3.12.14 and Python 3.14.6 on Windows. The Windows
launcher was also checked, and `pip check` reported no broken requirements.

## Before submission

Read the documentation and run the program so you can explain the calculations.
Create a GitHub repository, upload the project files and generated sample reports,
and exclude `.venv` and `__pycache__`. Add the repository URL to the documentation
after publishing. Submit that URL through the trainer's Google Form. No repository
or form submission has been created by this local project.

The assignment PDF gives a deadline of **15 October 2026**. Confirm the current
submission arrangement with the trainer if submitting after that date.
