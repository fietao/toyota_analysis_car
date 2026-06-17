@echo off
setlocal

:: Default model — change this or pass a model name as first arg
set "MODEL=qwen2.5-coder:7b"
if not "%~1"=="" set "MODEL=%~1"

echo.
echo  Local LLM ^| Model: %MODEL%
echo  Available models:
echo    qwen2.5-coder:7b   (default, fast, 4.7GB)
echo    qwen3:8b           (stronger reasoning, 5.2GB)
echo    devstral:latest    (best for code, 14GB)
echo    qwen3-coder:30b    (most capable, 18GB)
echo.
echo  Usage: local [model-name]
echo  Type /bye to exit.
echo.

ollama run %MODEL%
