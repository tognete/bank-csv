@echo off
setlocal ENABLEDELAYEDEXPANSION

set ROOT=%~dp0
cd /d "%ROOT%"

if not exist .venv (
    echo Creating Python virtual environment...
    python -m venv .venv || goto :error
)

call .venv\Scripts\python -m pip install --upgrade pip >nul
call .venv\Scripts\python -m pip install -r backend\requirements.txt || goto :error

set PYTHONPATH=%ROOT%backend
echo Starting Bank CSV Extractor (auto-opens browser at http://127.0.0.1:8020/)
call .venv\Scripts\python "%ROOT%launcher.py"
goto :eof

:error
echo.
echo An error occurred. Ensure Python, Tesseract, and Poppler are installed and try again.
pause
