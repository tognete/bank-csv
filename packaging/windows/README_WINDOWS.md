# Bank CSV Extractor – Windows Preview

Thanks for helping test the app! Before running it, please install the native dependencies:

1. **Tesseract OCR** (English + Spanish data)
   - Download the latest UB Mannheim installer: https://github.com/UB-Mannheim/tesseract/wiki
   - During setup, enable the Spanish language pack.
   - Make sure `tesseract.exe` is on your PATH (the installer usually does this automatically).
2. **Poppler** (for PDF raster fallback)
   - Get the latest release from https://blog.alivate.com.au/poppler-windows/
   - Extract it to `C:\poppler` (or similar) and add the `bin` folder (contains `pdftoppm.exe`) to your PATH.
3. **Python 3.11+** – https://www.python.org/downloads/

## Running the app

1. Unzip the archive somewhere like `C:\bank-csv`.
2. Double-click `run_app.bat` (or run `run_app.ps1` from PowerShell). The script will:
   - Create a virtual environment inside the folder (first run only).
   - Install the Python dependencies.
   - Start the FastAPI server at http://127.0.0.1:8000/.
3. Open a browser to http://127.0.0.1:8000/ and use the GUI to upload a PDF or screenshot.

### Prefer a single `.exe`?

If you received `BankCSV.exe` instead of the folder above, just double-click it. The app bundles Python **and** the OCR binaries internally, launches on http://127.0.0.1:8020/, and opens your default browser automatically. Press `Ctrl+C` in the small console window to exit when you’re done.

While the server stays open, the terminal window will show logs and OCR notes. Press `Ctrl+C` in that window to stop the app.

### Notes

- The GUI is already bundled, so you do **not** need Node.js on Windows.
- The sample files in the `Input/` folder are great for quick smoke tests.
- If the server reports that Tesseract or Poppler is missing, double-check your PATH environment variables and re-run the script.
