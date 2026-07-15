@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"

echo ==== Step 1: backend data pipeline ====
cd backend
py -3.12 run_pipeline.py --skip-map --skip-analyst
if %ERRORLEVEL% neq 0 (
    echo ERROR: Step 1 backend data pipeline failed.
    pause
    exit /b 1
)

echo ==== Step 2: export dashboard data ====
py -3.12 export_dashboard.py
if %ERRORLEVEL% neq 0 (
    echo ERROR: Step 2 export dashboard data failed.
    pause
    exit /b 1
)

echo ==== Step 3: frontend dev server ====
cd ..
cd frontend
if not exist node_modules (
    call npm install
)
call npm run dev
pause
