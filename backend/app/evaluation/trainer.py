"""
Model Trainer for Suraksha Scam Classifier
Uses FeatureUnion of word n-grams (1-2) and character n-grams (2-5)
with LogisticRegression (calibrated probabilities).
Saves model and vectorizer with joblib.
"""

from pathlib import Path
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from app.detect.normalizer import normalize_text

def train_scam_model(dataset: list, models_dir: Path = None, random_state: int = 42):
    has_explicit_split = any("split" in item for item in dataset)
    if has_explicit_split:
        train_items = [item for item in dataset if item.get("split") == "train"]
        test_items = [item for item in dataset if item.get("split") == "test"]
        
        # Apply adversarial & Chhattisgarhi dialect augmentation strictly to dialect/targeted training split
        from app.detect.augmentation import augment_training_dataset
        if len(train_items) > 10000:
            to_augment = [item for item in train_items if item.get("language") in ("hi", "chg", "hinglish")]
            plain_items = [item for item in train_items if item.get("language") not in ("hi", "chg", "hinglish")]
            augmented_train = plain_items + augment_training_dataset(to_augment, seed=random_state)
        else:
            augmented_train = augment_training_dataset(train_items, seed=random_state)
        
        train_texts = [normalize_text(item["text"])["clean"] for item in augmented_train]
        train_labels = [item["label"] for item in augmented_train]
        test_data = test_items
        test_texts = [normalize_text(item["text"])["clean"] for item in test_items]
    else:
        texts = [normalize_text(item["text"])["clean"] for item in dataset]
        labels = [item["label"] for item in dataset]
        languages = [item["language"] for item in dataset]

        # Stratified 80/20 split based on label and language combined
        stratify_col = [f"{lbl}_{lng}" for lbl, lng in zip(labels, languages)]
        train_texts, test_texts, train_labels, test_labels, train_idx, test_idx = train_test_split(
            texts, labels, list(range(len(texts))), test_size=0.20, random_state=random_state, stratify=stratify_col
        )
        test_data = [{
            "text": dataset[i]["text"],
            "label": labels[i],
            "language": languages[i]
        } for i in test_idx]

    # Robust word (1-2) and character (2-5) n-grams with min_df to eliminate noise and capture regional morphology
    feature_union = FeatureUnion([
        ("word_tfidf", TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            min_df=2,
            max_features=8000,
            sublinear_tf=True
        )),
        ("char_tfidf", TfidfVectorizer(
            analyzer="char",
            ngram_range=(2, 5),
            min_df=2,
            max_features=15000,
            sublinear_tf=True
        ))
    ])

    pipeline = Pipeline([
        ("features", feature_union),
        ("clf", LogisticRegression(
            C=0.8,
            max_iter=1000,
            solver="liblinear",
            random_state=random_state,
            class_weight="balanced"
        ))
    ])

    print(f"[Trainer] Training pipeline on {len(train_texts)} samples (held-out test set: {len(test_texts)} samples)...")
    pipeline.fit(train_texts, train_labels)

    if models_dir is None:
        models_dir = Path(__file__).resolve().parent.parent.parent / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    model_path = models_dir / "scam_model.joblib"
    joblib.dump(pipeline, model_path)
    print(f"[Trainer] Model successfully saved to {model_path}")

    # Return test set for rigorous evaluation
    if not has_explicit_split:
        test_data = [{
            "text": texts[i],
            "label": labels[i],
            "language": languages[i]
        } for i in test_idx]

    return pipeline, test_data
