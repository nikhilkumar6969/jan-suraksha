"""
Download Script for Whisper Medium (faster-whisper)
Downloads the official CTranslate2 Whisper Medium model (~769M parameters)
into the local directory for 100% offline, private inference.
"""

import os
import sys
from pathlib import Path

# Set UTF8 encoding for Windows console
os.environ["PYTHONUTF8"] = "1"

# Determine model directory
project_root = Path(__file__).resolve().parent.parent.parent
target_dir = project_root / "models" / "whisper-medium"

def download():
    from faster_whisper import download_model
    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading Whisper Medium model into: {target_dir}")
    print("This is a one-time download (~1.5 GB). After download, transcription works 100% offline.")
    
    output_path = download_model("medium", output_dir=str(target_dir))
    print(f"\n[SUCCESS] Whisper Medium model successfully downloaded to: {output_path}")
    print("Model files:")
    for f in target_dir.iterdir():
        print(f" - {f.name} ({f.stat().st_size / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    download()
