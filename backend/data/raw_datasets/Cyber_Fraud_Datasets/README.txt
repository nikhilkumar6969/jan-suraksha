CYBER FRAUD DETECTION & DIGITAL FINANCIAL LITERACY PLATFORM
Dataset starter pack

CONTENTS
1) 01_indian_sms/indian_sms_spam_real.csv
   3,822 rows; columns: id, text, label, language, source.
   Indian SMS sample with ham/spam labels. Language coverage is uneven; Hindi is a small subset.

2) 02_uci_sms/uci_sms_spam_english.csv
   5,171 rows; columns: id, text, label, language, source.
   English SMS Spam Collection benchmark with ham/spam labels.

3) 03_multilingual_reference/data-en-hi-de-fr.csv
   5,572 rows; columns: labels, text, text_hi, text_de, text_fr.
   Multilingual/translated version of SMS Spam Collection-style messages. Treat translated columns as reference/augmentation only until manually quality-checked; do not claim they are naturally occurring Hindi messages.

IMPORTANT TRAINING NOTES
- Keep the three datasets separate initially. Do not concatenate blindly: the multilingual file appears to be a translated version of the same underlying SMS corpus represented in the UCI dataset, so duplicates/data leakage are possible.
- Labels are ham/spam, not verified fraud/non-fraud. Spam includes non-fraudulent promotional messages; the data does not directly provide a reliable financial-fraud class.
- Create train/test splits by deduplicated message (and ideally source/campaign), not by randomly splitting duplicate copies across both sets.
- Report per-class precision, recall, F1, confusion matrix, and false-positive rate. Accuracy alone is insufficient.
- For Hindi and especially Chhattisgarhi support, collect and label genuine local-language examples with consent and privacy safeguards. Machine-translated text is not a substitute for real-world validation.
- These files cover SMS only. They do not provide recorded scam calls, call transcripts, QR images, regional incident counts, or lesson content.

Suggested first experiment:
1. Normalize text and inspect duplicates.
2. Train a TF-IDF + Logistic Regression baseline on the Indian dataset.
3. Benchmark separately on UCI English data.
4. Evaluate translated Hindi data separately as an exploratory test, not as proof of native Hindi performance.
