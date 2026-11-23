"""
Test suite for XLM-RoBERTa Migration & Multilingual Detection.
Verifies model loading, inference, multilingual smoke tests, and offline mode.
"""
import pytest
from app.detect.classifier import classify_text, is_model_available
from app.detect.pipeline import run_detection_pipeline


def test_xlm_roberta_model_available():
    assert is_model_available() is True, "XLM-RoBERTa model files must exist in backend/models/xlm_roberta_spam"


def test_classify_text_empty():
    res = classify_text("")
    assert res["p_scam"] == 0.0
    assert res["p_genuine"] == 1.0
    assert res["model_name"] == "XLM-RoBERTa"


def test_multilingual_smoke_scams():
    # English scam
    res_en = run_detection_pipeline("Your bank account will be blocked. Update your KYC immediately.", user_lang="en")
    assert res_en["verdict"] == "likely_scam"
    assert res_en["model_name"] == "XLM-RoBERTa"
    assert res_en["ml_spam_probability"] > 0.5

    # Hindi scam
    res_hi = run_detection_pipeline("आपका बैंक खाता बंद हो जाएगा। तुरंत KYC अपडेट करें।", user_lang="hi")
    assert res_hi["verdict"] == "likely_scam"
    assert res_hi["model_name"] == "XLM-RoBERTa"
    assert res_hi["ml_spam_probability"] > 0.5

    # Hinglish scam
    res_hing = run_detection_pipeline("Aapka bank account block ho jayega. KYC update karne ke liye link par click karo.", user_lang="hi")
    assert res_hing["verdict"] == "likely_scam"
    assert res_hing["model_name"] == "XLM-RoBERTa"
    assert res_hing["ml_spam_probability"] > 0.5

    # Chhattisgarhi scam
    res_chg = run_detection_pipeline("तोर बैंक खाता बंद हो जाही। जल्दी KYC अपडेट कर।", user_lang="chg")
    assert res_chg["verdict"] == "likely_scam"
    assert res_chg["model_name"] == "XLM-RoBERTa"
    assert res_chg["ml_spam_probability"] > 0.5


def test_multilingual_smoke_genuine():
    # English genuine
    res_en = run_detection_pipeline("Your account was credited with Rs 500. Available balance is Rs 2500.", user_lang="en")
    assert res_en["verdict"] == "genuine"
    assert res_en["model_name"] == "XLM-RoBERTa"
    assert res_en["ml_spam_probability"] < 0.5

    # Hindi genuine
    res_hi = run_detection_pipeline("आपके खाते में 500 रुपये जमा हुए हैं।", user_lang="hi")
    assert res_hi["verdict"] == "genuine"
    assert res_hi["model_name"] == "XLM-RoBERTa"
    assert res_hi["ml_spam_probability"] < 0.5

    # Hinglish genuine
    res_hing = run_detection_pipeline("Aaj college ki class 10 baje hai, time par aa jana.", user_lang="hi")
    assert res_hing["verdict"] == "genuine"
    assert res_hing["model_name"] == "XLM-RoBERTa"
    assert res_hing["ml_spam_probability"] < 0.5

    # Chhattisgarhi genuine
    res_chg = run_detection_pipeline("आज गांव म मेला हे, सब झन शाम के आवव।", user_lang="chg")
    assert res_chg["verdict"] == "genuine"
    assert res_chg["model_name"] == "XLM-RoBERTa"
    assert res_chg["ml_spam_probability"] < 0.5
