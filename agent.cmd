@echo off
setlocal
cd /d "%~dp0"

:: Default model — pass a model name as first arg to override
set "MODEL=devstral:latest"
if not "%~1"=="" set "MODEL=%~1"

echo.
echo  Local Agent ^| Model: %MODEL%
echo  Can read files, edit code, run commands — like Claude Code.
echo.
echo  Available models:
echo    devstral:latest      (best for code, 14GB)
echo    qwen3-coder:30b      (most capable, 18GB)
echo    qwen2.5-coder:7b     (fastest, 4.7GB)
echo.
echo  Usage: agent [model-name]
echo  Type /exit to quit.
echo.

aider --model ollama/%MODEL% --no-auto-commits
