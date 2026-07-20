@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"

echo ============================================================
echo  Local series review: admin server + dashboard
echo  Open http://localhost:3000 and use the review panel there.
echo  Admin server is local-only (127.0.0.1:8765) and never ships
echo  in the public release build.
echo ============================================================
echo.

start "series-admin-server" /D "%~dp0backend" cmd /c "py -3.12 admin_server.py"

cd frontend
if not exist node_modules (
    call npm ci
)
call npm run dev
