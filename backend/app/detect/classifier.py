"""
ML Classifier Inference and Top N-Gram Explainer
Loads the joblib pipeline and computes calibrated probabilities and top contributing n-grams.
"""

from pathlib import Path
import joblib
import numpy as np

_MODEL_CACHE = None
_FEATURE_NAMES_CACHE = None
_COEFS_CACHE = None

def get_model(model_path: Path = None):
    global _MODEL_CACHE, _FEATURE_NAMES_CACHE, _COEFS_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    if model_path is None:
        model_path = Path(__file__).resolve().parent.parent.parent / "models" / "scam_model.joblib"

    if not model_path.exists():
        # Fallback if model not trained yet
        from app.evaluation.run import run_pipeline
        run_pipeline()

    _MODEL_CACHE = joblib.load(model_path)
    try:
        features_union = _MODEL_CACHE.named_steps["features"]
        clf = _MODEL_CACHE.named_steps["clf"]
        _FEATURE_NAMES_CACHE = [fn.split("__")[-1] for fn in features_union.get_feature_names_out()]
        _COEFS_CACHE = clf.coef_[0]
    except Exception:
        _FEATURE_NAMES_CACHE = None
        _COEFS_CACHE = None

    return _MODEL_CACHE

def classify_text(text: str) -> dict:
    pipeline = get_model()
    # Predict probabilities: [P(genuine), P(scam)]
    probs = pipeline.predict_proba([text])[0]
    p_genuine = float(probs[0])
    p_scam = float(probs[1])

    # Top contributing features
    top_ngrams = []
    try:
        if _FEATURE_NAMES_CACHE is not None and _COEFS_CACHE is not None:
            features_union = pipeline.named_steps["features"]
            X_feat = features_union.transform([text])
            contributions = X_feat.toarray()[0] * _COEFS_CACHE
            pos_indices = np.argsort(contributions)[::-1]

            for idx in pos_indices:
                if contributions[idx] > 0.05 and len(top_ngrams) < 6:
                    top_ngrams.append({
                        "ngram": _FEATURE_NAMES_CACHE[idx],
                        "weight": round(float(contributions[idx]), 3)
                    })
    except Exception as e:
        top_ngrams = []

    return {
        "p_scam": round(p_scam, 4),
        "p_genuine": round(p_genuine, 4),
        "top_contributing_ngrams": top_ngrams
    }
