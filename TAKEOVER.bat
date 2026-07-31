@echo off
setlocal EnableExtensions
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"

if not exist "README.md" (
    echo ERROR: Run this file from the ai-reading-car-analysis folder.
    pause
    exit /b 1
)

:menu
cls
echo ============================================================
echo  Thailand DLT Dashboard
echo ============================================================
echo.
echo  1. Open the dashboard
echo  2. Update this month's data
echo  3. Open the monthly update guide
echo  4. Exit
echo.
set /p CHOICE="Choose 1-4: "

if "%CHOICE%"=="1" goto start_dashboard
if "%CHOICE%"=="2" goto update_data
if "%CHOICE%"=="3" goto open_guide
if "%CHOICE%"=="4" exit /b 0

echo.
echo Please choose a number from 1 to 4.
pause
goto menu

:start_dashboard
call "%~dp0START.bat"
goto menu

:update_data
echo.
echo This updates the published data using the new DLT files.
set /p CONFIRM="Type UPDATE to continue: "
if /I not "%CONFIRM%"=="UPDATE" goto menu
call "%~dp0MONTHLY_UPDATE.bat"
goto menu

:open_guide
start "" "%~dp0docs\THAI_OPERATOR_MONTHLY_GUIDE.md"
goto menu
