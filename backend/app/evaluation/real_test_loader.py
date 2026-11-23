"""
Locked Real-World Test Set Loader and Evaluator for Suraksha
Validates zero data leakage against training data and benchmarks both:
1. Pure ML Model (Logistic Regression + TF-IDF)
2. Full Production Pipeline (ML + Normalizer + Rule Engine + Scam Engine)
"""

import json
from pathlib import Path
from difflib import SequenceMatcher
from typing import Dict, Any, List, Tuple

from app.detect.classifier import classify_text
from app.detect.pipeline import run_detection_pipeline
from app.detect.normalizer import normalize_text

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
REAL_TEST_PATH = ROOT_DIR / "data" / "real_test" / "locked_benchmark.json"
TRAIN_DATA_PATH = ROOT_DIR / "backend" / "data" / "dataset.json"

def load_locked_benchmark() -> List[Dict[str, Any]]:
    if not REAL_TEST_PATH.exists():
        raise FileNotFoundError(f"Locked benchmark not found at {REAL_TEST_PATH}")
    with open(REAL_TEST_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("samples", [])

def check_benchmark_leakage(train_dataset_path: Path = TRAIN_DATA_PATH) -> Dict[str, Any]:
    """Audits whether any sample in the locked benchmark exists in the training set."""
    if not train_dataset_path.exists():
        return {"error": f"Training dataset not found at {train_dataset_path}"}

    with open(train_dataset_path, "r", encoding="utf-8") as f:
        train_raw = json.load(f)

    train_texts = [item["text"] for item in train_raw if item.get("split") == "train" or "split" not in item]
    train_norm_map = {normalize_text(t)["clean"]: t for t in train_texts}

    benchmark_samples = load_locked_benchmark()
    exact_matches = []
    normalized_matches = []
    near_duplicates = []

    for item in benchmark_samples:
        raw_text = item["text"]
        norm_text = normalize_text(raw_text)["clean"]

        if raw_text in train_texts:
            exact_matches.append(raw_text)
        elif norm_text in train_norm_map:
            normalized_matches.append((raw_text, train_norm_map[norm_text]))
        else:
            # Check near-duplicates (SequenceMatcher >= 0.90)
            for t_norm in train_norm_map:
                if SequenceMatcher(None, norm_text, t_norm).ratio() >= 0.90:
                    near_duplicates.append((raw_text, train_norm_map[t_norm]))
                    break

    is_clean = (len(exact_matches) == 0 and len(normalized_matches) == 0 and len(near_duplicates) == 0)

    return {
        "total_benchmark_samples": len(benchmark_samples),
        "total_train_samples": len(train_texts),
        "exact_matches": len(exact_matches),
        "normalized_matches": len(normalized_matches),
        "near_duplicates": len(near_duplicates),
        "is_leak_free": is_clean
    }

def evaluate_locked_benchmark() -> Dict[str, Any]:
    """Evaluates both the raw ML model and the full detection pipeline on the locked benchmark."""
    samples = load_locked_benchmark()

    # 1. Evaluate Pure ML Model
    ml_tp, ml_fp, ml_tn, ml_fn = 0, 0, 0, 0
    pipe_tp, pipe_fp, pipe_tn, pipe_fn = 0, 0, 0, 0
    details = []

    for item in samples:
        text = item["text"]
        expected_scam = (item["label"] == 1 or item.get("expected_verdict") == "likely_scam")

        # ML alone
        ml_pred = classify_text(text)
        ml_scam = ml_pred["p_scam"] >= 0.50

        if expected_scam and ml_scam: ml_tp += 1
        elif not expected_scam and not ml_scam: ml_tn += 1
        elif not expected_scam and ml_scam: ml_fp += 1
        else: ml_fn += 1

        # Full pipeline
        pipe_pred = run_detection_pipeline(text, user_lang=item.get("language", "hi"))
        pipe_scam = (pipe_pred["verdict"] == "likely_scam")

        if expected_scam and pipe_scam: pipe_tp += 1
        elif not expected_scam and not pipe_scam: pipe_tn += 1
        elif not expected_scam and pipe_scam: pipe_fp += 1
        else: pipe_fn += 1

        details.append({
            "id": item["id"],
            "expected": "scam" if expected_scam else "genuine",
            "ml_p_scam": ml_pred["p_scam"],
            "pipe_verdict": pipe_pred["verdict"],
            "pipe_conf": pipe_pred.get("confidence_percent", 0),
            "language": item.get("language")
        })

    def calc_metrics(tp, tn, fp, fn):
        total = tp + tn + fp + fn
        acc = (tp + tn) / total if total > 0 else 0.0
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (tp + fn) if (tp + fn) > 0 else 0.0
        return {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "fpr": round(fpr, 4),
            "fnr": round(fnr, 4),
            "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn}
        }

    return {
        "leakage_audit": check_benchmark_leakage(),
        "pure_ml_metrics": calc_metrics(ml_tp, ml_tn, ml_fp, ml_fn),
        "full_pipeline_metrics": calc_metrics(pipe_tp, pipe_tn, pipe_fp, pipe_fn),
        "details": details
    }

if __name__ == "__main__":
    report = evaluate_locked_benchmark()
    print("=" * 65)
    print("LOCKED REAL-WORLD BENCHMARK EVALUATION")
    print("=" * 65)
    print("Leakage Status:", "CLEAN (0% LEAK)" if report["leakage_audit"]["is_leak_free"] else "LEAK DETECTED")
    print(f"Pure ML Model     : Acc={report['pure_ml_metrics']['accuracy']*100:.1f}%, F1={report['pure_ml_metrics']['f1']*100:.1f}%")
    print(f"Full Pipeline     : Acc={report['full_pipeline_metrics']['accuracy']*100:.1f}%, F1={report['full_pipeline_metrics']['f1']*100:.1f}%")
