# Jan Suraksha — Dataset Cleaning & Model Training/Benchmarking Report
**Cyber Fraud Datasets: Data Normalization, Cross-Domain Generalization & Multi-Model Evaluation**

*Conducted by: Jan Suraksha Autonomous Engineering Team*  
*Timestamp: 2026-11-23*  
*Production Model: `Suraksha-Scam-LR-v1.0` (FeatureUnion Word 1-2 + Char 2-5 + Logistic Regression)*

---

## 1. Executive Summary

In response to the uploaded datasets (`data-en-hi-de-fr.csv` and `Cyber_Fraud_Datasets.zip`), a complete end-to-end machine learning pipeline was executed:
1. **Extraction & Inspection:** Unpacked raw datasets comprising Indian SMS spam, UCI English SMS spam, and Multilingual (English-Hindi-German-French) reference data.
2. **Text Cleaning & Normalization:** Applied HTML entity unescaping, zero-width character stripping, Unicode NFC normalization, whitespace collapsing, exact & semantic deduplication, and stratified 80/20 train/test splitting.
3. **Cross-Domain Benchmarking:** Conducted systematic experiments demonstrating the critical domain gap between Western English SMS datasets and real-world Indian SMS fraud.
4. **Multi-Model Evaluation:** Benchmarked Logistic Regression (Balanced), Calibrated LinearSVC, and Complement Naive Bayes across a 14,091-record deduplicated master corpus.
5. **Android Asset Integration:** Exported optimal model weights (1.37 MB) to `android/app/src/main/assets/scam_model_weights.json` for 100% on-device offline inference in `OfflineSmsClassifier.kt`.
6. **Full Regression Testing:** Verified 46/46 automated unit and dialect tests pass with 100%.

---

## 2. Dataset Cleaning & Preprocessing Methodology

The raw datasets presented several quality challenges:
- **HTML Entities:** 270+ records in UCI English and 309+ records in Multilingual data contained encoded HTML strings (`&lt;`, `&gt;`, `&amp;`, `&#123;`, etc.).
- **Zero-Width & Control Characters:** Invisible unicode characters (`\u200b`, `\u200c`, `\ufeff`) that distort tokenization.
- **Cross-Corpus Overlap:** As identified during profiling, `data-en-hi-de-fr.csv` is a translated variant of the UCI SMS corpus sharing 5,101 identical English texts. Blended training without deduplication would cause severe data leakage between training and testing splits.
- **Trivial/Noise Rows:** Single emoji (`👍`), punctuation (`???`), or single letters were present.

### Applied Cleaning Steps
```
[Raw Data] 
    --> HTML Entity Unescaping (html.unescape)
    --> Zero-Width & Control Char Removal ([\u200b\u200c\u200d\u200e\u200f\ufeff])
    --> Unicode NFC Normalization (unicodedata.normalize)
    --> Whitespace Collapsing (re.sub(r'\s+', ' '))
    --> Validity Filter (len >= 2, alphanumeric/Devanagari present)
    --> Intra-Dataset Deduplication
    --> Stratified 80/20 Split (stratified on label + language)
    --> Inter-Corpus Deduplication (Master Union)
```

### Dataset Statistics Table

| Dataset | Raw Rows | Cleaned Rows | Spam (1) | Ham (0) | Train Split (80%) | Test Split (20%) | Languages |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **01 Indian SMS Real** | 3,822 | **3,805** | 963 | 2,842 | 3,044 | 761 | English (3,479), Telugu (274), Hindi (52) |
| **02 UCI SMS English** | 5,171 | **5,158** | 642 | 4,516 | 4,126 | 1,032 | English (5,158) |
| **03 Multilingual Hindi Reference** | 5,572 | **5,130** | 630 | 4,500 | 4,104 | 1,026 | Hindi Translated (5,130) |
| **Master Combined Corpus** | 14,565 | **14,091** | **2,235** | **11,856** | **11,272** | **2,819** | EN (8,637), HI Trans (5,128), TE (274), HI (52) |

*All cleaned files exported to `backend/data/cleaned_datasets/`.*

---

## 3. Systematic Experimental Results

### Experiment 1: Indian SMS Dataset (In-Domain & Cross-Domain on UCI)
- **Training Set:** 3,044 Indian SMS records.
- **Evaluations:**
  - **In-Domain (Indian Test, 761 samples):**
    - **Accuracy:** 95.27%
    - **Spam:** Precision 87.86% | Recall 94.27% | **F1: 90.95%**
    - **Ham:** Precision 98.02% | Recall 95.61% | **F1: 96.80%**
    - **False Positive Rate (FPR):** **4.39%**
    - **ROC-AUC:** **0.9913**
    - **Latency:** 0.235 ms/sample
    - **Confusion Matrix:** TN=544, FP=25, FN=11, TP=181
  - **Cross-Domain (UCI English Benchmark, 1,032 samples):**
    - Accuracy drops to 77.91%, F1-Spam drops to 34.86% (FP=161), demonstrating that Indian scam phrasing (UPI, YONO, recharge, subsidy, Mandi) differs significantly from UK/US prize/ringtone spam.

### Experiment 2: UCI English SMS Dataset (In-Domain & Cross-Domain on Indian SMS)
- **Training Set:** 4,126 UCI English records.
- **Evaluations:**
  - **In-Domain (UCI Test, 1,032 samples):**
    - **Accuracy:** **99.32%**
    - **Spam:** Precision 100.00% | Recall 94.53% | **F1: 97.19%**
    - **Ham:** Precision 99.23% | Recall 100.00% | **F1: 99.61%**
    - **False Positive Rate (FPR):** **0.00%**
    - **ROC-AUC:** **0.9990**
    - **Confusion Matrix:** TN=904, FP=0, FN=7, TP=121
  - **Cross-Domain (Indian SMS Benchmark, 761 samples):**
    - **Severe Performance Collapse:** Accuracy plummets to **43.10%**, with False Positive Rate exploding to **63.97%** (FP=364!).
    - *Empirical Proof:* Standard Western benchmark models completely fail when deployed in an Indian telecom environment. Local Indian SMS training is strictly mandatory.

### Experiment 3: Multilingual Reference (Hindi Translation)
- **Training Set:** 4,104 translated Hindi records.
- **Test Set:** 1,026 translated Hindi records.
- **Results:**
  - **Accuracy:** **96.69%**
  - **Spam:** Precision 88.98% | Recall 83.33% | **F1: 86.07%**
  - **Ham:** Precision 97.69% | Recall 98.56% | **F1: 98.12%**
  - **False Positive Rate:** **1.44%**
  - **ROC-AUC:** **0.9674**
  - **Confusion Matrix:** TN=887, FP=13, FN=21, TP=105

### Experiment 4: Multi-Model Architecture Comparison on Master Cleaned Corpus (14,091 records)
Evaluated three production classifier candidates on 2,819 held-out test samples:

| Model Architecture | Accuracy | Spam Precision | Spam Recall | Spam F1 | Ham F1 | FPR (Ham) | ROC-AUC | Inference Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression (Balanced)** | **96.95%** | 90.18% | **90.58%** | **90.38%** | **98.19%** | **1.85%** | **0.9857** | **0.159 ms** |
| **Calibrated LinearSVC (Sigmoid)** | **97.06%** | **91.92%** | 89.24% | **90.56%** | **98.26%** | **1.47%** | **0.9817** | 0.173 ms |
| **Complement Naive Bayes** | 92.52% | 71.64% | 87.22% | 78.67% | 95.46% | 6.49% | 0.9607 | 0.163 ms |

---

## 4. Model Selection & Android Offline Deployment

### Architecture Selection
While Calibrated LinearSVC achieved a marginally higher F1 (90.56% vs 90.38%), **Logistic Regression (Balanced)** was chosen as the primary production model because:
1. **Higher Scam Recall:** 90.58% vs 89.24% (critical in fraud prevention to minimize missed scams).
2. **Direct Android Mathematical Compatibility:** Its calibrated single logit formula:
   $$\text{logit} = \vec{w}_{\text{word}} \cdot \vec{x}_{\text{word}} + \vec{w}_{\text{char}} \cdot \vec{x}_{\text{char}} + b$$
   $$P(\text{spam}) = \frac{1}{1 + e^{-\text{logit}}}$$
   is directly and efficiently implemented in Kotlin (`OfflineSmsClassifier.kt`) with zero external C++/Java dependencies.

### Exported Artifacts
- **Joblib Model:** `backend/models/scam_model.joblib`
- **Android Model Weights:** `android/app/src/main/assets/scam_model_weights.json` (1.37 MB)
- **Model Metadata:** `android/app/src/main/assets/model_metadata.json`
- **Verification Vectors:** `android/app/src/main/assets/test_vectors.json`

---

## 5. Verification & Regression Testing

After retraining and updating model weights:
- **Test Suite Execution:** Ran `pytest tests/` across all 46 test cases.
- **Pass Rate:** **46 / 46 passed (100% pass rate)**.
  - `test_call_transcribe.py`: 5/5 passed
  - `test_chhattisgarhi_dataset.py`: 3/3 passed (100% recall on 42 rural scenarios, 0.0% FPR)
  - `test_detector.py`: 8/8 passed
  - `test_qr.py`: 4/4 passed
  - `test_realtime_call_guardian.py`: 22/22 passed
  - `test_reports.py`: 2/2 passed
  - `test_updates.py`: 2/2 passed
- **Asset Sync:** Ran `scripts/sync_assets_to_android.py` to ensure Android package assets remain 100% in sync.

---

## 6. Conclusion

The uploaded datasets have been fully cleaned, normalized, deduplicated, and benchmarked. The resulting model achieves **>96.9% accuracy**, an outstanding **>90% F1-score on spam/fraud**, an exceptionally low **<1.9% false positive rate on legitimate ham**, and sub-millisecond inference speeds (~0.16 ms), ready for on-device deployment across India and rural Chhattisgarh.
