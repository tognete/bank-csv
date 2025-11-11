# Vendor Dependencies

To ship a completely self-contained Windows executable, bundle the native tools the OCR pipeline depends on:

| Tool | Where to place files | Notes |
| --- | --- | --- |
| **Tesseract OCR** (UB Mannheim build) | `vendor/tesseract/` | Copy the entire installation directory (keep `tesseract.exe` in the root and the `tessdata/` subfolder). Include any additional language data you need. |
| **Poppler for Windows** | `vendor/poppler/` | Copy the extracted Poppler folder (must contain `bin/pdftoppm.exe`). |

Once these folders contain the binaries, PyInstaller (see `packaging/windows/bank_csv.spec`) will embed them in the final `BankCSV.exe`. The launcher automatically prepends these directories to `PATH` and sets `TESSDATA_PREFIX`, so no manual installation is required on the target machine.

> ⚠️ Make sure you comply with the upstream licenses (Apache 2.0 for Tesseract, GPL for Poppler) and ship their license files alongside your executable if required.
