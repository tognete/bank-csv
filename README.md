# Bank CSV Extractor

Turn PDF statements and screenshots into CSVs with a FastAPI backend and a Vite/React GUI that you can iterate on throughout development.

## Project layout

- `backend/` – FastAPI service plus OCR/table extraction pipeline (Python 3.11, virtualenv in `backend/.venv`).
- `frontend/` – React + Vite single-page app for uploads and CSV previews.
- `Input/` – Sample PDF/image the app should be able to process.

## Prerequisites

| Tool | macOS | Windows |
| --- | --- | --- |
| Python 3.11 | `brew install python@3.11` | [python.org download](https://www.python.org/downloads/) |
| Tesseract OCR + lang data (`eng`, `spa`) | `brew install tesseract` (ships with `eng`; add `brew install tesseract-lang` for Spanish) | [UB Mannheim build](https://github.com/UB-Mannheim/tesseract/wiki) + enable Spanish during setup |
| Poppler (for PDF raster fallback) | `brew install poppler` | [poppler for Windows binaries](https://blog.alivate.com.au/poppler-windows/) and add `pdftoppm.exe` to `PATH` |
| Node.js ≥ 20 (for Vite 7) | `brew install node@20` | [Node 20 LTS installer](https://nodejs.org/) |

> **Tip:** During development on macOS you can stay on any Node version, but Windows builds (and lint tooling) expect Node 20+. Upgrade sooner rather than later.

## Backend setup

```bash
# Create virtual environment once
python3 -m venv backend/.venv

# Install dependencies
backend/.venv/bin/pip install -r backend/requirements.txt

# Run the API (add --reload while developing)
PYTHONPATH=backend backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

> Dependencies live in `backend/requirements.in`. Edit that file and run `pip-compile backend/requirements.in` (pip-tools) to regenerate `backend/requirements.txt` with fully pinned versions when you need a reproducible build.

### API

- `POST /api/extract` – multipart upload (`file`) → JSON payload containing CSV, columns, rows, notes.
- `GET /api/health` – simple health check.

**Screenshot extraction highlights**

- Upscales images to 2000px width and runs Tesseract with combined English/Spanish language packs for better accuracy on Latin American statements.
- Detects table columns by reading the screenshot grid lines (OpenCV morphology). If grid detection fails it falls back to clustering text bounding boxes.
- Reconstructs rows using the inferred columns, auto-detects text headers (e.g., `Fecha`, `Descripcion`, `Ingresos`) and removes noise rows (like `SALDO FINAL` banners) before emitting the CSV.

## Frontend setup

```bash
cd frontend
cp .env.example .env    # adjust VITE_API_BASE_URL if needed
npm install             # Node 20+ recommended
npm run dev             # http://localhost:5173
```

The GUI lets you drag/drop PDFs or images, invokes the FastAPI endpoint, previews the detected table, and offers a CSV download link.

## Windows-specific notes

1. Install **Tesseract** and **Poppler** and ensure both `tesseract.exe` and `pdftoppm.exe` are discoverable via `PATH`.
2. When running from PowerShell, adapt commands:

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\pip install -r backend\requirements.txt
set PYTHONPATH=backend
backend\.venv\Scripts\uvicorn app.main:app --port 8000
```

3. Configure the frontend API base URL (e.g., `http://localhost:8000/api`) inside `frontend/.env`.

## Packaging a Windows-friendly build

`scripts/build_windows.ps1` is the single entry point for all Windows deliverables. Run it from an elevated PowerShell prompt (recommended) on a Windows machine with Node 20+ and Python 3.11+. Example:

```powershell
pwsh ./scripts/build_windows.ps1 -Mode all -UseVendor -MakeInstaller
```

What the script does:

- builds the Vite frontend (`npm ci && npm run build`)
- optionally provisions `vendor/tesseract` and `vendor/poppler` via Chocolatey (`-UseVendor`)
- runs `scripts/prepare_windows_release.py` to create `release/windows/bank-csv.zip`
- executes the PyInstaller spec to produce `dist/BankCSV/BankCSV.exe`
- calls Inno Setup when available (`-MakeInstaller`)
- signs the `.exe` / installer with `signtool` when `-SignArtifacts -CertificatePath <pfx> [-CertificatePassword ...]` is supplied (timestamped via `-TimestampUrl`)

Share `release/windows/bank-csv.zip` when you want a Python-required bundle. It now includes the OCR binaries under `vendor/`, so Windows testers only need Python 3.11+ before running `run_app.bat` (which opens http://127.0.0.1:8020/ automatically). `scripts/prepare_windows_release.py` remains available if you want to invoke it manually, but the PowerShell helper already calls it.

### “One-click” Windows executable

`BankCSV.exe` (PyInstaller output) embeds the backend, frontend build, Python runtime, and the vendored OCR tools. Double-clicking it launches the server + browser with no prerequisites. Bundle the Inno Setup installer (`release/windows/BankCSV-Setup.exe`) if you need an install wizard, desktop shortcuts, etc.

### Code signing

To avoid SmartScreen warnings, provide a code-signing certificate (ideally EV) and let the build script sign artifacts:

```powershell
pwsh ./scripts/build_windows.ps1 -Mode exe -UseVendor `
  -SignArtifacts -CertificatePath C:\certs\bankcsv.pfx `
  -CertificatePassword 'your-password'
```

Use `-TimestampUrl` to target a different TSA if needed.

### GitHub Actions workflow

The `windows-build` workflow mirrors the local script. Add two repository secrets, `SIGNING_CERT_B64` (base64-encoded `.pfx`) and `SIGNING_CERT_PASSWORD`, to enable signing in CI. The action will:

1. Build the frontend
2. Fetch/install Tesseract + Poppler via Chocolatey and copy them into `vendor/`
3. Produce the ZIP, PyInstaller folder, and installer
4. Sign artifacts when secrets are present
5. Upload everything as a single artifact called **BankCSV-windows**

> **Tip:** After every release, spin up a clean Windows VM, run the installer or EXE, upload the sample files in `Input/`, and confirm the OCR notes look healthy before sharing the build.

## Testing with sample data

1. Start backend + frontend as above.
2. Use the GUI to upload one of the files in `Input/`.
3. You should see table rows populate and the “Download CSV” button become available.

For CLI-style validation without the GUI:

```bash
PYTHONPATH=backend backend/.venv/bin/python - <<'PY'
from pathlib import Path
from app.services.extractor import DocumentProcessor

processor = DocumentProcessor()
sample = Path("Input/guardarMovimientosHist.do.pdf").read_bytes()
result = processor.process("sample.pdf", sample)
print(result.notes, result.dataframe.head())
PY
```

## Next steps

- Improve table reconstruction heuristics (e.g., detect numeric columns, currency normalization).
- Persist extracted CSVs or upload history.
- Package the solution (PyInstaller / Electron shell) once features stabilize.
