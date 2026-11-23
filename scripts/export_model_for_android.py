#!/usr/bin/env python3
"""The old JSON TF-IDF exporter is intentionally disabled for XLM-RoBERTa.

The Android OfflineSmsClassifier.kt expects sparse TF-IDF/LogisticRegression
weights. XLM-RoBERTa is a transformer and cannot be exported to that format.
Use a separate ONNX + tokenizer + ONNX Runtime Android migration instead.
"""
raise SystemExit(
    "This exporter is for the retired TF-IDF/LogisticRegression model. "
    "It cannot export XLM-RoBERTa. Keep the existing Android assets until "
    "an ONNX Runtime Android implementation is integrated and tested."
)
