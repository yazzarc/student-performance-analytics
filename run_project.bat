@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py %*
) else (
    python main.py %*
)
set "project_exit=%errorlevel%"
echo.
if not "%project_exit%"=="0" echo Setup instructions are in README.md.
pause
exit /b %project_exit%
