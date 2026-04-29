@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

echo [1/4] Detecting Python...
set "PY_CMD="
if exist ".venv\Scripts\python.exe" set "PY_CMD=.venv\Scripts\python.exe"
if exist "venv\Scripts\python.exe" set "PY_CMD=venv\Scripts\python.exe"
if exist "env\Scripts\python.exe" set "PY_CMD=env\Scripts\python.exe"
if exist "d:\1mywork\test\.venv\Scripts\python.exe" set "PY_CMD=d:\1mywork\test\.venv\Scripts\python.exe"
if defined PY_CMD goto :python_found
where py >nul 2>nul
if %errorlevel%==0 set "PY_CMD=py -3"
if not defined PY_CMD (
    where python >nul 2>nul
    if %errorlevel%==0 set "PY_CMD=python"
)

:python_found

if not defined PY_CMD (
    echo Python was not found.
    echo Install Python 3.10+ first, then run this file again.
    pause
    exit /b 1
)

echo [2/4] Checking required packages...
%PY_CMD% -c "import requests, pandas, openpyxl, bs4" >nul 2>nul
if errorlevel 1 (
    %PY_CMD% -m pip --version >nul 2>nul
    if errorlevel 1 (
        echo pip is missing. Bootstrapping pip...
        %PY_CMD% -m ensurepip --upgrade
        if errorlevel 1 (
            echo Failed to bootstrap pip.
            pause
            exit /b 1
        )
    )
    echo Installing dependencies from requirements.txt...
    %PY_CMD% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Dependency installation failed.
        pause
        exit /b 1
    )
)

echo [3/4] Running collector...
%PY_CMD% run.py --config config/default.json
set "EXIT_CODE=%errorlevel%"

echo [4/4] Finished with exit code %EXIT_CODE%.
if exist "data\output\subnet_assessment.xlsx" (
    echo Output file: data\output\subnet_assessment.xlsx
)
pause
exit /b %EXIT_CODE%
