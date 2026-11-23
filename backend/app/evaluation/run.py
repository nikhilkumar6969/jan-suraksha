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

import json
from app.evaluation.dataset_generator import generate_synthetic_dataset
from app.evaluation.trainer import train_scam_model
from app.evaluation.evaluator import evaluate_model

def load_combined_dataset(dataset_path: Path) -> list:
    train_jsonl_path = workspace_dir / "dataset" / "train.jsonl"
    jsonl_samples = []
    if train_jsonl_path.exists():
        print(f"[Dataset] Loading new dataset from {train_jsonl_path}...")
        with open(train_jsonl_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                line_str = line.strip()
                if line_str:
                    item = json.loads(line_str)
                    lang_raw = item.get("language", "English").lower()
                    if lang_raw in ["english", "en"]:
                        lang = "en"
                    elif lang_raw in ["hindi", "hi"]:
                        lang = "hi"
                    elif lang_raw in ["hinglish"]:
                        lang = "hinglish"
                    elif lang_raw in ["chhattisgarhi", "chg"]:
                        lang = "chg"
                    else:
                        lang = "en"
                    
                    split_type = "test" if (i % 7 == 0) else "train"
                    jsonl_samples.append({
                        "id": item.get("id", f"sample_{len(jsonl_samples)}"),
                        "text": item["text"],
                        "label": int(item["is_scam"]),
                        "label_name": "scam" if item["is_scam"] == 1 else "genuine",
                        "language": lang,
                        "split": split_type
                    })
        print(f"[Dataset] Loaded {len(jsonl_samples)} samples from {train_jsonl_path}.")

    # Also load regional synthetic dataset for Chhattisgarh dialects and genuine bank safety guards
    synth_dataset = generate_synthetic_dataset(output_path=dataset_path, target_count=3600)
    
    combined = jsonl_samples + synth_dataset
    print(f"[Dataset] Combined dataset total: {len(combined)} samples.")
    return combined

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

    # Step 1: Generate/load dataset (includes new dataset/train.jsonl if present)
    dataset = load_combined_dataset(dataset_path)

    # Step 2: Train Model with Stratified Split
    pipeline, test_dataset = train_scam_model(dataset, models_dir=models_dir, random_state=42)

    # Step 3: Evaluate on Held-Out Test Split
    results = evaluate_model(pipeline, test_dataset, output_path=metrics_path)

    print("\n✅ Training and Evaluation complete!")
    return results

if __name__ == "__main__":
    run_pipeline()
