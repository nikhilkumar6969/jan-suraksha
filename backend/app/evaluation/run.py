"""
Unified Evaluation and Training Script for Suraksha.
Fine-tunes XLM-RoBERTa on multilingual message dataset and evaluates held-out split.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent
workspace_dir = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(workspace_dir) not in sys.path:
    sys.path.insert(0, str(workspace_dir))

from app.evaluation.trainer import train_xlm_roberta

def run_pipeline():
    print("=" * 60)
    print("🚀 SURAKSHA PIPELINE: XLM-RoBERTa TRAINING & EVALUATION")
    print("=" * 60)
    return train_xlm_roberta()

if __name__ == "__main__":
    run_pipeline()
