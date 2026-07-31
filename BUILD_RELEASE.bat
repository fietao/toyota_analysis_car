@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"

echo ============================================================
echo  Public Release Build Pipeline
echo ============================================================
echo.

echo ==== Step 1: Run Data Pipeline ====
cd backend
set "PY312=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
set "PYTHON_CMD="
py -3.12 --version >nul 2>&1
if %ERRORLEVEL%==0 set "PYTHON_CMD=py -3.12"
if not defined PYTHON_CMD if exist "%PY312%" set "PYTHON_CMD="%PY312%""
if not defined PYTHON_CMD (
    echo ERROR: Python 3.12 was not found. Run INSTALL_FROM_ZERO.bat first.
    pause
    exit /b 1
)
%PYTHON_CMD% run_pipeline.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Step 1 backend data pipeline failed.
    pause
    exit /b 1
)
echo.

echo ==== Step 2: Export Dashboard Data ====
%PYTHON_CMD% export_dashboard.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Step 2 export dashboard data failed.
    pause
    exit /b 1
)
echo.

echo ==== Step 3: Export Analyst Data ====
%PYTHON_CMD% export_analyst.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Step 3 export analyst data failed.
    pause
    exit /b 1
)
echo.

echo ==== Step 4: Export Manual Report (sheets 1-9) ====
%PYTHON_CMD% export_manual_report.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Step 4 export manual report failed.
    pause
    exit /b 1
)
echo.

echo ==== Step 5: Refresh BEV Review Watchlist ====
%PYTHON_CMD% bev_candidates.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Step 5 BEV review watchlist refresh failed.
    pause
    exit /b 1
)
echo.

echo ==== Step 6: Validate Manual Report Against Markdown ====
set "MARKDOWN_REPORT=%MARKDOWN_REPORT_PATH%"
if not defined MARKDOWN_REPORT (
    for /f "delims=" %%F in ('dir /b /a:-d /o:-d "%USERPROFILE%\Downloads\*_sheets1-9.md" 2^>nul') do if not defined MARKDOWN_REPORT set "MARKDOWN_REPORT=%USERPROFILE%\Downloads\%%F"
)
if not defined MARKDOWN_REPORT (
    echo ERROR: Markdown report not found. Set MARKDOWN_REPORT_PATH or place a
    echo        *_sheets1-9.md file in %USERPROFILE%\Downloads.
    pause
    exit /b 1
)
%PYTHON_CMD% validate_against_markdown.py "%MARKDOWN_REPORT%"
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Step 6 markdown parity validation failed ^(hard fuel-derived mismatch^).
    pause
    exit /b 1
)
echo.

echo ==== Step 7: Validate Public Release Data ====
%PYTHON_CMD% validate_public_release.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Step 7 validate public release data failed.
    pause
    exit /b 1
)
echo.

echo ==== Step 8: Frontend Linting ====
cd ../frontend
set "NEXT_PUBLIC_BASE_PATH=/toyota_analysis_car"
if not exist node_modules (
    echo Installing npm dependencies...
    call npm ci
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Frontend dependency install failed.
        pause
        exit /b 1
    )
)

call npm run lint
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Step 8 frontend lint failed.
    pause
    exit /b 1
)
echo.

echo ==== Step 9: Frontend Type Checking ====
call npx tsc --noEmit
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Step 9 frontend type check failed.
    pause
    exit /b 1
)
echo.

echo ==== Step 10: Frontend Build ====
call npm run build
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Step 10 frontend build failed.
    pause
    exit /b 1
)
echo.

cd ..
echo ============================================================
echo  PUBLIC RELEASE BUILD COMPLETED SUCCESSFULLY
echo ============================================================
echo.
pause
