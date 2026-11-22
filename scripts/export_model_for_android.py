"""
Export Suraksha Trained ML Model for Android Offline Inference
Reads backend/models/scam_model.joblib and exports vocabulary, IDF weights,
and Logistic Regression coefficients to android/app/src/main/assets/scam_model_weights.json.
Also exports test verification vectors for Android JUnit tests.
"""

import os
import sys
import json
from pathlib import Path
import joblib

workspace_dir = Path(__file__).resolve().parent.parent
model_path = workspace_dir / "backend" / "models" / "scam_model.joblib"
assets_dir = workspace_dir / "android" / "app" / "src" / "main" / "assets"
assets_dir.mkdir(parents=True, exist_ok=True)

if not model_path.exists():
    # If model not trained yet, run evaluation trainer
    sys.path.insert(0, str(workspace_dir / "backend"))
    from app.evaluation.run import run_pipeline
    run_pipeline()

print(f"Loading trained model from {model_path}...")
model = joblib.load(model_path)
clf = model.named_steps["clf"]
fu = model.named_steps["features"]
w_vec = fu.transformer_list[0][1]
c_vec = fu.transformer_list[1][1]

n_words = len(w_vec.vocabulary_)
w_coefs = clf.coef_[0][:n_words]
c_coefs = clf.coef_[0][n_words:]

word_dict = {}
for term, idx in w_vec.vocabulary_.items():
    idf = float(w_vec.idf_[idx])
    coef = float(w_coefs[idx])
    if abs(coef) > 0.0001:
        word_dict[term] = [round(idf, 5), round(coef, 5)]

char_dict = {}
for term, idx in c_vec.vocabulary_.items():
    idf = float(c_vec.idf_[idx])
    coef = float(c_coefs[idx])
    if abs(coef) > 0.0001:
        char_dict[term] = [round(idf, 5), round(coef, 5)]

export_data = {
    "model_name": "Suraksha-Scam-LR-v1.0",
    "version": "1.0.0",
    "algorithm": "FeatureUnion(TF-IDF Word 1-2 + Char 2-5) + LogisticRegression",
    "intercept": round(float(clf.intercept_[0]), 5),
    "threshold": 0.50,
    "word_features": word_dict,
    "char_features": char_dict
}

weights_out = assets_dir / "scam_model_weights.json"
with open(weights_out, "w", encoding="utf-8") as f:
    json.dump(export_data, f, ensure_ascii=False)

print(f"Saved weights ({os.path.getsize(weights_out) / 1024:.1f} KB) to {weights_out}")

# Metadata file
metadata = {
    "model_id": "suraksha_sms_v1",
    "name": "Suraksha Offline SMS Classifier",
    "format": "JSON_TFIDF_LOGREG",
    "classes": ["SAFE", "SPAM"],
    "total_word_features": len(word_dict),
    "total_char_features": len(char_dict),
    "total_features": len(word_dict) + len(char_dict),
    "training_date": "2026-11-22",
    "offline_capable": True
}

meta_out = assets_dir / "model_metadata.json"
with open(meta_out, "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2)

print(f"Saved metadata to {meta_out}")

# Generate Verification Test Vectors for Android Tests
test_samples = [
    {
        "text": "URGENT: CSPDCL Electricity officer notice. Your electricity power will be disconnected tonight at 9:30 PM due to unpaid bill of Rs 1,450. Call officer at 9876543210 immediately.",
        "expected_class": "SPAM"
    },
    {
        "text": "582910 is your secret One Time Password (OTP) for online purchase of Rs 450 at Amazon. DO NOT SHARE WITH ANYONE. Bank never calls to ask OTP.",
        "expected_class": "SAFE"
    },
    {
        "text": "CBI Cyber Crime Cell Notice: You are placed under DIGITAL ARREST. Do not disconnect this call or tell anyone. Pay clearance bond immediately.",
        "expected_class": "SPAM"
    },
    {
        "text": "Hey Ramesh, are you attending the gram panchayat meeting tomorrow morning in Raipur?",
        "expected_class": "SAFE"
    },
    {
        "text": "Dear user, aapka SBI YONO account block ho gaya hai. KYC update karne ke liye turant link bit.ly/sbi-kyc par click kare.",
        "expected_class": "SPAM"
    }
]

for s in test_samples:
    s["prob_scam"] = round(float(model.predict_proba([s["text"]])[0][1]), 4)

test_vectors_path = assets_dir / "test_vectors.json"
with open(test_vectors_path, "w", encoding="utf-8") as f:
    json.dump(test_samples, f, indent=2)

print(f"Saved test vectors to {test_vectors_path}")
print("Export completed successfully!")
