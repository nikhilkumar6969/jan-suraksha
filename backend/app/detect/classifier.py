"""
XLM-RoBERTa message classifier used by the detection pipeline.
Provides local transformer inference with thread-safe singleton caching.
"""
from __future__ import annotations

from pathlib import Path
import threading
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

_MODEL = None
_TOKENIZER = None
_LOCK = threading.Lock()
_MAX_LENGTH = 256


def _model_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "models" / "xlm_roberta_spam"


def is_model_available() -> bool:
    mdir = _model_dir()
    return (mdir / "config.json").exists() and (
        (mdir / "model.safetensors").exists() or (mdir / "pytorch_model.bin").exists()
    )


def get_model():
    global _MODEL, _TOKENIZER
    if _MODEL is not None and _TOKENIZER is not None:
        return _MODEL, _TOKENIZER

    with _LOCK:
        if _MODEL is not None and _TOKENIZER is not None:
            return _MODEL, _TOKENIZER

        model_dir = _model_dir()
        if not (model_dir / "config.json").exists():
            raise RuntimeError(
                f"XLM-RoBERTa model not found at {model_dir}. "
                "Train it first: python scripts/train_xlm_roberta.py"
            )

        try:
            _TOKENIZER = AutoTokenizer.from_pretrained(
                str(model_dir), local_files_only=True, fix_mistral_regex=True
            )
        except TypeError:
            _TOKENIZER = AutoTokenizer.from_pretrained(str(model_dir), local_files_only=True)
        _MODEL = AutoModelForSequenceClassification.from_pretrained(
            str(model_dir), local_files_only=True
        )
        _MODEL.eval()
        _MODEL.to(torch.device("cpu"))
        return _MODEL, _TOKENIZER


def classify_text(text: str) -> dict:
    if not text or not text.strip():
        return {
            "p_scam": 0.0,
            "p_genuine": 1.0,
            "top_contributing_ngrams": [],
            "model_name": "XLM-RoBERTa",
        }

    model, tokenizer = get_model()
    encoded = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=_MAX_LENGTH,
        padding=True,
    )

    with torch.inference_mode():
        logits = model(**encoded).logits
        probabilities = torch.softmax(logits, dim=-1)[0]

    # Class mapping: 0 = GENUINE, 1 = SPAM
    p_genuine = float(probabilities[0].item())
    p_scam = float(probabilities[1].item())

    return {
        "p_scam": round(p_scam, 6),
        "p_genuine": round(p_genuine, 6),
        "top_contributing_ngrams": [],
        "model_name": "XLM-RoBERTa",
    }
