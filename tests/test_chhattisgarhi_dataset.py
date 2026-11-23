"""
Automated Evaluation and Benchmarking Suite for Chhattisgarhi Dialect Scam Detection
Evaluates the 20 documented scenarios in backend/data/chhattisgarhi_eval_dataset.json against
the offline scam engine and ConversationTimelineTracker.
"""

import json
import os
import pytest
from backend.app.detect.scam_engine import detect_scam_in_transcript
from backend.app.calls.conversation_tracker import ConversationTimelineTracker

DATASET_PATH = os.path.join(
    os.path.dirname(__file__), "..", "backend", "data", "chhattisgarhi_eval_dataset.json"
)


def load_dataset():
    assert os.path.exists(DATASET_PATH), f"Dataset file missing at {DATASET_PATH}"
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_chhattisgarhi_dataset_coverage():
    """Verify dataset structure, variety of dialect regions, and scenario coverage."""
    dataset = load_dataset()
    samples = dataset.get("samples", [])
    assert len(samples) >= 40, f"Expected at least 40 evaluation samples, got {len(samples)}"

    regions = " ".join(s.get("dialect_region", "") for s in samples)
    for expected_keyword in ["Raipur", "Durg", "Bilaspur", "Bastar", "Surguja"]:
        assert expected_keyword in regions, f"Missing expected dialect region containing: {expected_keyword}"

    scam_count = sum(1 for s in samples if s.get("is_scam"))
    benign_count = sum(1 for s in samples if not s.get("is_scam"))
    assert scam_count >= 25, f"Expected >= 25 scam samples, got {scam_count}"
    assert benign_count >= 12, f"Expected >= 12 benign samples, got {benign_count}"


def test_chhattisgarhi_scam_detection_accuracy():
    """
    Evaluate scam engine accuracy across all 20 Chhattisgarhi dialect samples.
    Computes precision, recall, false-positive rate, and per-category verification.
    """
    dataset = load_dataset()
    samples = dataset.get("samples", [])

    true_positives = 0
    false_positives = 0
    true_negatives = 0
    false_negatives = 0

    results = []

    for s in samples:
        transcript = s["text"]
        is_scam_gt = s["is_scam"]
        expected_category = s.get("category")

        eval_result = detect_scam_in_transcript(transcript)
        detected_as_scam = eval_result["is_scam"] or eval_result["risk_level"] in [
            "HIGH",
            "CRITICAL",
        ]

        if is_scam_gt and detected_as_scam:
            true_positives += 1
            if expected_category and expected_category != "benign":
                assert eval_result["scam_category"] != "सुरक्षित बातचीत (Benign/Safe)", (
                    f"Sample {s['id']} detected as scam but category is safe"
                )
        elif not is_scam_gt and not detected_as_scam:
            true_negatives += 1
        elif not is_scam_gt and detected_as_scam:
            false_positives += 1
            print(f"\n[FALSE POSITIVE] ID: {s['id']} | Text: {transcript}")
            print(f"Detected as: {eval_result['risk_level']} - {eval_result['scam_category']}")
            print(f"Matched phrases: {eval_result['suspicious_phrases']}")
        elif is_scam_gt and not detected_as_scam:
            false_negatives += 1
            print(f"\n[FALSE NEGATIVE] ID: {s['id']} | Text: {transcript}")
            print(f"Expected: {expected_category} | Detected: {eval_result['risk_level']}")

        results.append({
            "id": s["id"],
            "region": s.get("dialect_region"),
            "gt_is_scam": is_scam_gt,
            "detected": detected_as_scam,
            "risk_level": eval_result["risk_level"],
            "scam_category": eval_result["scam_category"],
            "suspicious_phrases": eval_result["suspicious_phrases"],
        })

    total = len(samples)
    accuracy = (true_positives + true_negatives) / total
    precision = (
        true_positives / (true_positives + false_positives)
        if (true_positives + false_positives) > 0
        else 0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if (true_positives + false_negatives) > 0
        else 0
    )
    fpr = (
        false_positives / (false_positives + true_negatives)
        if (false_positives + true_negatives) > 0
        else 0
    )

    print("\n" + "=" * 60)
    print("CHHATTISGARHI DIALECT BENCHMARK RESULTS")
    print("=" * 60)
    print(f"Total Samples Evaluated:        {total}")
    print(f"True Positives (Scams Caught):   {true_positives}")
    print(f"True Negatives (Benign Passed):  {true_negatives}")
    print(f"False Positives (False Alarms):  {false_positives}")
    print(f"False Negatives (Missed Scams):  {false_negatives}")
    print(f"Overall Accuracy:               {accuracy * 100:.2f}%")
    print(f"Precision:                      {precision * 100:.2f}%")
    print(f"Recall (Sensitivity):           {recall * 100:.2f}%")
    print(f"False Positive Rate:            {fpr * 100:.2f}%")
    print("=" * 60)

    # Acceptance Criteria for Real-World Field Readiness
    assert recall == 1.0, f"Recall must be 100% on scam cases (got {recall*100:.2f}%)"
    assert fpr == 0.0, f"False Positive Rate must be 0% on benign controls (got {fpr*100:.2f}%)"
    assert precision == 1.0, f"Precision must be 100% (got {precision*100:.2f}%)"


def test_chhattisgarhi_5stage_lifecycle_tracking():
    """Verify that Chhattisgarhi conversation transcripts trigger progressive stages in ConversationTimelineTracker."""
    tracker = ConversationTimelineTracker(session_id="cg_test_session")

    # Step 1: Trust Claim in Chhattisgarhi
    t1 = tracker.add_utterance(
        "नमस्ते, मंय बैंक ऑफ बड़ौदा बैंक अधिकारी बोलत हंव। तोर खाता नंबर ल सत्यापित करना हे।"
    )
    active_stage_keys = set(tracker.active_stages.keys())
    assert 1 in active_stage_keys, "Stage 1 (Trust Claim) should be active"

    # Step 2: Fear & Urgency
    t2 = tracker.add_utterance(
        "जल्दी करा नइ त संझा 9:30 बजे तोर खाता ब्लॉक हो जाही अउ लाइन कट जाही।"
    )
    active_stage_keys = set(tracker.active_stages.keys())
    assert 2 in active_stage_keys, "Stage 2 (Fear & Urgency) should be active"

    # Step 3: Sensitive Info Demand (UPI PIN / OTP)
    t3 = tracker.add_utterance(
        "तोर मोबाइल म 6 अंक के गुप्त ओटीपी आइस हे ओला तुरंत बतावव।"
    )
    active_stage_keys = set(tracker.active_stages.keys())
    assert 3 in active_stage_keys, "Stage 3 (Sensitive Info Request) should be active"

    # Step 4: Device Compromise (AnyDesk / RustDesk)
    t4 = tracker.add_utterance(
        "अपन मोबाइल म anydesk ऐप डाउनलोड करव अउ 9 अंक के कोड बताहू।"
    )
    active_stage_keys = set(tracker.active_stages.keys())
    assert 5 in active_stage_keys, "Stage 5 (Device Compromise) should be active"

    # Verify cumulative progression
    assert t4["progression_percent"] >= 60
    assert t4["stages_active_count"] >= 4
