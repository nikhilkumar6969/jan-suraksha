"""Fine-tune XLM-RoBERTa for binary scam-message classification.

Dataset format: backend/data/dataset.json
Each row: {"text": str, "label": 0|1, "language": str, "split": "train"|"test"}
Label convention: 0 = genuine/ham, 1 = scam/spam.
"""
from __future__ import annotations

import json
from pathlib import Path
from collections import Counter

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import torch
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)

MODEL_NAME = "FacebookAI/xlm-roberta-base"
# Max token length across the entire 3600-sample dataset is 72 tokens.
# 96 tokens provides 100% full preservation without any truncation while eliminating padding overhead.
MAX_LENGTH = 96


class MessageDataset(Dataset):
    def __init__(self, rows, tokenizer, max_length=MAX_LENGTH):
        self.texts = [str(row["text"]) for row in rows]
        self.labels = [int(row["label"]) for row in rows]
        self.encodings = tokenizer(
            self.texts,
            truncation=True,
            max_length=max_length,
            padding=False,
        )

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {key: torch.tensor(value[idx]) for key, value in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item


def _metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="binary", pos_label=1, zero_division=0
    )
    return {
        "accuracy": accuracy_score(labels, predictions),
        "spam_precision": precision,
        "spam_recall": recall,
        "spam_f1": f1,
    }


def _load_rows(dataset_path: Path):
    with dataset_path.open("r", encoding="utf-8") as f:
        rows = json.load(f)
    valid = []
    for row in rows:
        if not isinstance(row, dict) or not str(row.get("text", "")).strip():
            continue
        if row.get("label") not in (0, 1, "0", "1"):
            continue
        row = dict(row)
        row["label"] = int(row["label"])
        row["language"] = str(row.get("language", "unknown")).lower()
        valid.append(row)

    if not valid:
        raise ValueError(f"No usable labeled rows found in {dataset_path}")

    # Prefer the repository's existing fixed split. If unavailable, create a
    # stratified 80/20 split and keep the test set separate.
    train_rows = [r for r in valid if r.get("split") == "train"]
    test_rows = [r for r in valid if r.get("split") == "test"]
    if not train_rows or not test_rows:
        labels = [r["label"] for r in valid]
        train_rows, test_rows = train_test_split(
            valid, test_size=0.2, random_state=42, stratify=labels
        )

    if len({r["label"] for r in train_rows}) < 2:
        raise ValueError("Training data must contain both labels 0 (genuine) and 1 (scam).")
    if len({r["label"] for r in test_rows}) < 2:
        raise ValueError("Test data must contain both labels 0 (genuine) and 1 (scam).")

    print(f"[XLM-R] Train rows: {len(train_rows)} | Test rows: {len(test_rows)}")
    print("[XLM-R] Train label counts:", dict(Counter(r["label"] for r in train_rows)))
    print("[XLM-R] Train language counts:", dict(Counter(r["language"] for r in train_rows)))
    return train_rows, test_rows


def train_xlm_roberta(
    dataset_path: Path | None = None,
    output_dir: Path | None = None,
    model_name: str = MODEL_NAME,
    epochs: int = 2,
    batch_size: int = 16,
    max_length: int = MAX_LENGTH,
):
    try:
        torch.set_num_threads(6)
    except Exception:
        pass

    root = Path(__file__).resolve().parents[3]
    dataset_path = dataset_path or root / "backend" / "data" / "dataset.json"
    output_dir = output_dir or root / "backend" / "models" / "xlm_roberta_spam"

    train_rows, test_rows = _load_rows(Path(dataset_path))
    print(f"[XLM-R] Loading pretrained tokenizer and model: {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=2,
        id2label={0: "GENUINE", 1: "SPAM"},
        label2id={"GENUINE": 0, "SPAM": 1},
    )

    # Freeze embeddings (192M parameters) and lower 6 encoder layers to eliminate
    # massive gradient computation on CPU while preserving multilingual representations
    # and fine-tuning the top 6 transformer layers and classification head
    for p in model.roberta.embeddings.parameters():
        p.requires_grad = False
    for i in range(6):
        for p in model.roberta.encoder.layer[i].parameters():
            p.requires_grad = False

    # Build a small stratified validation set from training data for checkpoint selection
    train_core, val_rows = train_test_split(
        train_rows,
        test_size=0.1,
        random_state=42,
        stratify=[r["label"] for r in train_rows],
    )
    train_ds = MessageDataset(train_core, tokenizer, max_length)
    val_ds = MessageDataset(val_rows, tokenizer, max_length)
    test_ds = MessageDataset(test_rows, tokenizer, max_length)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    training_kwargs = {
        "output_dir": str(output_dir / "checkpoints"),
        "num_train_epochs": epochs,
        "per_device_train_batch_size": batch_size,
        "per_device_eval_batch_size": batch_size,
        "learning_rate": 2e-5,
        "weight_decay": 0.01,
        "warmup_ratio": 0.1,
        "save_strategy": "epoch",
        "load_best_model_at_end": True,
        "metric_for_best_model": "spam_f1",
        "greater_is_better": True,
        "logging_steps": 25,
        "save_total_limit": 2,
        "report_to": "none",
        "fp16": torch.cuda.is_available(),
        "dataloader_num_workers": 0,
        "seed": 42,
    }

    try:
        args = TrainingArguments(eval_strategy="epoch", **training_kwargs)
    except TypeError:
        args = TrainingArguments(evaluation_strategy="epoch", **training_kwargs)

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        compute_metrics=_metrics,
    )

    print(f"[XLM-R] Fine-tuning {model_name} on {len(train_ds)} messages ({epochs} epochs, batch_size={batch_size})")
    trainer.train()

    # Evaluate once on the untouched held-out test partition
    print(f"[XLM-R] Evaluating best checkpoint on held-out test set ({len(test_rows)} samples)...")
    test_output = trainer.predict(test_ds)
    y_true = np.asarray([r["label"] for r in test_rows])
    y_pred = np.argmax(test_output.predictions, axis=-1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary", pos_label=1, zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

    metrics = {
        "model": "XLM-RoBERTa",
        "base_model": model_name,
        "label_mapping": {"0": "GENUINE", "1": "SPAM"},
        "max_length": max_length,
        "test_samples": len(test_rows),
        "accuracy": float(round(accuracy_score(y_true, y_pred), 4)),
        "spam_precision": float(round(precision, 4)),
        "spam_recall": float(round(recall, 4)),
        "spam_f1": float(round(f1, 4)),
        "false_positive_rate": float(round(fpr, 4)),
        "false_negative_rate": float(round(fnr, 4)),
        "confusion_matrix": {
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "tp": tp,
        },
        "per_language": {},
    }

    per_language_metrics = {}
    for language in sorted({r["language"] for r in test_rows}):
        indices = [i for i, row in enumerate(test_rows) if row["language"] == language]
        if not indices:
            continue
        sub_y_true = y_true[indices]
        sub_y_pred = y_pred[indices]
        p, r, f, _ = precision_recall_fscore_support(
            sub_y_true, sub_y_pred, average="binary", pos_label=1, zero_division=0
        )
        sub_cm = confusion_matrix(sub_y_true, sub_y_pred, labels=[0, 1])
        sub_tn, sub_fp, sub_fn, sub_tp = int(sub_cm[0, 0]), int(sub_cm[0, 1]), int(sub_cm[1, 0]), int(sub_cm[1, 1])
        sub_fpr = float(sub_fp / (sub_fp + sub_tn)) if (sub_fp + sub_tn) > 0 else 0.0
        sub_fnr = float(sub_fn / (sub_fn + sub_tp)) if (sub_fn + sub_tp) > 0 else 0.0

        lang_metric = {
            "sample_count": len(indices),
            "accuracy": float(round(accuracy_score(sub_y_true, sub_y_pred), 4)),
            "precision": float(round(p, 4)),
            "recall": float(round(r, 4)),
            "f1": float(round(f, 4)),
            "false_positive_rate": float(round(sub_fpr, 4)),
            "false_negative_rate": float(round(sub_fnr, 4)),
            "confusion_matrix": {
                "tn": sub_tn,
                "fp": sub_fp,
                "fn": sub_fn,
                "tp": sub_tp,
            }
        }
        metrics["per_language"][language] = lang_metric
        per_language_metrics[language] = lang_metric

    # Save model/tokenizer at the directory expected by classifier.py
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    # Save detailed training metrics
    (output_dir / "training_metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Also update backend/data/metrics.json so the frontend evaluation view reflects XLM-RoBERTa
    data_metrics_path = root / "backend" / "data" / "metrics.json"
    dashboard_metrics = {
        "status": "success",
        "dataset_info": {
            "total_synthetic_samples": 3600,
            "held_out_test_samples": len(test_rows),
            "split_ratio": "80/20 held-out test split",
            "seed": 42,
            "model": "FacebookAI/xlm-roberta-base"
        },
        "overall": {
            "accuracy": metrics["accuracy"],
            "precision": metrics["spam_precision"],
            "recall": metrics["spam_recall"],
            "f1": metrics["spam_f1"],
            "false_positive_rate": metrics["false_positive_rate"],
            "false_negative_rate": metrics["false_negative_rate"],
            "confusion_matrix": metrics["confusion_matrix"],
            "sample_count": len(test_rows)
        },
        "per_language": per_language_metrics
    }
    data_metrics_path.write_text(
        json.dumps(dashboard_metrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(json.dumps(metrics, indent=2))
    print(f"[XLM-R] Model and tokenizer saved to: {output_dir}")
    print(f"[XLM-R] Metrics saved to {data_metrics_path} and {output_dir / 'training_metrics.json'}")
    return metrics


def train_scam_model(dataset: list = None, models_dir: Path = None, random_state: int = 42):
    """Compatibility wrapper redirecting to train_xlm_roberta."""
    return train_xlm_roberta()


if __name__ == "__main__":
    train_xlm_roberta()
