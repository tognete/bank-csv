#!/usr/bin/env python3
"""
Builds the frontend, copies runtime assets, and creates a Windows-friendly bundle.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = REPO_ROOT / "frontend"
BACKEND_DIR = REPO_ROOT / "backend"
INPUT_DIR = REPO_ROOT / "Input"
PACKAGING_DIR = REPO_ROOT / "packaging" / "windows"
RELEASE_ROOT = REPO_ROOT / "release" / "windows"
TARGET_DIR = RELEASE_ROOT / "bank-csv"


def run(cmd: list[str], cwd: Path | None = None):
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def build_frontend():
    run(["npm", "install"], cwd=FRONTEND_DIR)
    run(["npm", "run", "build"], cwd=FRONTEND_DIR)


def copy_tree(src: Path, dest: Path, *, ignore_patterns: tuple[str, ...] = ()):
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns(*ignore_patterns))


def prepare_release_folder():
    if TARGET_DIR.exists():
        shutil.rmtree(TARGET_DIR)
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    # Backend (without the local virtualenv or pycache directories).
    copy_tree(
        BACKEND_DIR,
        TARGET_DIR / "backend",
        ignore_patterns=(".venv", "__pycache__", "*.pyc"),
    )

    # Frontend build artifacts only.
    dist_dir = FRONTEND_DIR / "dist"
    if not dist_dir.exists():
        raise SystemExit("frontend/dist missing. Run npm run build first.")
    copy_tree(dist_dir, TARGET_DIR / "frontend" / "dist")

    # Sample inputs for quick testing.
    if INPUT_DIR.exists():
        copy_tree(INPUT_DIR, TARGET_DIR / "Input")

    # Helper scripts and README for Windows testers.
    shutil.copy(PACKAGING_DIR / "README_WINDOWS.md", TARGET_DIR / "README_WINDOWS.md")
    shutil.copy(PACKAGING_DIR / "run_app.bat", TARGET_DIR / "run_app.bat")
    shutil.copy(PACKAGING_DIR / "run_app.ps1", TARGET_DIR / "run_app.ps1")


def make_zip():
    archive_path = shutil.make_archive(
        str(TARGET_DIR), "zip", root_dir=TARGET_DIR.parent, base_dir=TARGET_DIR.name
    )
    print(f"Release archive created: {archive_path}")


def main():
    build_frontend()
    prepare_release_folder()
    make_zip()


if __name__ == "__main__":
    main()
