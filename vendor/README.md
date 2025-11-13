# Vendor Dependencies

To ship a completely self-contained Windows executable, bundle the native tools the OCR pipeline depends on:

| Tool | Where to place files | Notes |
| --- | --- | --- |
| **Tesseract OCR** (UB Mannheim build) | `vendor/tesseract/` | Copy the entire installation directory (keep `tesseract.exe` in the root and the `tessdata/` subfolder). Include any additional language data you need. |
| **Poppler for Windows** | `vendor/poppler/` | Copy the extracted Poppler folder (must contain `bin/pdftoppm.exe`). |

Once these folders contain the binaries, `scripts/build_windows.ps1 -UseVendor` will bundle them into:

- `release/windows/bank-csv.zip` (Python-required bundle)
- `dist/BankCSV/BankCSV.exe` (PyInstaller)
- `release/windows/BankCSV-Setup.exe` (when `iscc` is available)

`launcher.py` automatically prepends the vendor paths to `PATH` and sets `TESSDATA_PREFIX`, so nothing needs to be installed globally on the target PC.

> ⚠️ Make sure you comply with the upstream licenses (Apache 2.0 for Tesseract, GPL for Poppler). Keep their `LICENSE` files inside the corresponding vendor folders so they ship with every release, and mention them in your release notes if required.
