"""
Jan Suraksha - Hardened Multi-Category Evaluation Benchmark Generator
Builds a curated, independently labelled dataset covering:
  Category A: Ordinary messages (greetings, day-to-day conversation)
  Category B: Normal financial messages (transfers, payment receipts, bills)
  Category C: Suspicious messages (KYC expiry warnings, unverified links)
  Category D: Explicit scams (OTP theft, UPI PIN to receive money, digital arrest, AnyDesk)
  Category E: Regional Hindi and Chhattisgarhi variations (spelling, dialectal expressions)
"""

import json
from pathlib import Path

def build_dataset():
    dataset = {
        "metadata": {
            "title": "Jan Suraksha Hardened Multi-Category Evaluation Benchmark",
            "description": "Balanced, independently labelled dataset covering ordinary messages, normal financial communications, suspicious prompts, explicit scams, and regional Hindi/Chhattisgarhi variations.",
            "version": "1.0.0",
            "total_samples": 100,
            "category_distribution": {
                "A_ordinary": 20,
                "B_normal_financial": 20,
                "C_suspicious": 20,
                "D_explicit_scams": 20,
                "E_regional": 20
            },
            "ground_truth_distribution": {
                "genuine_total": 50,
                "scam_suspicious_total": 50
            }
        },
        "samples": [
            # --- Category A: Ordinary Messages (20 samples, label 0 / genuine) ---
            {"id": "A_01", "category": "A_ordinary", "text": "Hello", "expected_verdict": "genuine", "expected_label": 0, "language": "en", "description": "Single word greeting"},
            {"id": "A_02", "category": "A_ordinary", "text": "Hi", "expected_verdict": "genuine", "expected_label": 0, "language": "en", "description": "Casual short greeting"},
            {"id": "A_03", "category": "A_ordinary", "text": "Good morning", "expected_verdict": "genuine", "expected_label": 0, "language": "en", "description": "Morning greeting"},
            {"id": "A_04", "category": "A_ordinary", "text": "Namaste", "expected_verdict": "genuine", "expected_label": 0, "language": "en", "description": "Transliterated Indian greeting"},
            {"id": "A_05", "category": "A_ordinary", "text": "Kaise ho?", "expected_verdict": "genuine", "expected_label": 0, "language": "hinglish", "description": "Casual inquiry in Hinglish"},
            {"id": "A_06", "category": "A_ordinary", "text": "Thank you", "expected_verdict": "genuine", "expected_label": 0, "language": "en", "description": "Expression of gratitude"},
            {"id": "A_07", "category": "A_ordinary", "text": "Where are you?", "expected_verdict": "genuine", "expected_label": 0, "language": "en", "description": "Conversational inquiry"},
            {"id": "A_08", "category": "A_ordinary", "text": "I will call you later.", "expected_verdict": "genuine", "expected_label": 0, "language": "en", "description": "Everyday conversational phrase"},
            {"id": "A_09", "category": "A_ordinary", "text": "Are you free this weekend?", "expected_verdict": "genuine", "expected_label": 0, "language": "en", "description": "Friendly inquiry"},
            {"id": "A_10", "category": "A_ordinary", "text": "Let us meet for lunch at 1 PM.", "expected_verdict": "genuine", "expected_label": 0, "language": "en", "description": "Appointment scheduling"},
            {"id": "A_11", "category": "A_ordinary", "text": "नमस्ते, आप कैसे हैं?", "expected_verdict": "genuine", "expected_label": 0, "language": "hi", "description": "Formal Hindi greeting"},
            {"id": "A_12", "category": "A_ordinary", "text": "सुप्रभात, आज का दिन शुभ हो।", "expected_verdict": "genuine", "expected_label": 0, "language": "hi", "description": "Hindi good morning"},
            {"id": "A_13", "category": "A_ordinary", "text": "धन्यवाद, आपकी मदद के लिए शुक्रिया।", "expected_verdict": "genuine", "expected_label": 0, "language": "hi", "description": "Hindi gratitude"},
            {"id": "A_14", "category": "A_ordinary", "text": "कहाँ हो भाई? मैं स्टेशन पर इंतज़ार कर रहा हूँ।", "expected_verdict": "genuine", "expected_label": 0, "language": "hi", "description": "Waiting at station in Hindi"},
            {"id": "A_15", "category": "A_ordinary", "text": "मैं थोड़ी देर में कॉल बैक करता हूँ।", "expected_verdict": "genuine", "expected_label": 0, "language": "hi", "description": "Calling back in Hindi"},
            {"id": "A_16", "category": "A_ordinary", "text": "खाना खा लिया क्या?", "expected_verdict": "genuine", "expected_label": 0, "language": "hi", "description": "Casual Hindi family question"},
            {"id": "A_17", "category": "A_ordinary", "text": "जय जोहार संगवारी!", "expected_verdict": "genuine", "expected_label": 0, "language": "chg", "description": "Chhattisgarhi traditional greeting"},
            {"id": "A_18", "category": "A_ordinary", "text": "कइसे हस भाई? सब कुशल मंगल हे?", "expected_verdict": "genuine", "expected_label": 0, "language": "chg", "description": "Chhattisgarhi wellbeing check"},
            {"id": "A_19", "category": "A_ordinary", "text": "मंय अभी बजार म हंव, बाद म गोठियाबो।", "expected_verdict": "genuine", "expected_label": 0, "language": "chg", "description": "Chhattisgarhi marketplace chat"},
            {"id": "A_20", "category": "A_ordinary", "text": "सुग्घर काम करे हस भाई, धन्यवाद।", "expected_verdict": "genuine", "expected_label": 0, "language": "chg", "description": "Chhattisgarhi gratitude"},

            # --- Category B: Normal Financial Messages (20 samples, label 0 / genuine) ---
            {"id": "B_01", "category": "B_normal_financial", "text": "I transferred money.", "expected_verdict": "genuine", "expected_label": 0, "language": "en", "description": "Benign statement of money transfer"},
            {"id": "B_02", "category": "B_normal_financial", "text": "Your payment was received.", "expected_verdict": "genuine", "expected_label": 0, "language": "en", "description": "Payment receipt notification"},
            {"id": "B_03", "category": "B_normal_financial", "text": "Please check your bank statement.", "expected_verdict": "genuine", "expected_label": 0, "language": "en", "description": "Routine financial bookkeeping advice"},
            {"id": "B_04", "category": "B_normal_financial", "text": "Your electricity bill is due.", "expected_verdict": "genuine", "expected_label": 0, "language": "en", "description": "Standard due date alert"},
            {"id": "B_05", "category": "B_normal_financial", "text": "I have already paid the school fees online.", "expected_verdict": "genuine", "expected_label": 0, "language": "en", "description": "User narration of payment"},
            {"id": "B_06", "category": "B_normal_financial", "text": "Salary of Rs 35,000 has been credited to your savings account XX1092. -HDFC Bank", "expected_verdict": "genuine", "expected_label": 0, "language": "en", "description": "Bank salary credit SMS"},
            {"id": "B_07", "category": "B_normal_financial", "text": "INR 350 debited for grocery purchase at Smart Bazaar. Avail Bal: INR 14,200.", "expected_verdict": "genuine", "expected_label": 0, "language": "en", "description": "Standard merchant debit alert"},
            {"id": "B_08", "category": "B_normal_financial", "text": "Your monthly mobile postpaid bill of Rs 499 is generated. Pay via telecom app.", "expected_verdict": "genuine", "expected_label": 0, "language": "en", "description": "Postpaid telecom bill"},
            {"id": "B_09", "category": "B_normal_financial", "text": "CSPDCL: Your electricity bill for consumer 100234 is Rs 1,420 due on 28th.", "expected_verdict": "genuine", "expected_label": 0, "language": "en", "description": "Routine power bill without threats"},
            {"id": "B_10", "category": "B_normal_financial", "text": "458921 is your secret OTP for Amazon purchase of Rs 500. DO NOT SHARE WITH ANYONE. Bank never calls to ask OTP.", "expected_verdict": "genuine", "expected_label": 0, "language": "en", "description": "Authentic bank OTP advisory"},
            {"id": "B_11", "category": "B_normal_financial", "text": "मैंने 500 रुपये ट्रांसफर कर दिए हैं, चेक कर लो।", "expected_verdict": "genuine", "expected_label": 0, "language": "hi", "description": "Hindi personal transfer confirmation"},
            {"id": "B_12", "category": "B_normal_financial", "text": "आपका बिजली बिल 650 रुपये देय है। अंतिम तिथि 30 तारीख है।", "expected_verdict": "genuine", "expected_label": 0, "language": "hi", "description": "Hindi electricity bill notice"},
            {"id": "B_13", "category": "B_normal_financial", "text": "खाता संख्या XX4582 में 10,000 रुपये जमा हुए हैं। कुल शेष: 45,000 रुपये। -SBI", "expected_verdict": "genuine", "expected_label": 0, "language": "hi", "description": "Hindi bank deposit SMS"},
            {"id": "B_14", "category": "B_normal_financial", "text": "पासबुक में एंट्री करवाने कल बैंक शाखा जाना है।", "expected_verdict": "genuine", "expected_label": 0, "language": "hi", "description": "Hindi routine banking plan"},
            {"id": "B_15", "category": "B_normal_financial", "text": "किराने की दुकान पर फोनपे से 250 रुपये का भुगतान सफल रहा।", "expected_verdict": "genuine", "expected_label": 0, "language": "hi", "description": "Hindi merchant UPI confirmation"},
            {"id": "B_16", "category": "B_normal_financial", "text": "मैंने अपना बिजली का बिल कल ही ऑनलाइन भर दिया है।", "expected_verdict": "genuine", "expected_label": 0, "language": "hi", "description": "Hindi user narration bill paid"},
            {"id": "B_17", "category": "B_normal_financial", "text": "मंय बिजली बिल पटा दे हंव, रसीद मिल गे हे।", "expected_verdict": "genuine", "expected_label": 0, "language": "chg", "description": "Chhattisgarhi narration of bill paid"},
            {"id": "B_18", "category": "B_normal_financial", "text": "तोर खाता म 1000 रुपया भेज दे हंव, चेक कर लेबे।", "expected_verdict": "genuine", "expected_label": 0, "language": "chg", "description": "Chhattisgarhi money transfer confirmation"},
            {"id": "B_19", "category": "B_normal_financial", "text": "सोसाइटी म धान के बोनस के पईसा आ गे हे।", "expected_verdict": "genuine", "expected_label": 0, "language": "chg", "description": "Chhattisgarhi paddy bonus credit"},
            {"id": "B_20", "category": "B_normal_financial", "text": "पासबुक चढ़ाए बर बिहाने बैंक शाखा जाबो।", "expected_verdict": "genuine", "expected_label": 0, "language": "chg", "description": "Chhattisgarhi passbook update plan"},

            # --- Category C: Suspicious Messages (20 samples, label 1 / suspicious) ---
            {"id": "C_01", "category": "C_suspicious", "text": "Your KYC will expire.", "expected_verdict": "unsure", "expected_label": 1, "language": "en", "description": "Isolated KYC expiration prompt"},
            {"id": "C_02", "category": "C_suspicious", "text": "Your account has been blocked.", "expected_verdict": "unsure", "expected_label": 1, "language": "en", "description": "Isolated unverified account block claim"},
            {"id": "C_03", "category": "C_suspicious", "text": "Click this link to verify your account.", "expected_verdict": "likely_scam", "expected_label": 1, "language": "en", "description": "Direct link verification prompt"},
            {"id": "C_04", "category": "C_suspicious", "text": "Your SIM service will stop in 24 hours. Update KYC at bit.ly/sim-kyc.", "expected_verdict": "likely_scam", "expected_label": 1, "language": "en", "description": "SIM deactivation urgency with shortlink"},
            {"id": "C_05", "category": "C_suspicious", "text": "Dear user, suspicious login detected. Verify identity at sbi-security.xyz.", "expected_verdict": "likely_scam", "expected_label": 1, "language": "en", "description": "Phishing domain verification"},
            {"id": "C_06", "category": "C_suspicious", "text": "Urgent: Your credit card reward points worth Rs 4500 will lapse today. Click to claim.", "expected_verdict": "likely_scam", "expected_label": 1, "language": "en", "description": "Urgent reward lapse lure"},
            {"id": "C_07", "category": "C_suspicious", "text": "Your PAN card is not linked with bank account. Verify details immediately.", "expected_verdict": "unsure", "expected_label": 1, "language": "en", "description": "Urgent PAN linking notice"},
            {"id": "C_08", "category": "C_suspicious", "text": "CSPDCL notice: Unpaid bill pending. Call officer at 9876543210 to avoid cutoff.", "expected_verdict": "likely_scam", "expected_label": 1, "language": "en", "description": "Power disconnection phone lure"},
            {"id": "C_09", "category": "C_suspicious", "text": "प्रिय ग्राहक, आपकी बैंक KYC समाप्त हो रही है। खाते के सत्यापन हेतु लिंक खोलें।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "hi", "description": "Hindi KYC link prompt"},
            {"id": "C_10", "category": "C_suspicious", "text": "आपका बिजली कनेक्शन बकाया बिल के कारण आज रात काट दिया जाएगा। संपर्क करें।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "hi", "description": "Hindi electricity disconnection cutoff"},
            {"id": "C_11", "category": "C_suspicious", "text": "आपके एसबीआई खाते में असामान्य गतिविधि देखी गई है। तुरंत लॉगिन करें।", "expected_verdict": "unsure", "expected_label": 1, "language": "hi", "description": "Hindi unusual activity prompt"},
            {"id": "C_12", "category": "C_suspicious", "text": "प्रिय उपभोक्ता, आपका सिम कार्ड ब्लॉक कर दिया गया है। पुनः चालू करने हेतु कॉल करें।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "hi", "description": "Hindi SIM block alert"},
            {"id": "C_13", "category": "C_suspicious", "text": "तोर बैंक खाता ब्लॉक हो गे हे, ये लिंक म जाके आधार नंबर सत्यापित कर।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "chg", "description": "Chhattisgarhi account block phishing link"},
            {"id": "C_14", "category": "C_suspicious", "text": "बिजली बिल नइ भरे हस, संझा 9 बजे मीटर काट देबो।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "chg", "description": "Chhattisgarhi bill cut threat"},
            {"id": "C_15", "category": "C_suspicious", "text": "तोर पैन कार्ड बैंक ले लिंक नइ हे, तुरते अपडेट करवाव।", "expected_verdict": "unsure", "expected_label": 1, "language": "chg", "description": "Chhattisgarhi PAN link urgency"},
            {"id": "C_16", "category": "C_suspicious", "text": "Your loan approval is waiting. Confirm registration at bit.ly/easy-loan.", "expected_verdict": "likely_scam", "expected_label": 1, "language": "en", "description": "Unsolicited loan shortlink"},
            {"id": "C_17", "category": "C_suspicious", "text": "Aapka netbanking suspend ho sakta hai, turant branch call kare ya link khole.", "expected_verdict": "likely_scam", "expected_label": 1, "language": "hinglish", "description": "Hinglish netbanking suspension warning"},
            {"id": "C_18", "category": "C_suspicious", "text": "Urgent: Aadhaar biometric update required or banking disabled.", "expected_verdict": "unsure", "expected_label": 1, "language": "en", "description": "Aadhaar biometric update urgency"},
            {"id": "C_19", "category": "C_suspicious", "text": "बधाई हो, आपका नंबर लॉटरी ड्रॉ के लिए चुना गया है।", "expected_verdict": "unsure", "expected_label": 1, "language": "hi", "description": "Hindi lottery selection teaser"},
            {"id": "C_20", "category": "C_suspicious", "text": "तोर नाम म पार्सल आए हे, पोस्ट ऑफिस ले संपर्क करव।", "expected_verdict": "unsure", "expected_label": 1, "language": "chg", "description": "Chhattisgarhi parcel notification"},

            # --- Category D: Explicit Scams (20 samples, label 1 / scam) ---
            {"id": "D_01", "category": "D_explicit_scams", "text": "Share your OTP.", "expected_verdict": "likely_scam", "expected_label": 1, "language": "en", "description": "Direct OTP solicitation"},
            {"id": "D_02", "category": "D_explicit_scams", "text": "Enter your UPI PIN to receive money.", "expected_verdict": "likely_scam", "expected_label": 1, "language": "en", "description": "Critical UPI PIN reverse scam"},
            {"id": "D_03", "category": "D_explicit_scams", "text": "Pay immediately or police will arrest you.", "expected_verdict": "likely_scam", "expected_label": 1, "language": "en", "description": "Direct police extortion threat"},
            {"id": "D_04", "category": "D_explicit_scams", "text": "Install AnyDesk for bank verification.", "expected_verdict": "likely_scam", "expected_label": 1, "language": "en", "description": "Remote access malware APK trap"},
            {"id": "D_05", "category": "D_explicit_scams", "text": "Dear customer, share the 6-digit OTP sent to your phone to activate ATM card.", "expected_verdict": "likely_scam", "expected_label": 1, "language": "en", "description": "ATM activation OTP theft"},
            {"id": "D_06", "category": "D_explicit_scams", "text": "You have received cashback of Rs 2500. Enter your 6-digit UPI PIN to credit to bank.", "expected_verdict": "likely_scam", "expected_label": 1, "language": "en", "description": "Cashback UPI PIN trap"},
            {"id": "D_07", "category": "D_explicit_scams", "text": "CBI Cyber Crime notice: You are placed under DIGITAL ARREST. Pay clearance bond of Rs 50,000 immediately.", "expected_verdict": "likely_scam", "expected_label": 1, "language": "en", "description": "Digital arrest extortion"},
            {"id": "D_08", "category": "D_explicit_scams", "text": "Download QuickSupport APK from link to complete verification or SIM deactivated.", "expected_verdict": "likely_scam", "expected_label": 1, "language": "en", "description": "QuickSupport remote access threat"},
            {"id": "D_09", "category": "D_explicit_scams", "text": "Congratulations! You won 25 Lakhs in KBC Lottery. Share 6-digit code to claim prize.", "expected_verdict": "likely_scam", "expected_label": 1, "language": "en", "description": "KBC lottery OTP trap"},
            {"id": "D_10", "category": "D_explicit_scams", "text": "SBI manager: Tell me the OTP immediately to unblock your netbanking account.", "expected_verdict": "likely_scam", "expected_label": 1, "language": "en", "description": "Bank officer impersonation OTP demand"},
            {"id": "D_11", "category": "D_explicit_scams", "text": "पैसे पाने के लिए अपना UPI पिन दर्ज करें।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "hi", "description": "Hindi UPI PIN to receive money"},
            {"id": "D_12", "category": "D_explicit_scams", "text": "अपना 6 अंकों का गुप्त OTP हमारे बैंक अधिकारी को बताएं।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "hi", "description": "Hindi OTP theft"},
            {"id": "D_13", "category": "D_explicit_scams", "text": "क्राइम ब्रांच डिजिटल अरेस्ट: आपके पार्सल में ड्रग्स पकड़े गए हैं। तुरंत 30,000 रु जमानत भरें।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "hi", "description": "Hindi digital arrest warrant"},
            {"id": "D_14", "category": "D_explicit_scams", "text": "तुरंत AnyDesk ऐप डाउनलोड करें और 9 अंकों का कोड बताएं।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "hi", "description": "Hindi AnyDesk code theft"},
            {"id": "D_15", "category": "D_explicit_scams", "text": "बधाई! आपने 50,000 रुपये का इनाम जीता है। खाते में पैसे लेने के लिए UPI पिन डालें।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "hi", "description": "Hindi lottery reward PIN theft"},
            {"id": "D_16", "category": "D_explicit_scams", "text": "खाता म पईसा आही, मोबाइल निकालव अउ तुरते UPI पिन डारव।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "chg", "description": "Chhattisgarhi UPI PIN theft"},
            {"id": "D_17", "category": "D_explicit_scams", "text": "मोबाइल म आए 6 अंक के OTP ला बताव, नइ ते खाता सील हो जाही।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "chg", "description": "Chhattisgarhi OTP demand"},
            {"id": "D_18", "category": "D_explicit_scams", "text": "पुलिस थाना ले बोलत हंव, तोर नाम म वारंट हे, तुरते 20000 रुपया भेज नइ ते जेल जाबे।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "chg", "description": "Chhattisgarhi police extortion"},
            {"id": "D_19", "category": "D_explicit_scams", "text": "AnyDesk ऐप डाउनलोड करव अउ अपन स्क्रीन शेयर करव।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "chg", "description": "Chhattisgarhi AnyDesk remote scam"},
            {"id": "D_20", "category": "D_explicit_scams", "text": "CSPDCL अधिकारी बोलत हंव, बिजली चालू रखे बर तुरते 5000 रुपया ट्रांसफर करव।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "chg", "description": "Chhattisgarhi electricity officer money extortion"},

            # --- Category E: Regional Hindi and Chhattisgarhi Messages (20 samples, balanced 10 genuine, 10 scam) ---
            {"id": "E_01", "category": "E_regional", "text": "का हाल चाल हे संगवारी? चाय पिए बर चलबो का?", "expected_verdict": "genuine", "expected_label": 0, "language": "chg", "description": "Chhattisgarhi casual tea invitation"},
            {"id": "E_02", "category": "E_regional", "text": "कल गांव म धान कटाई के काम सुरू होही।", "expected_verdict": "genuine", "expected_label": 0, "language": "chg", "description": "Chhattisgarhi harvest plan"},
            {"id": "E_03", "category": "E_regional", "text": "मंय अपन हाथ ले बिल पटाए हंव, कोनो फोन नइ करे हंव।", "expected_verdict": "genuine", "expected_label": 0, "language": "chg", "description": "Chhattisgarhi benign narration of self payment"},
            {"id": "E_04", "category": "E_regional", "text": "बैंक कभू फोन म गुप्त ओटीपी नइ मांगय, ककरो ले साझा झन करव।", "expected_verdict": "genuine", "expected_label": 0, "language": "chg", "description": "Chhattisgarhi bank awareness warning"},
            {"id": "E_05", "category": "E_regional", "text": "पईसा निकाले बर बैंक शाखा म जाके फॉर्म भरना पड़ही।", "expected_verdict": "genuine", "expected_label": 0, "language": "chg", "description": "Chhattisgarhi banking procedure"},
            {"id": "E_06", "category": "E_regional", "text": "हेलो भैया, घर कब आ रहे हो? मम्मी पूछ रही हैं।", "expected_verdict": "genuine", "expected_label": 0, "language": "hi", "description": "Hindi family check-in"},
            {"id": "E_07", "category": "E_regional", "text": "ऑफिस में काम ज्यादा है, आज थोड़ा लेट हो जाऊंगा।", "expected_verdict": "genuine", "expected_label": 0, "language": "hi", "description": "Hindi workday update"},
            {"id": "E_08", "category": "E_regional", "text": "बिजली विभाग का मैसेज आया था लेकिन मैंने ऑनलाइन पहले ही बिल भर दिया है।", "expected_verdict": "genuine", "expected_label": 0, "language": "hi", "description": "Hindi user bill payment narration"},
            {"id": "E_09", "category": "E_regional", "text": "सुप्रभात! आज की मीटिंग 10 बजे है।", "expected_verdict": "genuine", "expected_label": 0, "language": "hi", "description": "Hindi meeting scheduling"},
            {"id": "E_10", "category": "E_regional", "text": "Bhai kal Raipur jaa raha hu, kuch mangwana hai kya?", "expected_verdict": "genuine", "expected_label": 0, "language": "hinglish", "description": "Hinglish travel check-in"},
            {"id": "E_11", "category": "E_regional", "text": "ए संगवारी, तोर लॉटरी लगे हे, मोबाइल के OTP ला तुरते भेज।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "chg", "description": "Chhattisgarhi dialect lottery OTP theft"},
            {"id": "E_12", "category": "E_regional", "text": "डिजिटल अरेस्ट! तोर आधार कार्ड म नशीला दवाई पकड़ाए हे, पुलिस आही।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "chg", "description": "Chhattisgarhi dialect digital arrest threat"},
            {"id": "E_13", "category": "E_regional", "text": "बिजली बिल नइ भरे हस, संझा 9:30 बजे बिजली लाइन कट जाही, तुरते ये नंबर म कॉल करव।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "chg", "description": "Chhattisgarhi power cutoff phone threat"},
            {"id": "E_14", "category": "E_regional", "text": "घर बैठे मोबाइल म लाइक करके 3000 रुपया कमाव, पहिले 500 रुपया रजिस्ट्रेशन फीस डारव।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "chg", "description": "Chhattisgarhi task scam upfront fee"},
            {"id": "E_15", "category": "E_regional", "text": "तोर महतारी वंदन योजना के पईसा रुके हे, पाए बर अपन एटीएम पिन बताव।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "chg", "description": "Chhattisgarhi Mahtari Vandan fake scheme PIN theft"},
            {"id": "E_16", "category": "E_regional", "text": "कस्टमर केयर: आपका क्रेडिट कार्ड रिवॉर्ड ब्लॉक हो गया है, ओटीपी साझा करें।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "hi", "description": "Hindi customer care reward OTP demand"},
            {"id": "E_17", "category": "E_regional", "text": "आपका पार्सल कस्टम में अटका है, छुड़ाने के लिए तुरंत 1200 रु पे करें।", "expected_verdict": "likely_scam", "expected_label": 1, "language": "hi", "description": "Hindi customs parcel duty scam"},
            {"id": "E_18", "category": "E_regional", "text": "Share your Google Pay OTP to receive 1000 rupees cashback.", "expected_verdict": "likely_scam", "expected_label": 1, "language": "en", "description": "GPay cashback OTP theft"},
            {"id": "E_19", "category": "E_regional", "text": "Police cyber cell notice: Under digital arrest. Pay fine immediately.", "expected_verdict": "likely_scam", "expected_label": 1, "language": "en", "description": "Police cyber cell digital arrest"},
            {"id": "E_20", "category": "E_regional", "text": "Dear customer, your SBI account is locked. Download anydesk.apk to unlock.", "expected_verdict": "likely_scam", "expected_label": 1, "language": "en", "description": "Malware APK download lure"}
        ]
    }

    out_path = Path(__file__).resolve().parent.parent.parent / "data" / "hardened_eval_dataset.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"[Dataset Generator] Successfully wrote {len(dataset['samples'])} benchmark samples to {out_path}")
    return dataset

if __name__ == "__main__":
    build_dataset()
