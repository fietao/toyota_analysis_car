@echo off
setlocal EnableExtensions
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"

echo ============================================================
echo  Install from zero: Thailand DLT dashboard
echo ============================================================
echo.
echo This installs or checks:
echo   - Python 3.12
echo   - Node.js LTS and npm
echo   - Git
echo   - Project Python and npm packages
echo.

if not exist "backend\requirements.txt" (
    echo ERROR: This file must be run from the ai-reading-car-analysis folder.
    echo Missing backend\requirements.txt.
    echo.
    pause
    exit /b 1
)

if not exist "frontend\package-lock.json" (
    echo ERROR: This file must be run from the ai-reading-car-analysis folder.
    echo Missing frontend\package-lock.json.
    echo.
    pause
    exit /b 1
)

call :ensure_python
if errorlevel 1 goto failed

call :ensure_node
if errorlevel 1 goto failed

call :ensure_git
if errorlevel 1 goto failed

echo.
echo ==== Installing project dependencies ====
call "%~dp0SETUP.bat" nopause
if errorlevel 1 goto failed

echo.
echo ============================================================
echo  Everything is installed.
echo ============================================================
echo.
echo Next:
echo   1. To open the dashboard:
echo        frontend\RUN.bat
echo.
echo   2. To run the monthly maintainer workflow:
echo        Put the 2 DLT Excel files in backend\raw data\
echo        Then double-click MONTHLY_UPDATE.bat
echo.
pause
exit /b 0

:ensure_python
echo ==== Checking Python 3.12 ====
py -3.12 --version >nul 2>&1
if %ERRORLEVEL%==0 (
    py -3.12 --version
    exit /b 0
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" --version
    exit /b 0
)

call :require_winget
if errorlevel 1 exit /b 1

call :winget_install "Python 3.12" "Python.Python.3.12"
if errorlevel 1 exit /b 1

py -3.12 --version >nul 2>&1
if %ERRORLEVEL%==0 (
    py -3.12 --version
    exit /b 0
)

echo ERROR: Python 3.12 was installed, but this Command Prompt cannot see py -3.12 yet.
echo Close this window, open a new Command Prompt, and run INSTALL_FROM_ZERO.bat again.
exit /b 1

:ensure_node
echo.
echo ==== Checking Node.js and npm ====
where npm.cmd >nul 2>&1
if %ERRORLEVEL%==0 (
    node --version
    call npm.cmd --version
    exit /b 0
)

call :require_winget
if errorlevel 1 exit /b 1

call :winget_install "Node.js LTS" "OpenJS.NodeJS.LTS"
if errorlevel 1 exit /b 1

where npm.cmd >nul 2>&1
if %ERRORLEVEL%==0 (
    node --version
    call npm.cmd --version
    exit /b 0
)

if exist "%ProgramFiles%\nodejs\npm.cmd" (
    set "PATH=%ProgramFiles%\nodejs;%PATH%"
    node --version
    call npm.cmd --version
    exit /b 0
)

echo ERROR: Node.js was installed, but this Command Prompt cannot see npm yet.
echo Close this window, open a new Command Prompt, and run INSTALL_FROM_ZERO.bat again.
exit /b 1

:ensure_git
echo.
echo ==== Checking Git ====
where git.exe >nul 2>&1
if %ERRORLEVEL%==0 (
    git --version
    exit /b 0
)

call :require_winget
if errorlevel 1 exit /b 1

call :winget_install "Git" "Git.Git"
if errorlevel 1 exit /b 1

where git.exe >nul 2>&1
if %ERRORLEVEL%==0 (
    git --version
    exit /b 0
)

if exist "%ProgramFiles%\Git\cmd\git.exe" (
    set "PATH=%ProgramFiles%\Git\cmd;%PATH%"
    git --version
    exit /b 0
)

echo ERROR: Git was installed, but this Command Prompt cannot see it yet.
echo Close this window, open a new Command Prompt, and run INSTALL_FROM_ZERO.bat again.
exit /b 1

:require_winget
where winget.exe >nul 2>&1
if %ERRORLEVEL%==0 exit /b 0

echo ERROR: winget was not found.
echo Install "App Installer" from the Microsoft Store, then run this file again.
echo Or install Python 3.12, Node.js LTS, and Git manually, then run SETUP.bat.
exit /b 1

:winget_install
echo Installing %~1...
winget install --id "%~2" --exact --source winget --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo ERROR: Could not install %~1 with winget.
    exit /b 1
)
exit /b 0

:failed
echo.
echo ============================================================
echo  Install did not finish. Read the error above.
echo ============================================================
echo.
pause
exit /b 1
