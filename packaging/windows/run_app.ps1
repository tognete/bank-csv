Param()

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-Not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv .venv
}

& .\.venv\Scripts\python -m pip install --upgrade pip | Out-Null
& .\.venv\Scripts\python -m pip install -r .\backend\requirements.txt

$env:PYTHONPATH = Join-Path $root "backend"
Write-Host "Starting Bank CSV Extractor at http://127.0.0.1:8000/ (Ctrl+C to stop)"
& .\.venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000
