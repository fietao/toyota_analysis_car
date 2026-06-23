@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ============================================================
echo  Monthly Data Update
echo  Drop the 2 DLT files into "backend\raw data\" then run this.
echo ============================================================
echo.
cd backend
python update_raw_data.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Update failed. See message above.
    pause
    exit /b 1
)
echo.
echo Done. Check the backend folder for the new output files.
pause
