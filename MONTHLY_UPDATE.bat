@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"

rem Find a working Python 3.12: the py launcher first, then the standard per-user install.
rem (python.exe on PATH is deliberately NOT used — it is often a different/older version.)
set "PY312=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
py -3.12 --version >nul 2>&1
if %ERRORLEVEL%==0 goto run_py
if exist "%PY312%" goto run_path
goto no_python

:run_py
py -3.12 backend\monthly_update.py
goto done

:run_path
"%PY312%" backend\monthly_update.py
goto done

:no_python
echo ------------------------------------------------------------
echo  ไม่พบ Python 3.12 ในเครื่องนี้ - ยังรันไม่ได้
echo  Python 3.12 was not found on this computer.
echo.
echo  วิธีแก้ / Fix: ติดตั้ง Python 3.12 จาก https://www.python.org/downloads/
echo  (ตอนติดตั้งให้ติ๊ก "Add Python to PATH" และ "py launcher")
echo  Install Python 3.12, tick "Add Python to PATH" and "py launcher", then run again.
echo ------------------------------------------------------------
echo.
pause
exit /b 1

:done
set RC=%ERRORLEVEL%
echo.
if %RC% neq 0 (
    echo ------------------------------------------------------------
    echo  Not finished - read the error above and fix it.
    echo ------------------------------------------------------------
)
echo.
pause
exit /b %RC%
