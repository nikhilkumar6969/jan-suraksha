"""
Test Suite for Locked Real-World Benchmark Dataset Isolation & Leakage
Ensures:
1. data/real_test/locked_benchmark.json exists and is valid.
2. 0.00% exact, normalized, or high-similarity overlap with backend/data/dataset.json.
3. Benchmark samples have valid labels and categories.
"""

import sys
from pathlib import Path
import pytest

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.evaluation.real_test_loader import (
    load_locked_benchmark,
    check_benchmark_leakage,
    evaluate_locked_benchmark
)

def test_locked_benchmark_exists_and_valid():
    samples = load_locked_benchmark()
    assert len(samples) >= 15, f"Expected at least 15 locked benchmark samples, found {len(samples)}"
    for s in samples:
        assert "text" in s and len(s["text"].strip()) > 10
        assert s.get("label") in (0, 1)
        assert s.get("expected_verdict") in ("genuine", "likely_scam")
        assert "category" in s
        assert "language" in s

def test_zero_leakage_with_training_data():
    audit = check_benchmark_leakage()
    assert "error" not in audit, f"Audit encountered error: {audit.get('error')}"
    assert audit["exact_matches"] == 0, f"Found {audit['exact_matches']} exact matches with training set"
    assert audit["normalized_matches"] == 0, f"Found {audit['normalized_matches']} normalized matches with training set"
    assert audit["near_duplicates"] == 0, f"Found {audit['near_duplicates']} near duplicates with training set"
    assert audit["is_leak_free"] is True

def test_locked_benchmark_evaluation():
    eval_res = evaluate_locked_benchmark()
    pipe_metrics = eval_res["full_pipeline_metrics"]
    assert pipe_metrics["accuracy"] >= 0.85, f"Pipeline accuracy on locked benchmark is {pipe_metrics['accuracy']}"
    assert pipe_metrics["f1"] >= 0.85, f"Pipeline F1 score on locked benchmark is {pipe_metrics['f1']}"
