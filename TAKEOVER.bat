@echo off
setlocal EnableExtensions
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"

if not exist "README.md" (
    echo ERROR: Run this file from the ai-reading-car-analysis folder.
    echo Missing README.md.
    echo.
    pause
    exit /b 1
)

:menu
cls
echo ============================================================
echo  Takeover Menu - Thailand DLT Dashboard
echo ============================================================
echo.
echo  Everyday tasks:
echo  1. Start the dashboard (view it in your browser)
echo  2. Update this month's data
echo  3. Open the monthly update guide (how-to, in Thai)
echo  4. Open the latest update summary (what happened last time)
echo  5. Open the model review file (approve new car models)
echo  6. Check the website still works (before handing off)
echo.
echo  One-time / rare:
echo  7. First-time install on this laptop
echo  8. Refresh project dependencies only
echo  9. Open Thai release notes and PowerPoint
echo  10. Exit
echo.
set /p CHOICE="Choose 1-10: "

if "%CHOICE%"=="1" goto run_dashboard
if "%CHOICE%"=="2" goto run_monthly_update
if "%CHOICE%"=="3" goto open_guide
if "%CHOICE%"=="4" goto open_summary
if "%CHOICE%"=="5" goto open_review_csv
if "%CHOICE%"=="6" goto frontend_checks
if "%CHOICE%"=="7" goto install_zero
if "%CHOICE%"=="8" goto setup_only
if "%CHOICE%"=="9" goto open_notes
if "%CHOICE%"=="10" exit /b 0

echo.
echo Please choose a number from 1 to 10.
pause
goto menu

:install_zero
call "%~dp0INSTALL_FROM_ZERO.bat"
goto after_action

:setup_only
call "%~dp0SETUP.bat"
goto after_action

:run_dashboard
call "%~dp0frontend\RUN.bat"
goto after_action

:run_monthly_update
call "%~dp0MONTHLY_UPDATE.bat"
goto after_action

:open_guide
start "" "%~dp0docs\THAI_OPERATOR_MONTHLY_GUIDE.md"
goto after_action

:open_summary
call "%~dp0OPEN_OPERATOR_SUMMARY.bat"
goto after_action

:open_review_csv
call "%~dp0OPEN_MODEL_REVIEW_CSV.bat"
goto after_action

:frontend_checks
where npm.cmd >nul 2>nul
if errorlevel 1 (
    echo ERROR: npm.cmd was not found. Run option 7 or install Node.js LTS.
    echo.
    pause
    goto menu
)
cd frontend
call npm.cmd test
if errorlevel 1 goto checks_failed
call npm.cmd run lint
if errorlevel 1 goto checks_failed
call npm.cmd run build
if errorlevel 1 goto checks_failed
cd ..
echo.
echo Frontend release checks passed.
goto after_action

:checks_failed
cd ..
echo.
echo Frontend checks failed. Read the error above.
goto after_action

:open_notes
start "" "%~dp0handoffs\release-summary-and-takeover-2026-07-24.md"
if exist "%~dp0handoffs\thai-takeover-training-2026-07-24.pptx" start "" "%~dp0handoffs\thai-takeover-training-2026-07-24.pptx"
start "" "%~dp0handoffs\manual-report-comparison-final-handoff-2026-07-24.md"
start "" "%~dp0handoffs\other-laptop-setup-and-final-test-2026-07-24.md"
goto after_action

:after_action
echo.
pause
goto menu
