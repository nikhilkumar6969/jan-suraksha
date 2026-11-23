#!/usr/bin/env python3
"""
Jan Suraksha ML Training & Benchmarking Suite
Evaluates cleaned datasets across 4 systematic experimental stages:
  Exp 1: In-Domain & Cross-Domain on Indian SMS
  Exp 2: In-Domain & Cross-Domain on UCI English SMS
  Exp 3: Multilingual Hindi Reference Evaluation
  Exp 4: Full Multi-Model Comparison on Master Cleaned Corpus
           (Logistic Regression, Calibrated LinearSVC, ComplementNB)
Computes:
  - Accuracy, Precision (Spam/Ham), Recall (Spam/Ham), F1-Score,
  - False Positive Rate (FPR), ROC-AUC, Confusion Matrix, Latency (ms)
Exports selected production model weights to backend/models/ & Android assets.
"""

import os
import sys
import time
import json
from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.naive_bayes import ComplementNB
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)
import joblib

ROOT_DIR = Path(__file__).resolve().parent.parent
CLEANED_DIR = ROOT_DIR / "backend" / "data" / "cleaned_datasets"
MODELS_DIR = ROOT_DIR / "backend" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR = ROOT_DIR / "backend" / "data" / "benchmark_results"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def build_feature_extractor():
    """Word (1-2) + Character (2-5) n-gram TF-IDF FeatureUnion."""
    return FeatureUnion([
        ("word_tfidf", TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            max_features=15000,
            sublinear_tf=True
        )),
        ("char_tfidf", TfidfVectorizer(
            analyzer="char",
            ngram_range=(2, 5),
            max_features=30000,
            sublinear_tf=True
        ))
    ])

def evaluate_predictions(y_true, y_pred, y_prob=None, latency_ms=0.0):
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    
    acc = float(accuracy_score(y_true, y_pred))
    prec_spam = float(precision_score(y_true, y_pred, pos_label=1, zero_division=0))
    rec_spam = float(recall_score(y_true, y_pred, pos_label=1, zero_division=0))
    f1_spam = float(f1_score(y_true, y_pred, pos_label=1, zero_division=0))
    
    prec_ham = float(precision_score(y_true, y_pred, pos_label=0, zero_division=0))
    rec_ham = float(recall_score(y_true, y_pred, pos_label=0, zero_division=0))
    f1_ham = float(f1_score(y_true, y_pred, pos_label=0, zero_division=0))
    
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    
    auc = None
    if y_prob is not None:
        try:
            auc = float(roc_auc_score(y_true, y_prob))
        except Exception:
            pass

    return {
        "accuracy": round(acc, 4),
        "precision_spam": round(prec_spam, 4),
        "recall_spam": round(rec_spam, 4),
        "f1_spam": round(f1_spam, 4),
        "precision_ham": round(prec_ham, 4),
        "recall_ham": round(rec_ham, 4),
        "f1_ham": round(f1_ham, 4),
        "false_positive_rate": round(fpr, 4),
        "roc_auc": round(auc, 4) if auc is not None else None,
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "latency_ms_per_sample": round(latency_ms, 3),
        "total_test_samples": len(y_true)
    }

def print_metrics_table(title, metrics):
    print(f"\n--- {title} ---")
    print(f"  Samples: {metrics['total_test_samples']} | Accuracy: {metrics['accuracy']*100:.2f}% | Latency: {metrics['latency_ms_per_sample']} ms/sample")
    print(f"  SPAM  -> Precision: {metrics['precision_spam']*100:.2f}% | Recall: {metrics['recall_spam']*100:.2f}% | F1: {metrics['f1_spam']*100:.2f}%")
    print(f"  HAM   -> Precision: {metrics['precision_ham']*100:.2f}% | Recall: {metrics['recall_ham']*100:.2f}% | F1: {metrics['f1_ham']*100:.2f}%")
    print(f"  FPR (False Positives on Ham): {metrics['false_positive_rate']*100:.2f}% | ROC-AUC: {metrics['roc_auc']}")
    cm = metrics['confusion_matrix']
    print(f"  Confusion Matrix: TN={cm['tn']}, FP={cm['fp']}, FN={cm['fn']}, TP={cm['tp']}")

def run_experiment_1():
    """Exp 1: Baseline Indian SMS Model & Cross-Domain Benchmark on UCI."""
    print("\n" + "=" * 70)
    print("EXPERIMENT 1: Indian SMS Dataset (In-Domain & Cross-Domain)")
    print("=" * 70)
    
    df_ind = pd.read_csv(CLEANED_DIR / "cleaned_indian_sms.csv")
    df_uci = pd.read_csv(CLEANED_DIR / "cleaned_uci_sms.csv")
    
    train = df_ind[df_ind["split"] == "train"]
    test_ind = df_ind[df_ind["split"] == "test"]
    test_uci = df_uci[df_uci["split"] == "test"]
    
    pipe = Pipeline([
        ("features", build_feature_extractor()),
        ("clf", LogisticRegression(C=1.5, max_iter=1000, solver="liblinear", class_weight="balanced", random_state=42))
    ])
    
    print(f"[*] Training on Indian SMS ({len(train)} samples)...")
    pipe.fit(train["text_clean"], train["label_num"])
    
    # In-domain eval
    t0 = time.perf_counter()
    probs_ind = pipe.predict_proba(test_ind["text_clean"])[:, 1]
    preds_ind = (probs_ind >= 0.5).astype(int)
    lat_ind = ((time.perf_counter() - t0) / len(test_ind)) * 1000
    m_ind = evaluate_predictions(test_ind["label_num"], preds_ind, probs_ind, lat_ind)
    print_metrics_table("Indian SMS -> In-Domain Test (Indian)", m_ind)
    
    # Cross-domain eval on UCI
    t0 = time.perf_counter()
    probs_uci = pipe.predict_proba(test_uci["text_clean"])[:, 1]
    preds_uci = (probs_uci >= 0.5).astype(int)
    lat_uci = ((time.perf_counter() - t0) / len(test_uci)) * 1000
    m_uci = evaluate_predictions(test_uci["label_num"], preds_uci, probs_uci, lat_uci)
    print_metrics_table("Indian SMS -> Cross-Domain Benchmark (UCI English)", m_uci)
    
    return {"in_domain": m_ind, "cross_domain_uci": m_uci}

def run_experiment_2():
    """Exp 2: UCI English Model & Cross-Domain Benchmark on Indian SMS."""
    print("\n" + "=" * 70)
    print("EXPERIMENT 2: UCI English SMS Dataset (In-Domain & Cross-Domain)")
    print("=" * 70)
    
    df_ind = pd.read_csv(CLEANED_DIR / "cleaned_indian_sms.csv")
    df_uci = pd.read_csv(CLEANED_DIR / "cleaned_uci_sms.csv")
    
    train = df_uci[df_uci["split"] == "train"]
    test_uci = df_uci[df_uci["split"] == "test"]
    test_ind = df_ind[df_ind["split"] == "test"]
    
    pipe = Pipeline([
        ("features", build_feature_extractor()),
        ("clf", LogisticRegression(C=1.5, max_iter=1000, solver="liblinear", class_weight="balanced", random_state=42))
    ])
    
    print(f"[*] Training on UCI English SMS ({len(train)} samples)...")
    pipe.fit(train["text_clean"], train["label_num"])
    
    # In-domain eval
    t0 = time.perf_counter()
    probs_uci = pipe.predict_proba(test_uci["text_clean"])[:, 1]
    preds_uci = (probs_uci >= 0.5).astype(int)
    lat_uci = ((time.perf_counter() - t0) / len(test_uci)) * 1000
    m_uci = evaluate_predictions(test_uci["label_num"], preds_uci, probs_uci, lat_uci)
    print_metrics_table("UCI English -> In-Domain Test (UCI)", m_uci)
    
    # Cross-domain eval on Indian SMS
    t0 = time.perf_counter()
    probs_ind = pipe.predict_proba(test_ind["text_clean"])[:, 1]
    preds_ind = (probs_ind >= 0.5).astype(int)
    lat_ind = ((time.perf_counter() - t0) / len(test_ind)) * 1000
    m_ind = evaluate_predictions(test_ind["label_num"], preds_ind, probs_ind, lat_ind)
    print_metrics_table("UCI English -> Cross-Domain Benchmark (Indian SMS)", m_ind)
    
    return {"in_domain": m_uci, "cross_domain_indian": m_ind}

def run_experiment_3():
    """Exp 3: Multilingual Hindi Reference Evaluation."""
    print("\n" + "=" * 70)
    print("EXPERIMENT 3: Multilingual Reference (Hindi Translation)")
    print("=" * 70)
    
    df_hi = pd.read_csv(CLEANED_DIR / "cleaned_multilingual_hi.csv")
    train = df_hi[df_hi["split"] == "train"]
    test = df_hi[df_hi["split"] == "test"]
    
    pipe = Pipeline([
        ("features", build_feature_extractor()),
        ("clf", LogisticRegression(C=1.5, max_iter=1000, solver="liblinear", class_weight="balanced", random_state=42))
    ])
    
    print(f"[*] Training on Multilingual Hindi Reference ({len(train)} samples)...")
    pipe.fit(train["text_hi_clean"], train["label_num"])
    
    t0 = time.perf_counter()
    probs = pipe.predict_proba(test["text_hi_clean"])[:, 1]
    preds = (probs >= 0.5).astype(int)
    lat = ((time.perf_counter() - t0) / len(test)) * 1000
    m_hi = evaluate_predictions(test["label_num"], preds, probs, lat)
    print_metrics_table("Multilingual Hindi Reference Test", m_hi)
    
    return m_hi

def run_experiment_4():
    """Exp 4: Multi-Model Benchmark on Master Cleaned Corpus."""
    print("\n" + "=" * 70)
    print("EXPERIMENT 4: Multi-Model Comparison on Master Cleaned Corpus (14,091 records)")
    print("=" * 70)
    
    df_master = pd.read_csv(CLEANED_DIR / "cleaned_master_corpus.csv")
    train = df_master[df_master["split"] == "train"]
    test = df_master[df_master["split"] == "test"]
    
    X_train, y_train = train["text"], train["label"]
    X_test, y_test = test["text"], test["label"]
    
    models = {
        "LogisticRegression_Balanced": LogisticRegression(
            C=1.5, max_iter=1000, solver="liblinear", class_weight="balanced", random_state=42
        ),
        "Calibrated_LinearSVC": CalibratedClassifierCV(
            LinearSVC(C=1.0, max_iter=2000, class_weight="balanced", random_state=42),
            method="sigmoid",
            cv=3
        ),
        "Complement_Naive_Bayes": ComplementNB(alpha=0.5)
    }
    
    results = {}
    best_f1 = -1
    best_pipe = None
    best_name = None
    pipe_lr = None
    
    for name, clf in models.items():
        print(f"\n[*] Training {name} on {len(X_train)} training records...")
        pipe = Pipeline([
            ("features", build_feature_extractor()),
            ("clf", clf)
        ])
        
        t_fit = time.perf_counter()
        pipe.fit(X_train, y_train)
        fit_time = time.perf_counter() - t_fit
        
        if name == "LogisticRegression_Balanced":
            pipe_lr = pipe
        
        t0 = time.perf_counter()
        if hasattr(pipe, "predict_proba"):
            probs = pipe.predict_proba(X_test)[:, 1]
            preds = (probs >= 0.5).astype(int)
        else:
            preds = pipe.predict(X_test)
            probs = None
        lat = ((time.perf_counter() - t0) / len(X_test)) * 1000
        
        m = evaluate_predictions(y_test, preds, probs, lat)
        m["training_time_sec"] = round(fit_time, 2)
        print_metrics_table(f"Model: {name}", m)
        results[name] = m
        
        if m["f1_spam"] > best_f1:
            best_f1 = m["f1_spam"]
            best_pipe = pipe
            best_name = name
            
    print(f"\n🏆 Best Selected Production Model: {best_name} (F1-Spam: {best_f1*100:.2f}%)")
    
    # LogisticRegression is the optimal native architecture matching Android's on-device sigmoid dot-product
    selected_prod_clf = pipe_lr if "LogisticRegression_Balanced" in models else best_pipe
    prod_model_path = MODELS_DIR / "scam_model.joblib"
    joblib.dump(selected_prod_clf, prod_model_path)
    print(f"[+] Saved optimal model to {prod_model_path} (Type: {selected_prod_clf.named_steps['clf'].__class__.__name__})")
    
    return results, "LogisticRegression_Balanced"

def export_to_android_assets():
    """Runs export_model_for_android.py to synchronize weights for Android."""
    print("\n" + "=" * 70)
    print("[*] Exporting Model Weights for Android Offline Inference...")
    print("=" * 70)
    export_script = ROOT_DIR / "scripts" / "export_model_for_android.py"
    if export_script.exists():
        import subprocess
        res = subprocess.run([sys.executable, str(export_script)], capture_output=True, text=True)
        print(res.stdout)
        if res.stderr:
            print("[!] Export stderr:", res.stderr)
    else:
        print("[!] Warning: export_model_for_android.py not found.")

def main():
    print("🚀 JAN SURAKSHA FULL MODEL TRAINING & EVALUATION PIPELINE")
    
    r1 = run_experiment_1()
    r2 = run_experiment_2()
    r3 = run_experiment_3()
    r4, best_model_name = run_experiment_4()
    
    all_benchmarks = {
        "exp1_indian_sms": r1,
        "exp2_uci_english": r2,
        "exp3_multilingual_hindi": r3,
        "exp4_master_comparison": r4,
        "selected_production_model": best_model_name
    }
    
    out_json = REPORT_DIR / "comprehensive_benchmark_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_benchmarks, f, indent=2)
    print(f"\n[+] Full benchmark metrics saved to {out_json}")
    
    # Update Android assets
    export_to_android_assets()

if __name__ == "__main__":
    main()
