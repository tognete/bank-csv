"""
Bank CSV desktop launcher.

Runs the FastAPI app in-process and opens the default browser automatically.
Intended to be bundled via PyInstaller so non-technical testers can double-click
an .exe and immediately use the tool.
"""

from __future__ import annotations

import multiprocessing
import signal
import threading
import time
import urllib.request
import webbrowser

import os
from pathlib import Path
import sys

from uvicorn import Config, Server

BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import create_app

HOST = "127.0.0.1"
PORT = 8020
BASE_URL = f"http://{HOST}:{PORT}/"


def prepend_path(path: Path):
    current = os.environ.get("PATH", "")
    os.environ["PATH"] = str(path) + os.pathsep + current if current else str(path)


def configure_vendor_binaries():
    vendor_dir = BASE_DIR / "vendor"
    tesseract_dir = vendor_dir / "tesseract"
    if (tesseract_dir / "tesseract.exe").exists():
        prepend_path(tesseract_dir)
        tessdata = tesseract_dir / "tessdata"
        if tessdata.exists():
            # Point Tesseract directly at the tessdata folder so packaged builds
            # don't depend on a system-wide installation.
            os.environ["TESSDATA_PREFIX"] = str(tessdata)

    poppler_dir = vendor_dir / "poppler"
    poppler_bin = poppler_dir / "bin"
    if (poppler_bin / "pdftoppm.exe").exists():
        prepend_path(poppler_bin)
        os.environ.setdefault("POPPLER_PATH", str(poppler_dir))


def _open_browser_when_ready():
    for _ in range(40):
        try:
            urllib.request.urlopen(f"{BASE_URL}api/health", timeout=0.5)
            break
        except Exception:
            time.sleep(0.5)
    webbrowser.open(BASE_URL)


def run_server():
    configure_vendor_binaries()
    app = create_app()
    config = Config(app=app, host=HOST, port=PORT, log_level="info")
    server = Server(config)
    threading.Thread(target=_open_browser_when_ready, daemon=True).start()
    server.run()


def main():
    multiprocessing.freeze_support()
    try:
        run_server()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
