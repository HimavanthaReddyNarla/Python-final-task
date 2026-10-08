@echo off
setlocal
cd /d "%~dp0"

if not defined MYSQL_HOST set "MYSQL_HOST=127.0.0.1"
if not defined MYSQL_PORT set "MYSQL_PORT=3306"
if not defined MYSQL_USER set "MYSQL_USER=root"
if not defined MYSQL_PASSWORD set "MYSQL_PASSWORD="
if not defined MYSQL_DATABASE set "MYSQL_DATABASE=job_portal"

if not exist ".venv\Scripts\python.exe" (
    echo Creating the project virtual environment...
    py -3 -m venv .venv
    if errorlevel 1 goto :python_missing
)

echo Installing or updating project requirements...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :install_failed

echo Starting the Job Portal...
".venv\Scripts\python.exe" "python\main.py"
if errorlevel 1 (
    echo.
    echo The portal stopped. Check that MySQL is running and the connection
    echo settings in run.bat are correct.
    pause
)
exit /b

:python_missing
echo Python 3 was not found. Install Python 3.10 or newer and enable the py launcher.
pause
exit /b 1

:install_failed
echo Could not install requirements. Check your internet connection and try again.
pause
exit /b 1
