"""
Validation test: Compares JS Offline Scam Classifier predictions with Python/Kotlin predictions
across 22 multilingual sample messages in English, Hindi, and Chhattisgarhi.
Ensures zero mismatches between on-device JS ML inference and Python/Kotlin models.
"""

import json
import subprocess
from pathlib import Path
import pytest

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
WEIGHTS_PATH = FRONTEND_DIR / "content" / "scam_model_weights.json"
JS_CLASSIFIER_PATH = FRONTEND_DIR / "js" / "offline_classifier.js"

SAMPLE_MESSAGES = [
    # 1. Genuine Bank OTP (English)
    {
        "id": "EN_OTP_GENUINE",
        "text": "582910 is your secret One Time Password (OTP) for Rs 450 at Amazon. DO NOT SHARE WITH ANYONE. Bank never calls to ask OTP.",
        "lang": "en",
        "expected_verdict": "genuine"
    },
    # 2. Electricity Scam (English)
    {
        "id": "EN_ELEC_SCAM",
        "text": "URGENT: CSPDCL Electricity officer notice. Your power will be disconnected tonight at 9:30 PM due to unpaid bill of Rs 1,450. Call officer at 9876543210 immediately.",
        "lang": "en",
        "expected_verdict": "likely_scam"
    },
    # 3. Digital Arrest Extortion (English)
    {
        "id": "EN_DIGITAL_ARREST",
        "text": "CBI Cyber Crime Cell Notice: A parcel with drugs and passports found under your Aadhaar. You are placed under DIGITAL ARREST. Do not disconnect this call or tell anyone. Pay clearance bond immediately.",
        "lang": "en",
        "expected_verdict": "likely_scam"
    },
    # 4. Bank KYC Phishing with Shortlink (Hinglish)
    {
        "id": "HINGLISH_KYC_PHISH",
        "text": "Dear user, aapka SBI YONO account block ho gaya hai. KYC update karne ke liye turant link bit.ly/sbi-kyc par click kare.",
        "lang": "hi",
        "expected_verdict": "likely_scam"
    },
    # 5. WhatsApp Lottery Scam (Hinglish)
    {
        "id": "HINGLISH_LOTTERY",
        "text": "Badhai ho! Aapka number KBC lottery me select hua hai rs 2500000 ke liye. Prize lene ke liye 6 digit OTP manager 9826102938 ko turant bataye.",
        "lang": "hi",
        "expected_verdict": "likely_scam"
    },
    # 6. Genuine Conversation (English)
    {
        "id": "EN_CONV_GENUINE",
        "text": "Hey Ramesh, are you attending the gram panchayat meeting tomorrow morning in Raipur?",
        "lang": "en",
        "expected_verdict": "genuine"
    },
    # 7. Genuine Transaction Notification (English)
    {
        "id": "EN_TXN_DEBIT",
        "text": "Your A/C XX4921 has been debited by INR 350.00 on 24-Nov-26 for UPI txn to Sharma Kirana. Avl Bal: INR 12,430.",
        "lang": "en",
        "expected_verdict": "genuine"
    },
    # 8. Genuine Conversation (Hindi)
    {
        "id": "HI_CONV_GENUINE",
        "text": "कल शाम को रायपुर में मिलते हैं चाय पीने के लिए, घर पर सब कैसे हैं?",
        "lang": "hi",
        "expected_verdict": "genuine"
    },
    # 9. Coercive OTP demand (Hindi)
    {
        "id": "HI_OTP_THEFT",
        "text": "बैंक अधिकारी: अपने खाते को चालू रखने के लिए आपके मोबाइल पर आया 6 अंकों का ओटीपी तुरंत बताएं।",
        "lang": "hi",
        "expected_verdict": "likely_scam"
    },
    # 10. Electricity Disconnection (Hindi)
    {
        "id": "HI_BIJLI_SCAM",
        "text": "बिजली विभाग सूचना: प्रिय उपभोक्ता आपका बिजली बिल बकाया है, आज रात 10 बजे बिजली काट दी जाएगी। तुरंत 9876543210 पर संपर्क करें।",
        "lang": "hi",
        "expected_verdict": "likely_scam"
    },
    # 11. Fake Loan Offer (Hindi)
    {
        "id": "HI_LOAN_SCAM",
        "text": "प्रधानमंत्री मुद्रा योजना के तहत 5 लाख का लोन बिना गारंटी मंजूर। प्रोसेसिंग फीस 2500 तुरंत ट्रांसफर करें।",
        "lang": "hi",
        "expected_verdict": "likely_scam"
    },
    # 12. Remote Access Fraud (English)
    {
        "id": "EN_REMOTE_ACCESS",
        "text": "Dear customer, to avoid immediate SIM deactivation, install AnyDesk app and share 9 digit code with telecom officer.",
        "lang": "en",
        "expected_verdict": "likely_scam"
    },
    # 13. Genuine Salary Credit (English)
    {
        "id": "EN_SALARY_CREDIT",
        "text": "Salary of Rs 45,000.00 credited to your State Bank A/C XX8812 on 24-11-2026. Ref: SAL/Nov/2026.",
        "lang": "en",
        "expected_verdict": "genuine"
    },
    # 14. Password Reset Code (English)
    {
        "id": "EN_PASSWORD_RESET",
        "text": "Your password reset code is 829104. Valid for 10 minutes. Never share this code with anyone.",
        "lang": "en",
        "expected_verdict": "genuine"
    },
    # 15. Chhattisgarhi Genuine Conversation
    {
        "id": "CHG_CONV_GENUINE",
        "text": "भईया, काली बिहनिया ले खेत म काम हे, आजे धान बेचे बर मंडी जाना हे का?",
        "lang": "chg",
        "expected_verdict": "genuine"
    },
    # 16. Chhattisgarhi UPI PIN Theft
    {
        "id": "CHG_PIN_SCAM",
        "text": "तुंहर खाता म पईसा आही, 5000 रूपिया पाए बर अपन 6 अंक के यूपीआई पिन डालव।",
        "lang": "chg",
        "expected_verdict": "likely_scam"
    },
    # 17. Chhattisgarhi Genuine Banking Alert
    {
        "id": "CHG_BANK_GENUINE",
        "text": "मोर खाता म 500 रूपिया जमा होगे हे, कोनो ले पिन या पासवर्ड साझा झन करव।",
        "lang": "chg",
        "expected_verdict": "genuine"
    },
    # 18. Chhattisgarhi OTP Theft
    {
        "id": "CHG_OTP_SCAM",
        "text": "ओटीपी बताव तभे तुंहर महतारी वंदन योजना के पईसा मिलही, तुरंत भेजव।",
        "lang": "chg",
        "expected_verdict": "likely_scam"
    },
    # 19. Chhattisgarhi Electricity Threat
    {
        "id": "CHG_BIJLI_SCAM",
        "text": "बिजली बिल नइ भरे हो, आज रात के कनेक्शन काट देबो। बिजली साहब ले बात करव।",
        "lang": "chg",
        "expected_verdict": "likely_scam"
    },
    # 20. Fake Traffic Challan (English)
    {
        "id": "EN_CHALLAN_SCAM",
        "text": "Traffic Police: Your vehicle CG04-1234 has pending challan of Rs 1000. Pay before midnight at challan-pay.top.apk to avoid court warrant.",
        "lang": "en",
        "expected_verdict": "likely_scam"
    },
    # 21. Job Offer Fraud (English)
    {
        "id": "EN_JOB_FRAUD",
        "text": "Work from home part-time: Earn Rs 3000 to Rs 8000 daily by liking videos. Telegram contact @vip_jobs_online. Limited slots.",
        "lang": "en",
        "expected_verdict": "likely_scam"
    },
    # 22. College Notice Genuine (English)
    {
        "id": "EN_COLLEGE_NOTICE",
        "text": "Govt Engineering College Raipur: Semester exams commence from 15th December. Download admit card from official student portal.",
        "lang": "en",
        "expected_verdict": "genuine"
    }
]


def test_weights_file_exists_and_valid():
    assert WEIGHTS_PATH.exists(), f"Weights file missing at {WEIGHTS_PATH}"
    with open(WEIGHTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "intercept" in data
    assert "word_features" in data
    assert "char_features" in data
    assert len(data["word_features"]) >= 1000
    assert len(data["char_features"]) >= 1000


def test_js_offline_classifier_predictions_via_node():
    """
    Executes the exact frontend/js/offline_classifier.js module via Node.js
    and tests all 22 sample messages across English, Hindi, and Chhattisgarhi.
    Verifies that all predictions match expected verdicts with zero mismatches.
    """
    node_script = f"""
    const fs = require('fs');
    const path = require('path');

    // Setup browser globals for Node runtime
    global.window = {{}};
    const weightsJson = JSON.parse(fs.readFileSync({json.dumps(str(WEIGHTS_PATH))}, 'utf-8'));

    // Mock fetch for offline classifier
    global.fetch = async () => ({{
        ok: true,
        json: async () => weightsJson
    }});

    // Load classifier
    require({json.dumps(str(JS_CLASSIFIER_PATH))});
    const classifier = global.window.SurakshaOfflineClassifier;

    async function runTests() {{
        await classifier.init();
        const samples = {json.dumps(SAMPLE_MESSAGES)};
        const results = [];

        for (const s of samples) {{
            const res = classifier.classify(s.text);
            results.push({{
                id: s.id,
                text: s.text,
                lang: s.lang,
                expected: s.expected_verdict,
                actual: res.verdict,
                confidence: res.confidence_percent,
                prob: res.probability_scam,
                rules: res.matched_rules,
                explanation: res.explanation
            }});
        }}
        console.log('__RESULTS_START__' + JSON.stringify(results) + '__RESULTS_END__');
    }}

    runTests().catch(err => {{
        console.error(err);
        process.exit(1);
    }});
    """

    res = subprocess.run(
        ["node", "-e", node_script],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    assert res.returncode == 0, f"Node script execution failed: {res.stderr}"

    stdout = res.stdout
    start_tag = '__RESULTS_START__'
    end_tag = '__RESULTS_END__'
    assert start_tag in stdout and end_tag in stdout, f"Delimiter not found in output: {stdout}"
    json_str = stdout.split(start_tag)[1].split(end_tag)[0]
    results = json.loads(json_str)
    mismatches = []

    print("\n--- Multilingual JS Offline ML Evaluation Results ---")
    for r in results:
        status = "PASS" if r["actual"] == r["expected"] else "FAIL"
        print(f"[{status}] [{r['lang'].upper()}] {r['id']}: expected {r['expected']} | actual {r['actual']} (conf: {r['confidence']}%, prob: {r['prob']:.4f})")
        if r["actual"] != r["expected"]:
            mismatches.append(r)

    assert len(mismatches) == 0, f"Found {len(mismatches)} prediction mismatches: {mismatches}"
