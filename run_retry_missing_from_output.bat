@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "OUTPUT_XLSX=data\output\subnet_assessment.xlsx"
set "RETRY_OUTPUT_XLSX=data\output\subnet_assessment.retry.xlsx"

echo [1/5] Detecting Python...
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

echo [2/5] Checking required packages...
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

echo [3/5] Reading failed netuids from %OUTPUT_XLSX%...
if not exist "%OUTPUT_XLSX%" (
    echo Output file not found: %OUTPUT_XLSX%
    echo Run run_collector.bat once first, then retry with this file.
    pause
    exit /b 1
)

set "RETRY_NETUIDS="
for /f "usebackq delims=" %%i in (`%PY_CMD% find_retry_netuids.py --xlsx "%OUTPUT_XLSX%"`) do set "RETRY_NETUIDS=%%i"
if errorlevel 1 (
    echo Failed to parse retry netuids from %OUTPUT_XLSX%.
    pause
    exit /b 1
)

if not defined RETRY_NETUIDS (
    echo No subnet marked for manual review was found in %OUTPUT_XLSX%.
    pause
    exit /b 0
)

echo Found retry netuids: %RETRY_NETUIDS%
echo [4/6] Running collector for retry netuids...
if exist "%RETRY_OUTPUT_XLSX%" del /f /q "%RETRY_OUTPUT_XLSX%" >nul 2>nul
%PY_CMD% run.py --config config/default.json --netuids %RETRY_NETUIDS% --output "%RETRY_OUTPUT_XLSX%"
set "EXIT_CODE=%errorlevel%"
if errorlevel 1 goto :finish

echo [5/6] Merging retry result back into %OUTPUT_XLSX%...
%PY_CMD% merge_retry_output.py --base "%OUTPUT_XLSX%" --retry "%RETRY_OUTPUT_XLSX%"
set "EXIT_CODE=%errorlevel%"
if exist "%RETRY_OUTPUT_XLSX%" del /f /q "%RETRY_OUTPUT_XLSX%" >nul 2>nul

:finish
echo [6/6] Finished with exit code %EXIT_CODE%.
if exist "%OUTPUT_XLSX%" (
    echo Output file: %OUTPUT_XLSX%
    set "FAILED_COUNT="
    for /f "usebackq delims=" %%i in (`%PY_CMD% find_retry_netuids.py --xlsx "%OUTPUT_XLSX%" --count`) do set "FAILED_COUNT=%%i"
    if defined FAILED_COUNT (
        echo Failed subnets: %FAILED_COUNT%
    ) else (
        echo Failed subnets: unknown
    )
)
pause
exit /b %EXIT_CODE%