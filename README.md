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

The repo includes a helper script that builds the React frontend, copies only the runtime assets, and produces a `release/windows/bank-csv.zip` bundle with start scripts.

```bash
python scripts/prepare_windows_release.py
```

Share the resulting ZIP with Windows testers. Inside they’ll find:

- `run_app.bat` / `run_app.ps1` – create a venv, install dependencies, run `uvicorn`.
- `backend/` – FastAPI app + requirements.
- `frontend/dist/` – prebuilt SPA served directly by FastAPI (no Node needed).
- `README_WINDOWS.md` – instructions covering Tesseract/Poppler prerequisites.

Testers simply unzip, run the batch file, and open http://127.0.0.1:8000/ to use the app.

### “One-click” Windows executable

For friends who prefer double-clicking a single `.exe`, bundle the native OCR binaries directly:

1. Download the Windows Tesseract build (with Spanish data) and copy the whole folder into `vendor/tesseract/`.
2. Download the Poppler ZIP, extract it, and copy the folder into `vendor/poppler/` (keep the `bin/` directory intact).
3. On a Windows box:

```powershell
# once per machine
pip install pyinstaller
npm install
npm run build

# bundle backend, frontend/dist, Input/, and vendor binaries into BankCSV.exe
pyinstaller packaging/windows/bank_csv.spec --noconfirm
```

You’ll get `dist/BankCSV/BankCSV.exe`, which launches the embedded FastAPI server (via `launcher.py`), opens the default browser to http://127.0.0.1:8020/, and serves the built GUI with no terminal interaction. You still need to distribute the external Tesseract/Poppler installers alongside clear instructions, but the Python runtime is fully packaged.

Prefer not to build locally? Trigger the **`windows-build`** GitHub Actions workflow (manual `workflow_dispatch`). It runs on a Windows runner, installs Tesseract/Poppler via Chocolatey, copies them into `vendor/`, builds the frontend, runs PyInstaller, and publishes `BankCSV.exe` as an artifact you can download from the workflow run.

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
