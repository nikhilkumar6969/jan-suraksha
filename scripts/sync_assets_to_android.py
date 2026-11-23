#!/usr/bin/env python3
"""
Sync Frontend Assets to Android App
Copies the complete web dashboard from `frontend/` to `android/app/src/main/assets/public/`
so that it can be served 100% offline via WebViewAssetLoader in Jan Suraksha.
"""

import os
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
TARGET_DIR = ROOT_DIR / "android" / "app" / "src" / "main" / "assets" / "public"

def sync_assets():
    print(f"[*] Starting asset synchronization...")
    print(f"    Source: {FRONTEND_DIR}")
    print(f"    Target: {TARGET_DIR}")

    if not FRONTEND_DIR.exists():
        print(f"[!] Error: Frontend directory '{FRONTEND_DIR}' does not exist.")
        sys.exit(1)

    # Ensure target directory exists
    if TARGET_DIR.exists():
        print(f"[*] Cleaning previous web assets in '{TARGET_DIR}'...")
        shutil.rmtree(TARGET_DIR)
    
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    # Copy files
    ignore_patterns = shutil.ignore_patterns(
        "*.tmp", "*.log", ".DS_Store", "Thumbs.db", "__pycache__"
    )
    
    file_count = 0
    total_bytes = 0

    for item in FRONTEND_DIR.iterdir():
        dest = TARGET_DIR / item.name
        if item.is_dir():
            shutil.copytree(item, dest, ignore=ignore_patterns)
            # count files
            for p in dest.rglob("*"):
                if p.is_file():
                    file_count += 1
                    total_bytes += p.stat().st_size
        else:
            shutil.copy2(item, dest)
            file_count += 1
            total_bytes += dest.stat().st_size

    print(f"[+] Synchronized {file_count} files ({total_bytes / (1024*1024):.2f} MB) to {TARGET_DIR}")
    
    # Sanity checks
    required_files = [
        "index.html",
        "js/call.js",
        "js/detector.js",
        "assets/alerts/alert_upi_pin_hi.wav",
        "assets/alerts/alert_upi_pin_chg.wav"
    ]
    
    all_ok = True
    for rf in required_files:
        check_path = TARGET_DIR / rf
        if not check_path.exists():
            print(f"[!] Warning: Missing critical asset: {rf}")
            all_ok = False
            
    if all_ok:
        print("[+] All critical dashboard assets verified in Android package directory.")
    else:
        print("[!] Asset verification had warnings.")

if __name__ == "__main__":
    sync_assets()
