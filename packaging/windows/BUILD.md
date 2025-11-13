Windows build and packaging

- Run `pwsh ./scripts/build_windows.ps1 -Mode all -UseVendor -MakeInstaller` to generate the ZIP, PyInstaller folder, and (if `iscc` is installed) the installer.
- Add `-SignArtifacts -CertificatePath <pfx> [-CertificatePassword ...] [-TimestampUrl ...]` to sign `BankCSV.exe` and the installer with `signtool`.
- The script will automatically install/copy Tesseract + Poppler into `vendor/` via Chocolatey when `-UseVendor` is provided.
- `scripts/prepare_windows_release.py` is still available if you want to regenerate only the ZIP bundle from any platform.

Notes

- Vendor binaries live under `vendor/tesseract` and `vendor/poppler`. See `vendor/README.md` for details and licensing reminders.
- If you skip `-UseVendor`, the generated artifacts expect `tesseract.exe` and `pdftoppm.exe` to be installed globally on the target machine.
