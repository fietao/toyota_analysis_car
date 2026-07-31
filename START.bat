@echo off
setlocal EnableExtensions
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"

echo ============================================================
echo  Thailand DLT Dashboard
echo ============================================================
echo.

where npm.cmd >nul 2>nul
if errorlevel 1 (
    echo First time on this computer. Installing what is needed
    echo - this can take a few minutes. Please wait...
    echo.
    call "%~dp0INSTALL_FROM_ZERO.bat"
    if errorlevel 1 exit /b 1
) else if not exist "frontend\node_modules" (
    echo First time in this folder. Installing project files
    echo - this can take a minute. Please wait...
    echo.
    call "%~dp0SETUP.bat" nopause
    if errorlevel 1 exit /b 1
)

call "%~dp0frontend\RUN.bat"
