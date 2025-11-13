# Bank CSV Extractor – Windows Preview

Thanks for helping test the app! The ZIP you received already contains:

- Python backend + frontend build
- `vendor/tesseract` and `vendor/poppler` with the OCR binaries + language data
- Launcher scripts that point the app at those vendor folders automatically

All you need before running the app is **Python 3.11+** (https://www.python.org/downloads/).
If you ever receive a bundle without `vendor/`, install Tesseract and Poppler manually as described in the README.

## Running the app

1. Unzip the archive somewhere like `C:\bank-csv`.
2. Double-click `run_app.bat` (or run `run_app.ps1` from PowerShell). The script will:
   - Create a virtual environment inside the folder (first run only).
   - Install the Python dependencies.
   - Launch the app and open your default browser at http://127.0.0.1:8020/.
3. Use the GUI to upload a PDF or screenshot.

### Prefer a single `.exe`?

If you received `BankCSV.exe` instead of the folder above, just double-click it. The app bundles Python **and** the OCR binaries internally, launches on http://127.0.0.1:8020/, and opens your default browser automatically. Press `Ctrl+C` in the small console window to exit when you’re done.

While the server stays open, the terminal window will show logs and OCR notes. Press `Ctrl+C` in that window to stop the app.

### Notes

- The GUI is already bundled, so you do **not** need Node.js on Windows.
- The sample files in the `Input/` folder are great for quick smoke tests.
- If you remove the bundled `vendor/` folder, install Tesseract and Poppler manually or re-run `run_app` after restoring the vendor binaries.
