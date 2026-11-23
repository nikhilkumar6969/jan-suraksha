"""
Empirical Benchmarking Script for Offline Transcription Modes
Evaluates:
- Mode A: Accuracy (Whisper Medium, beam_size=5, INT8 CPU)
- Mode B: Balanced (Whisper Small, beam_size=1, INT8 CPU) [DEFAULT]
- Mode C: Speed (Sherpa-ONNX Whisper Tiny, INT8 ONNX, VAD)

Measures exact runtime, Real-Time Factor (RTF), Process RAM, GPU VRAM,
and transcription text across identical Indian English, Hinglish, and Hindi audio samples.
"""

import os
import sys
import time
import json
import gc
import subprocess
from pathlib import Path

# Ensure backend is on sys.path
backend_root = Path(__file__).resolve().parent.parent
project_root = backend_root.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.audio.whisper_service import (
    transcribe_audio,
    MODE_ACCURACY,
    MODE_BALANCED,
    MODE_SPEED,
    get_whisper_model,
    get_sherpa_tiny_recognizer
)

def get_process_ram_mb() -> float:
    """Read current process WorkingSet / RSS in MB via psutil."""
    try:
        import psutil
        return round(psutil.Process().memory_info().rss / (1024 * 1024), 1)
    except Exception:
        return 0.0

def get_gpu_vram_mb() -> float:
    """Query NVIDIA GPU VRAM used in MB via nvidia-smi."""
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=3
        )
        if res.returncode == 0 and res.stdout.strip():
            return float(res.stdout.strip().split("\n")[0])
    except Exception:
        pass
    return 0.0

TEST_AUDIO_SAMPLES = [
    {
        "category": "Indian English (Digital Arrest Scam)",
        "path": project_root / "frontend" / "assets" / "samples" / "digital_arrest_call.wav",
        "ground_truth": "Hello this is Senior Inspector from Mumbai Police Crime Branch an arrest warrant is issued against you for illegal money laundering and narcotics parcel",
        "lang": "en"
    },
    {
        "category": "Hinglish (Bank KYC & OTP Scam)",
        "path": project_root / "frontend" / "assets" / "samples" / "bank_kyc_call.wav",
        "ground_truth": "Namaste this is SBI customer service calling your debit card and banking account will be blocked by 5pm today due to pending KYC update download AnyDesk app immediately and share the 6 digit verification OTP code",
        "lang": "en"
    },
    {
        "category": "Indian English (FedEx Customs Scam)",
        "path": project_root / "frontend" / "assets" / "samples" / "fedex_customs_call.wav",
        "ground_truth": "This is FedEx International Courier Department your parcel containing illegal narcotics and passports has been seized by customs officials press 1 to speak with investigation officer or pay customs penalty now",
        "lang": "en"
    },
    {
        "category": "Hindi (Police Cyber Advisory)",
        "path": project_root / "frontend" / "assets" / "alerts" / "alert_police_hi.wav",
        "ground_truth": "चेतावनी फर्जी पुलिस या डिजिटल अरेस्ट की धमकी से ना डरें कॉल तुरंत काटें",
        "lang": "hi"
    }
]

def calculate_word_accuracy(hyp: str, ref: str) -> float:
    """Calculates simple word recall/overlap percentage between hypothesis and reference."""
    import re
    hyp_words = set(re.findall(r'\b[A-Za-z\u0900-\u097F]+\b', hyp.lower()))
    ref_words = set(re.findall(r'\b[A-Za-z\u0900-\u097F]+\b', ref.lower()))
    if not ref_words:
        return 100.0
    overlap = len(hyp_words.intersection(ref_words))
    return round(float(overlap) / float(len(ref_words)) * 100.0, 1)

def run_benchmarks():
    print("=" * 80)
    print("OFFLINE SPEECH-TO-TEXT BENCHMARK SUITE")
    print("System: Windows 10 | 6-Core i5-11400H | 8 GB RAM | NVIDIA RTX 2050 (4 GB)")
    print("=" * 80)

    # Initial prewarm of models
    print("\nPrewarming models into memory...")
    get_whisper_model("small")
    get_whisper_model("medium")
    get_sherpa_tiny_recognizer("en")
    print("Prewarm complete.\n")

    results = []

    modes = [
        (MODE_SPEED, "Mode C: Speed (Sherpa Tiny ONNX)"),
        (MODE_BALANCED, "Mode B: Balanced (Whisper Small INT8) [DEFAULT]"),
        (MODE_ACCURACY, "Mode A: Accuracy (Whisper Medium INT8)")
    ]

    for mode_id, mode_label in modes:
        print(f"\n>>> BENCHMARKING: {mode_label} <<<")
        mode_results = {
            "mode_id": mode_id,
            "mode_label": mode_label,
            "samples": []
        }

        for sample in TEST_AUDIO_SAMPLES:
            sample_path = sample["path"]
            if not sample_path.exists():
                print(f"Skipping missing sample: {sample_path}")
                continue

            gc.collect()
            ram_before = get_process_ram_mb()
            vram_before = get_gpu_vram_mb()

            t0 = time.perf_counter()
            res = transcribe_audio(
                sample_path,
                language=sample["lang"],
                mode=mode_id
            )
            elapsed = time.perf_counter() - t0
            ram_after = get_process_ram_mb()
            vram_after = get_gpu_vram_mb()

            duration = res.get("duration", 0.0)
            rtf = round(elapsed / max(duration, 0.001), 3)
            acc = calculate_word_accuracy(res.get("text", ""), sample["ground_truth"])

            entry = {
                "category": sample["category"],
                "audio_duration_sec": duration,
                "transcription_time_sec": round(elapsed, 2),
                "rtf": rtf,
                "ram_usage_mb": ram_after,
                "gpu_vram_mb": vram_after,
                "word_accuracy_pct": acc,
                "text": res.get("text", "")
            }
            mode_results["samples"].append(entry)

            print(f"  [{sample['category']}]")
            print(f"    Duration: {duration:.2f}s | Time: {elapsed:.2f}s | RTF: {rtf:.3f}x")
            print(f"    RAM: {ram_after} MB | VRAM: {vram_after} MB | Accuracy: {acc}%")
            print(f"    Text: {res.get('text', '')[:90]}...")

        results.append(mode_results)

    # Save benchmark JSON for report generation
    out_json = project_root / "output" / "transcription_benchmark_results.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[SUCCESS] Benchmark results saved to: {out_json}")

if __name__ == "__main__":
    run_benchmarks()
