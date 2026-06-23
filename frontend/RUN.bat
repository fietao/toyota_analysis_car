@echo off
setlocal

cd /d "%~dp0"

set "URL=http://localhost:3001"

echo Thailand EV Registration dashboard
echo.
echo URL: %URL%
echo.

netstat -ano | findstr /R /C:":3001 .*LISTENING" >nul 2>nul

if %errorlevel%==0 (
  echo Port 3001 is already in use. Opening the dashboard URL...
  start "" "%URL%"
  echo.
  echo If the page does not load, stop the old process using port 3001 and run this file again.
  pause
  exit /b 0
)

where npm.cmd >nul 2>nul
if errorlevel 1 (
  echo ERROR: npm.cmd was not found. Install Node.js, then run this again.
  echo.
  pause
  exit /b 1
)

echo Starting dashboard server...
echo Press Ctrl+C to stop the server.
echo.
start "" "%URL%"

call npm.cmd run dev -- --port 3001

echo.
echo Server stopped or failed to start.
pause
