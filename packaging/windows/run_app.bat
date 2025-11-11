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
echo Starting Bank CSV Extractor at http://127.0.0.1:8000/
call .venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000
goto :eof

:error
echo.
echo An error occurred. Ensure Python, Tesseract, and Poppler are installed and try again.
pause
