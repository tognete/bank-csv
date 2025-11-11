# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import os

project_root = Path(os.environ.get("GITHUB_WORKSPACE", Path.cwd()))
frontend_dist = project_root / "frontend" / "dist"
input_dir = project_root / "Input"
vendor_root = project_root / "vendor"

datas = []
if frontend_dist.exists():
    datas.append((str(frontend_dist), "frontend/dist"))
if input_dir.exists():
    datas.append((str(input_dir), "Input"))

vendor_targets = {
    "tesseract": vendor_root / "tesseract",
    "poppler": vendor_root / "poppler",
}
for name, path in vendor_targets.items():
    if path.exists():
        datas.append((str(path), f"vendor/{name}"))

block_cipher = None

a = Analysis(
    [str(project_root / "launcher.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BankCSV",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="BankCSV",
)
