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
Write-Host "Starting Bank CSV Extractor (auto-opens browser at http://127.0.0.1:8020/)"
& .\.venv\Scripts\python "$root\launcher.py"
