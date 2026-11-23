#!/usr/bin/env python3
"""Run from the Jan Suraksha repository root: python scripts/train_xlm_roberta.py"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.evaluation.trainer import train_xlm_roberta

if __name__ == "__main__":
    train_xlm_roberta()
