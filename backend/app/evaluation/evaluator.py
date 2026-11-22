"""
Evaluator for Suraksha Held-out Test Split
Computes accuracy, precision, recall, F1, FPR, and confusion matrix overall and per language.
Saves metrics to data/metrics.json.
"""

import json
from pathlib import Path
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

def compute_metrics(y_true, y_pred):
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp)
        },
        "sample_count": len(y_true)
    }

def evaluate_model(pipeline, test_dataset: list, output_path: Path = None):
    y_true = [item["label"] for item in test_dataset]
    texts = [item["text"] for item in test_dataset]
    languages = [item["language"] for item in test_dataset]

    y_pred = pipeline.predict(texts)

    overall_metrics = compute_metrics(y_true, y_pred)
    print(f"\n=================== HELD-OUT TEST EVALUATION ===================")
    print(f"Overall Samples: {overall_metrics['sample_count']}")
    print(f"Accuracy:        {overall_metrics['accuracy'] * 100:.2f}%")
    print(f"Precision:       {overall_metrics['precision'] * 100:.2f}%")
    print(f"Recall:          {overall_metrics['recall'] * 100:.2f}%")
    print(f"F1 Score:        {overall_metrics['f1'] * 100:.2f}%")
    print(f"FPR (False Pos): {overall_metrics['false_positive_rate'] * 100:.2f}%")
    print(f"Confusion Matrix: TN={overall_metrics['confusion_matrix']['tn']}, FP={overall_metrics['confusion_matrix']['fp']}, FN={overall_metrics['confusion_matrix']['fn']}, TP={overall_metrics['confusion_matrix']['tp']}")

    # Language-wise breakdown
    per_language = {}
    for lang in sorted(list(set(languages))):
        idx_lang = [i for i, l in enumerate(languages) if l == lang]
        y_true_lang = [y_true[i] for i in idx_lang]
        y_pred_lang = [y_pred[i] for i in idx_lang]
        per_language[lang] = compute_metrics(y_true_lang, y_pred_lang)
        print(f"--- Language: {lang:8s} | Acc: {per_language[lang]['accuracy']*100:.2f}% | Prec: {per_language[lang]['precision']*100:.2f}% | Rec: {per_language[lang]['recall']*100:.2f}% | F1: {per_language[lang]['f1']*100:.2f}% | FPR: {per_language[lang]['false_positive_rate']*100:.2f}%")

    results = {
        "status": "success",
        "dataset_info": {
            "total_synthetic_samples": 3300,
            "held_out_test_samples": len(test_dataset),
            "split_ratio": "80/20 stratified",
            "seed": 42
        },
        "overall": overall_metrics,
        "per_language": per_language
    }

    if output_path is None:
        output_path = Path(__file__).resolve().parent.parent.parent / "data" / "metrics.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[Evaluator] Saved detailed held-out metrics to {output_path}")
    return results
