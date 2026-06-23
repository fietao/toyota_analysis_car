@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==== Step 1: backend data pipeline ====
cd backend
python run_pipeline.py --skip-map --skip-analyst
if %ERRORLEVEL% neq 0 (
    echo ERROR: Step 1 backend data pipeline failed.
    pause
    exit /b 1
)

echo ==== Step 2: export dashboard data ====
python export_dashboard.py
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
