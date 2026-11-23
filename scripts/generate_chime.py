"""
Generates the offline audio alert library for Jan Suraksha:
- alert_chime.wav: Attention chime (dual-tone harmonic warning)
- Alert voice files in Hindi (hi), Chhattisgarhi (chg), and English (en)
"""

import os
import numpy as np
from scipy.io import wavfile

ALERTS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "frontend", "assets", "alerts"
)
os.makedirs(ALERTS_DIR, exist_ok=True)


def generate_chime():
    sr = 44100
    t1 = np.linspace(0, 0.18, int(sr * 0.18), False)
    t2 = np.linspace(0, 0.28, int(sr * 0.28), False)

    # Note 1: 880 Hz (A5) with slight 1760 Hz harmonic
    tone1 = 0.7 * np.sin(2 * np.pi * 880 * t1) + 0.3 * np.sin(
        2 * np.pi * 1760 * t1
    )
    env1 = np.exp(-t1 * 12)
    sig1 = tone1 * env1

    # Note 2: 1318.5 Hz (E6) with harmonic
    tone2 = 0.7 * np.sin(2 * np.pi * 1318.5 * t2) + 0.3 * np.sin(
        2 * np.pi * 2637 * t2
    )
    env2 = np.exp(-t2 * 8)
    sig2 = tone2 * env2

    # Silence gap
    gap = np.zeros(int(sr * 0.04))

    chime = np.concatenate([sig1, gap, sig2])
    # Normalize to 16-bit PCM
    chime_norm = (chime / np.max(np.abs(chime)) * 30000).astype(np.int16)

    out_path = os.path.join(ALERTS_DIR, "alert_chime.wav")
    wavfile.write(out_path, sr, chime_norm)
    print(f"Generated chime: {out_path} ({len(chime_norm)/sr:.2f}s)")


if __name__ == "__main__":
    generate_chime()
