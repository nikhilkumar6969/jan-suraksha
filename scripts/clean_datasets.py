#!/usr/bin/env python3
"""
Jan Suraksha Dataset Cleaning & Normalization Pipeline
Cleans and standardizes raw datasets:
  1. Indian SMS Spam Real (01_indian_sms/indian_sms_spam_real.csv)
  2. UCI SMS Spam English (02_uci_sms/uci_sms_spam_english.csv)
  3. Multilingual Reference (03_multilingual_reference/data-en-hi-de-fr.csv)

Applies:
  - HTML entity unescaping
  - Zero-width character removal & Unicode NFC normalization
  - Whitespace collapsing
  - Exact & semantic deduplication
  - Label standardization (ham -> 0, spam -> 1)
  - Stratified 80/20 train/test splitting
Saves cleaned CSVs to backend/data/cleaned_datasets/
"""

import os
import re
import html
import unicodedata
import json
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "backend" / "data" / "raw_datasets" / "Cyber_Fraud_Datasets"
OUTPUT_DIR = ROOT_DIR / "backend" / "data" / "cleaned_datasets"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ZERO_WIDTH_PATTERN = re.compile(r"[\u200b\u200c\u200d\u200e\u200f\ufeff\u00ad]")
WHITESPACE_PATTERN = re.compile(r"\s+")

def clean_text(text: str) -> str:
    """Performs rigorous text normalization."""
    if not isinstance(text, str):
        return ""
    # 1. Unescape HTML entities (&amp; -> &, &lt; -> <, &#123;, etc.)
    text = html.unescape(text)
    # 2. Remove zero-width & non-printable control characters
    text = ZERO_WIDTH_PATTERN.sub("", text)
    # 3. Unicode normalization (NFC)
    text = unicodedata.normalize("NFC", text)
    # 4. Collapse whitespace & strip
    text = WHITESPACE_PATTERN.sub(" ", text).strip()
    return text

def is_valid_message(text: str) -> bool:
    """Filters out trivial, empty or noise-only messages."""
    if len(text) < 2:
        return False
    # Must contain at least one alphanumeric or Devanagari character
    has_alphanumeric = bool(re.search(r"[\w\u0900-\u097F]", text))
    return has_alphanumeric

def standardize_label(lbl) -> int:
    """Maps ham/safe to 0 and spam/fraud to 1."""
    if isinstance(lbl, (int, float)):
        return 1 if int(lbl) == 1 else 0
    val = str(lbl).strip().lower()
    if val in ["spam", "fraud", "1", "true", "yes"]:
        return 1
    return 0

def process_indian_sms():
    print("=" * 60)
    print("[*] Processing 01_indian_sms (Indian SMS Real)...")
    path = RAW_DIR / "01_indian_sms" / "indian_sms_spam_real.csv"
    df = pd.read_csv(path)
    initial_count = len(df)
    
    df["text_clean"] = df["text"].apply(clean_text)
    df["label_num"] = df["label"].apply(standardize_label)
    
    # Filter valid
    df = df[df["text_clean"].apply(is_valid_message)].copy()
    valid_count = len(df)
    
    # Deduplicate on cleaned text
    df = df.drop_duplicates(subset=["text_clean"]).copy()
    dedup_count = len(df)
    
    # Stratified train/test split
    strat_key = df["label_num"].astype(str) + "_" + df["language"].astype(str)
    train_idx, test_idx = train_test_split(
        df.index, test_size=0.20, random_state=42, stratify=strat_key
    )
    df["split"] = "train"
    df.loc[test_idx, "split"] = "test"
    
    out_path = OUTPUT_DIR / "cleaned_indian_sms.csv"
    df[["id", "text_clean", "label_num", "language", "source", "split"]].to_csv(
        out_path, index=False, encoding="utf-8"
    )
    
    stats = {
        "dataset": "Indian SMS",
        "initial_rows": initial_count,
        "valid_rows": valid_count,
        "dedup_rows": dedup_count,
        "spam_count": int(df["label_num"].sum()),
        "ham_count": int((df["label_num"] == 0).sum()),
        "train_rows": int((df["split"] == "train").sum()),
        "test_rows": int((df["split"] == "test").sum()),
        "languages": df["language"].value_counts().to_dict()
    }
    print(f"    Cleaned: {dedup_count} rows (Spam: {stats['spam_count']}, Ham: {stats['ham_count']})")
    print(f"    Train: {stats['train_rows']}, Test: {stats['test_rows']}")
    print(f"    Saved -> {out_path}")
    return df, stats

def process_uci_sms():
    print("=" * 60)
    print("[*] Processing 02_uci_sms (UCI SMS English Benchmark)...")
    path = RAW_DIR / "02_uci_sms" / "uci_sms_spam_english.csv"
    df = pd.read_csv(path)
    initial_count = len(df)
    
    df["text_clean"] = df["text"].apply(clean_text)
    df["label_num"] = df["label"].apply(standardize_label)
    
    df = df[df["text_clean"].apply(is_valid_message)].copy()
    valid_count = len(df)
    
    df = df.drop_duplicates(subset=["text_clean"]).copy()
    dedup_count = len(df)
    
    train_idx, test_idx = train_test_split(
        df.index, test_size=0.20, random_state=42, stratify=df["label_num"]
    )
    df["split"] = "train"
    df.loc[test_idx, "split"] = "test"
    
    out_path = OUTPUT_DIR / "cleaned_uci_sms.csv"
    df[["id", "text_clean", "label_num", "language", "source", "split"]].to_csv(
        out_path, index=False, encoding="utf-8"
    )
    
    stats = {
        "dataset": "UCI SMS",
        "initial_rows": initial_count,
        "valid_rows": valid_count,
        "dedup_rows": dedup_count,
        "spam_count": int(df["label_num"].sum()),
        "ham_count": int((df["label_num"] == 0).sum()),
        "train_rows": int((df["split"] == "train").sum()),
        "test_rows": int((df["split"] == "test").sum()),
        "languages": df["language"].value_counts().to_dict()
    }
    print(f"    Cleaned: {dedup_count} rows (Spam: {stats['spam_count']}, Ham: {stats['ham_count']})")
    print(f"    Train: {stats['train_rows']}, Test: {stats['test_rows']}")
    print(f"    Saved -> {out_path}")
    return df, stats

def process_multilingual_reference():
    print("=" * 60)
    print("[*] Processing 03_multilingual_reference (Multilingual Reference)...")
    path = RAW_DIR / "03_multilingual_reference" / "data-en-hi-de-fr.csv"
    df = pd.read_csv(path)
    initial_count = len(df)
    
    df["text_en_clean"] = df["text"].apply(clean_text)
    df["text_hi_clean"] = df["text_hi"].apply(clean_text)
    df["label_num"] = df["labels"].apply(standardize_label)
    
    # Drop rows where english or hindi text is invalid
    df = df[df["text_en_clean"].apply(is_valid_message) & df["text_hi_clean"].apply(is_valid_message)].copy()
    valid_count = len(df)
    
    # Deduplicate on Hindi clean text to avoid duplicate translations
    df_hi = df.drop_duplicates(subset=["text_hi_clean"]).copy()
    dedup_count = len(df_hi)
    
    train_idx, test_idx = train_test_split(
        df_hi.index, test_size=0.20, random_state=42, stratify=df_hi["label_num"]
    )
    df_hi["split"] = "train"
    df_hi.loc[test_idx, "split"] = "test"
    
    out_path_hi = OUTPUT_DIR / "cleaned_multilingual_hi.csv"
    df_hi[["text_hi_clean", "label_num", "text_en_clean", "split"]].to_csv(
        out_path_hi, index=False, encoding="utf-8"
    )
    
    stats = {
        "dataset": "Multilingual Reference (Hindi)",
        "initial_rows": initial_count,
        "valid_rows": valid_count,
        "dedup_rows": dedup_count,
        "spam_count": int(df_hi["label_num"].sum()),
        "ham_count": int((df_hi["label_num"] == 0).sum()),
        "train_rows": int((df_hi["split"] == "train").sum()),
        "test_rows": int((df_hi["split"] == "test").sum())
    }
    print(f"    Cleaned Hindi: {dedup_count} rows (Spam: {stats['spam_count']}, Ham: {stats['ham_count']})")
    print(f"    Train: {stats['train_rows']}, Test: {stats['test_rows']}")
    print(f"    Saved -> {out_path_hi}")
    return df_hi, stats

def create_master_combined_corpus(df_indian, df_uci, df_multi_hi):
    print("=" * 60)
    print("[*] Creating Master Combined Corpus (Deduplicated across datasets)...")
    
    combined_rows = []
    seen_texts = set()
    
    # 1. Add Indian SMS (Highest priority for local context)
    for _, row in df_indian.iterrows():
        t = row["text_clean"]
        if t not in seen_texts:
            seen_texts.add(t)
            combined_rows.append({
                "text": t,
                "label": int(row["label_num"]),
                "language": row["language"],
                "origin_corpus": "Indian_SMS",
                "split": row["split"]
            })
            
    # 2. Add UCI English SMS (Only non-overlapping texts)
    uci_added = 0
    for _, row in df_uci.iterrows():
        t = row["text_clean"]
        if t not in seen_texts:
            seen_texts.add(t)
            combined_rows.append({
                "text": t,
                "label": int(row["label_num"]),
                "language": "en",
                "origin_corpus": "UCI_English",
                "split": row["split"]
            })
            uci_added += 1
            
    # 3. Add Multilingual Reference Hindi
    hi_added = 0
    for _, row in df_multi_hi.iterrows():
        t = row["text_hi_clean"]
        if t not in seen_texts:
            seen_texts.add(t)
            combined_rows.append({
                "text": t,
                "label": int(row["label_num"]),
                "language": "hi_translated",
                "origin_corpus": "Multilingual_Hindi",
                "split": row["split"]
            })
            hi_added += 1
            
    master_df = pd.DataFrame(combined_rows)
    out_master = OUTPUT_DIR / "cleaned_master_corpus.csv"
    master_df.to_csv(out_master, index=False, encoding="utf-8")
    
    stats = {
        "dataset": "Master Combined Corpus",
        "total_rows": len(master_df),
        "spam_count": int(master_df["label"].sum()),
        "ham_count": int((master_df["label"] == 0).sum()),
        "train_rows": int((master_df["split"] == "train").sum()),
        "test_rows": int((master_df["split"] == "test").sum()),
        "corpus_breakdown": master_df["origin_corpus"].value_counts().to_dict(),
        "language_breakdown": master_df["language"].value_counts().to_dict()
    }
    print(f"    Master Corpus: {len(master_df)} records (Spam: {stats['spam_count']}, Ham: {stats['ham_count']})")
    print(f"    Origins: {stats['corpus_breakdown']}")
    print(f"    Languages: {stats['language_breakdown']}")
    print(f"    Saved -> {out_master}")
    return master_df, stats

def main():
    print("🚀 JAN SURAKSHA DATASET CLEANING & PREPROCESSING")
    df_indian, s1 = process_indian_sms()
    df_uci, s2 = process_uci_sms()
    df_multi_hi, s3 = process_multilingual_reference()
    master_df, s_master = create_master_combined_corpus(df_indian, df_uci, df_multi_hi)
    
    all_stats = {
        "indian_sms": s1,
        "uci_sms": s2,
        "multilingual_hi": s3,
        "master_corpus": s_master
    }
    
    stats_path = OUTPUT_DIR / "cleaning_summary.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(all_stats, f, indent=2)
    print(f"\n[+] Full cleaning summary saved to {stats_path}")

if __name__ == "__main__":
    main()
