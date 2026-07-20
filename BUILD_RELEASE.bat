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
py -3.12 run_pipeline.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Step 1 backend data pipeline failed.
    pause
    exit /b 1
)
echo.

echo ==== Step 2: Export Dashboard Data ====
py -3.12 export_dashboard.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Step 2 export dashboard data failed.
    pause
    exit /b 1
)
echo.

echo ==== Step 3: Export Analyst Data ====
py -3.12 export_analyst.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Step 3 export analyst data failed.
    pause
    exit /b 1
)
echo.

echo ==== Step 4: Export Manual Report (sheets 1-9) ====
py -3.12 export_manual_report.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Step 4 export manual report failed.
    pause
    exit /b 1
)
echo.

echo ==== Step 5: Validate Manual Report Against Markdown ====
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
py -3.12 validate_against_markdown.py "%MARKDOWN_REPORT%"
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Step 5 markdown parity validation failed ^(hard fuel-derived mismatch^).
    pause
    exit /b 1
)
echo.

echo ==== Step 6: Validate Public Release Data ====
py -3.12 validate_public_release.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Step 6 validate public release data failed.
    pause
    exit /b 1
)
echo.

echo ==== Step 7: Frontend Linting ====
cd ../frontend
if not exist node_modules (
    echo Installing npm dependencies...
    call npm install
    if %ERRORLEVEL% neq 0 (
        echo ERROR: npm install failed.
        pause
        exit /b 1
    )
)

call npm run lint
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Step 7 frontend lint failed.
    pause
    exit /b 1
)
echo.

echo ==== Step 8: Frontend Type Checking ====
call npx tsc --noEmit
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Step 8 frontend type check failed.
    pause
    exit /b 1
)
echo.

echo ==== Step 9: Frontend Build ====
call npm run build
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Step 9 frontend build failed.
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
