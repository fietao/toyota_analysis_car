@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist "reports\monthly_operator_summary.txt" (
    echo ยังไม่มีไฟล์สรุป - กรุณาดับเบิลคลิก MONTHLY_UPDATE.bat ก่อน
    echo No summary yet - run MONTHLY_UPDATE.bat first.
    pause
    exit /b 1
)
start "" "reports\monthly_operator_summary.txt"
