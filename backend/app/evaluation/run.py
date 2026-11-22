"""
Unified Evaluation and Training Script for Suraksha
Run with:
  python -m app.evaluation.run (from backend/ directory)
or:
  python -m backend.app.evaluation.run (from workspace root)
"""

import sys
from pathlib import Path

# Ensure root paths are in sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
workspace_dir = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(workspace_dir) not in sys.path:
    sys.path.insert(0, str(workspace_dir))

from app.evaluation.dataset_generator import generate_synthetic_dataset
from app.evaluation.trainer import train_scam_model
from app.evaluation.evaluator import evaluate_model

def run_pipeline():
    print("=" * 60)
    print("🚀 SURAKSHA PIPELINE: DATASET -> TRAINING -> EVALUATION")
    print("=" * 60)

    data_dir = backend_dir / "data"
    models_dir = backend_dir / "models"
    data_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = data_dir / "dataset.json"
    metrics_path = data_dir / "metrics.json"

    # Step 1: Generate/load dataset
    dataset = generate_synthetic_dataset(output_path=dataset_path, target_count=3300)

    # Step 2: Train Model with 80/20 Stratified Split
    pipeline, test_dataset = train_scam_model(dataset, models_dir=models_dir, random_state=42)

    # Step 3: Evaluate on Held-Out Test Split
    results = evaluate_model(pipeline, test_dataset, output_path=metrics_path)

    print("\n✅ Training and Evaluation complete!")
    return results

if __name__ == "__main__":
    run_pipeline()
