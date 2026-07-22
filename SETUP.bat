@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"

echo ============================================================
echo  One-time / occasional project setup
echo ============================================================
echo.

echo ==== Backend: installing Python dependencies ====
cd backend
py -3.12 -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Backend dependency install failed.
    pause
    exit /b 1
)
cd ..
echo.

echo ==== Frontend: installing npm dependencies ====
cd frontend
call npm ci
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Frontend dependency install failed.
    pause
    exit /b 1
)
cd ..
echo.

echo ============================================================
echo  Setup complete. Next: UPDATE.bat or BUILD_RELEASE.bat
echo ============================================================
pause
