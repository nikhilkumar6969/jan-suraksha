"""
Jan Suraksha - Detection Calibration & Hardened Evaluation Engine
Computes:
  - Accuracy, Precision, Recall, F1
  - False Positive Rate (FPR), False Negative Rate (FNR)
  - Confusion Matrix (TN, FP, FN, TP)
  - Expected Calibration Error (ECE, 10 bins)
  - Maximum Calibration Error (MCE)
  - Brier Score
  - Category-wise & Language-wise metrics breakdown
Saves detailed JSON metrics to data/calibration_metrics.json.
"""

import json
from pathlib import Path
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, brier_score_loss

def compute_classification_metrics(y_true, y_pred):
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

    return {
        "sample_count": len(y_true),
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp)
        }
    }

def compute_calibration_metrics(y_true, p_pred, n_bins=10):
    """
    Computes Expected Calibration Error (ECE), Maximum Calibration Error (MCE),
    Brier Score, and reliability diagram bin statistics.
    """
    y_true = np.array(y_true)
    p_pred = np.array(p_pred)
    
    brier = float(brier_score_loss(y_true, p_pred))
    
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_data = []
    ece = 0.0
    mce = 0.0
    total_samples = len(y_true)

    for i in range(n_bins):
        low, high = bin_edges[i], bin_edges[i + 1]
        if i == n_bins - 1:
            in_bin = (p_pred >= low) & (p_pred <= high)
        else:
            in_bin = (p_pred >= low) & (p_pred < high)
            
        count = int(np.sum(in_bin))
        if count > 0:
            bin_acc = float(np.mean(y_true[in_bin]))
            bin_conf = float(np.mean(p_pred[in_bin]))
            gap = abs(bin_acc - bin_conf)
            weight = count / total_samples
            ece += weight * gap
            mce = max(mce, gap)
            bin_data.append({
                "bin_range": f"{low:.1f}-{high:.1f}",
                "count": count,
                "confidence": round(bin_conf, 4),
                "empirical_accuracy": round(bin_acc, 4),
                "calibration_gap": round(gap, 4)
            })
        else:
            bin_data.append({
                "bin_range": f"{low:.1f}-{high:.1f}",
                "count": 0,
                "confidence": round((low + high) / 2.0, 4),
                "empirical_accuracy": 0.0,
                "calibration_gap": 0.0
            })

    return {
        "expected_calibration_error": round(float(ece), 4),
        "maximum_calibration_error": round(float(mce), 4),
        "brier_score": round(brier, 4),
        "n_bins": n_bins,
        "bins": bin_data
    }

def run_calibration_evaluation(
    eval_dataset_path: Path = None,
    output_path: Path = None
):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from app.detect.pipeline import run_detection_pipeline

    if eval_dataset_path is None:
        eval_dataset_path = Path(__file__).resolve().parent.parent.parent / "data" / "hardened_eval_dataset.json"

    with open(eval_dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    samples = data["samples"]
    print(f"\n==================================================================")
    print(f" JAN SURAKSHA DETECTION BENCHMARK & CALIBRATION EVALUATION")
    print(f" Dataset: {eval_dataset_path.name} ({len(samples)} independently labelled samples)")
    print(f"==================================================================")

    y_true = []
    y_pred = []
    p_scam_list = []
    calibrated_conf_list = []
    category_results = {}
    language_results = {}

    for s in samples:
        target_lang = s.get("language", "hi")
        if target_lang == "hinglish":
            user_lang = "hi"
        elif target_lang == "chg":
            user_lang = "chg"
        elif target_lang == "en":
            user_lang = "en"
        else:
            user_lang = "hi"

        res = run_detection_pipeline(s["text"], user_lang=user_lang)
        
        # Classification mapping:
        # In cybersecurity detection, "likely_scam" and "unsure" (suspicious/verify) are flags (1),
        # whereas "genuine" is benign (0).
        is_flagged = 1 if res["verdict"] in ["likely_scam", "unsure"] else 0
        expected = s["expected_label"]

        y_true.append(expected)
        y_pred.append(is_flagged)
        
        # For calibration:
        # 1. Raw ML Classifier probability
        p_scam = res["model_probability"]["p_scam"]
        p_scam_list.append(p_scam)

        # 2. Final Calibrated Hybrid Risk probability:
        v = res["verdict"]
        c = res["calibrated_confidence"]
        if v == "likely_scam":
            p_hybrid = c
        elif v == "unsure":
            p_hybrid = 0.60
        else:
            p_hybrid = round(1.0 - c, 4)
        calibrated_conf_list.append(p_hybrid)

        cat = s["category"]
        if cat not in category_results:
            category_results[cat] = {"y_true": [], "y_pred": [], "samples": []}
        category_results[cat]["y_true"].append(expected)
        category_results[cat]["y_pred"].append(is_flagged)
        category_results[cat]["samples"].append({
            "id": s["id"],
            "text": s["text"],
            "expected_verdict": s["expected_verdict"],
            "actual_verdict": res["verdict"],
            "confidence_percent": res["confidence_percent"],
            "calibrated_confidence": res["calibrated_confidence"],
            "model_probability": res["model_probability"],
            "rule_risk": res["rule_risk"],
            "combined_score": res["combined_score"],
            "correct": (expected == is_flagged)
        })

        lng = s.get("language", "en")
        if lng not in language_results:
            language_results[lng] = {"y_true": [], "y_pred": []}
        language_results[lng]["y_true"].append(expected)
        language_results[lng]["y_pred"].append(is_flagged)

    overall_metrics = compute_classification_metrics(y_true, y_pred)
    raw_ml_calibration = compute_calibration_metrics(y_true, p_scam_list)
    hybrid_calibrated_metrics = compute_calibration_metrics(y_true, calibrated_conf_list)

    print(f"\n--- OVERALL PERFORMANCE METRICS ---")
    print(f"Total Evaluated Samples:            {overall_metrics['sample_count']}")
    print(f"Accuracy:                           {overall_metrics['accuracy'] * 100:.2f}%")
    print(f"Precision:                          {overall_metrics['precision'] * 100:.2f}%")
    print(f"Recall:                             {overall_metrics['recall'] * 100:.2f}%")
    print(f"F1 Score:                           {overall_metrics['f1'] * 100:.2f}%")
    print(f"False Positive Rate (FPR):          {overall_metrics['false_positive_rate'] * 100:.2f}%")
    print(f"False Negative Rate (FNR):          {overall_metrics['false_negative_rate'] * 100:.2f}%")
    cm = overall_metrics['confusion_matrix']
    print(f"Confusion Matrix:                   TN={cm['tn']} | FP={cm['fp']} | FN={cm['fn']} | TP={cm['tp']}")
    print(f"\n--- CALIBRATION METRICS ---")
    print(f"Raw ML ECE (10 bins):               {raw_ml_calibration['expected_calibration_error'] * 100:.2f}%")
    print(f"Raw ML Brier Score:                 {raw_ml_calibration['brier_score']:.4f}")
    print(f"Calibrated Hybrid Risk ECE:         {hybrid_calibrated_metrics['expected_calibration_error'] * 100:.2f}%")
    print(f"Calibrated Hybrid Risk MCE:         {hybrid_calibrated_metrics['maximum_calibration_error'] * 100:.2f}%")
    print(f"Calibrated Hybrid Brier Score:      {hybrid_calibrated_metrics['brier_score']:.4f}")

    print(f"\n--- CATEGORY BREAKDOWN ---")
    cat_metrics = {}
    for cat, data_cat in category_results.items():
        m = compute_classification_metrics(data_cat["y_true"], data_cat["y_pred"])
        cat_metrics[cat] = {
            "metrics": m,
            "samples": data_cat["samples"]
        }
        print(f"  [{cat:20s}] Count: {m['sample_count']:2d} | Acc: {m['accuracy']*100:6.2f}% | Prec: {m['precision']*100:6.2f}% | Rec: {m['recall']*100:6.2f}% | FPR: {m['false_positive_rate']*100:5.2f}%")

    print(f"\n--- LANGUAGE BREAKDOWN ---")
    lang_metrics = {}
    for lng, data_lng in language_results.items():
        m = compute_classification_metrics(data_lng["y_true"], data_lng["y_pred"])
        lang_metrics[lng] = m
        print(f"  [{lng:10s}] Count: {m['sample_count']:2d} | Acc: {m['accuracy']*100:6.2f}% | Prec: {m['precision']*100:6.2f}% | Rec: {m['recall']*100:6.2f}% | FPR: {m['false_positive_rate']*100:5.2f}%")

    output_report = {
        "status": "success",
        "dataset_metadata": data.get("metadata", {}),
        "overall_classification": overall_metrics,
        "calibration": {
            "raw_ml_classifier": raw_ml_calibration,
            "calibrated_hybrid_risk": hybrid_calibrated_metrics
        },
        "category_metrics": cat_metrics,
        "language_metrics": lang_metrics
    }

    if output_path is None:
        output_path = Path(__file__).resolve().parent.parent.parent / "data" / "calibration_metrics.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_report, f, ensure_ascii=False, indent=2)

    print(f"\n[Calibration Evaluator] Results successfully exported to {output_path}")
    return output_report

if __name__ == "__main__":
    run_calibration_evaluation()
