@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo กำลังเปิดไฟล์รีวิวรุ่นรถ - แก้แล้วบันทึกแบบ CSV UTF-8 จากนั้นรัน MONTHLY_UPDATE.bat
echo Opening the model-review CSV - edit, save as CSV UTF-8, then run MONTHLY_UPDATE.bat
start "" "backend\config\model_powertrain_review.csv"
