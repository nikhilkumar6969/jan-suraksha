"""
Scam Call Analyzer for Suraksha
Integrates real-time scam engine, conversation stage tracking, and unified pipeline.
Supports multi-lingual localized script metadata in Hindi, Chhattisgarhi, and English.
"""

from typing import Dict, Any, Optional
from app.detect.pipeline import run_detection_pipeline
from app.detect.scam_engine import detect_scam_in_transcript
from app.calls.conversation_tracker import track_conversation_step, reset_tracker

CALL_SCRIPTS = {
    "digital_arrest": {
        "hi": {
            "title": "पुलिस / सीबीआई डिजिटल अरेस्ट जबरन वसूली",
            "danger_banner": "🚨 गंभीर खतरा: कॉलर पुलिस/सीबीआई बनकर गिरफ्तारी का डर दिखाकर पैसे ऐंठने का प्रयास कर रहा है। तुरंत फोन काटें!",
            "action_advice": "कॉल पर बिल्कुल न रहें। असली पुलिस कभी 'डिजिटल अरेस्ट' नहीं करती और न ही ऑनलाइन जमानत राशि मांगती है। 1930 डायल करें।"
        },
        "chg": {
            "title": "पुलिस / सीबीआई डिजिटल अरेस्ट पईसा ऐंठे के कॉल",
            "danger_banner": "🚨 भारी खतरा: फोन करने वाला पुलिस बनके डरावा देत हे अउ पईसा मांगत हे। तुरते फोन ल काटव!",
            "action_advice": "फोन म झन रहव। कानून म 'डिजिटल अरेस्ट' नइ होवय। असली पुलिस कभू फोन म जमानत नइ मांगय। तुरते 1930 म फोन लगावव।"
        },
        "en": {
            "title": "Police / CBI Digital Arrest Extortion Call",
            "danger_banner": "🚨 CRITICAL THREAT: The caller is impersonating Law Enforcement to extort money. Hang up immediately!",
            "action_advice": "Do NOT stay on the call. Real police NEVER conduct digital arrests or demand online bond fees. Call 1930 immediately."
        }
    },
    "fake_kyc": {
        "hi": {
            "title": "फर्जी बैंक अधिकारी / खाता व बिजली बंद की धमकी",
            "danger_banner": "⚠️ ठगी का अलर्ट: कॉलर बैंक अधिकारी बनकर आपका खाता या डेबिट कार्ड बंद करने की धमकी दे रहा है।",
            "action_advice": "किसी को भी अपना OTP न बताएं और न ही AnyDesk या QuickSupport ऐप डाउनलोड करें। सीधे अपनी बैंक शाखा जाएं।"
        },
        "chg": {
            "title": "फर्जी बैंक अधिकारी / खाता अउ बिजली बंद करे के धमकी",
            "danger_banner": "⚠️ ठगी के अलर्ट: तोर खाता या बिजली काटे के डर दिखा के ठगे के कोसिस हे।",
            "action_advice": "ककरो ले अपन OTP झन बतावव अउ कोनो अनजान ऐप डाउनलोड झन करव। सीधा अपन बैंक शाखा जाके पूछव।"
        },
        "en": {
            "title": "Fake Bank Officer / KYC Suspension Call",
            "danger_banner": "⚠️ SCAM ALERT: Caller is pretending to be a bank official to steal your account credentials.",
            "action_advice": "Never share OTP or install remote-access apps (AnyDesk/QuickSupport). Visit your bank branch directly."
        }
    },
    "customs_courier": {
        "hi": {
            "title": "फर्जी कस्टम्स / पार्सल ड्रग्स घोटाला",
            "danger_banner": "📦 ठगी का अलर्ट: कॉलर आपके नाम पर अवैध पार्सल मिलने का दावा कर कस्टम शुल्क मांग रहा है।",
            "action_advice": "किसी भी तरह का टैक्स या क्लीयरेंस शुल्क न दें। यदि आपने विदेश से पार्सल नहीं भेजा है तो कॉलर को ब्लॉक करें।"
        },
        "chg": {
            "title": "फर्जी कस्टम्स / पार्सल म ड्रग्स के धोखा",
            "danger_banner": "📦 ठगी के अलर्ट: तोर पार्सल म नशीली दवा मिले के झूठा दावा करके पईसा मांगे जात हे।",
            "action_advice": "कोनो टैक्स या क्लीयरेंस फीस झन देहू। कॉलर ल सीधा ब्लॉक करव अउ 1930 म रिपोर्ट करव।"
        },
        "en": {
            "title": "Fake Customs / International Courier Parcel Call",
            "danger_banner": "📦 SCAM ALERT: Caller claims illegal contraband or luxury parcel to demand customs duty.",
            "action_advice": "Do not pay any clearance fees. If you did not ship an international parcel, ignore and report the caller."
        }
    },
    "upi_pin_fraud": {
        "hi": {
            "title": "UPI PIN चोरी का अत्यंत गंभीर खतरा",
            "danger_banner": "🛑 अत्यंत गंभीर खतरा: कॉलर कैशबैक या रिफंड का झांसा देकर आपका गुप्त UPI PIN चुराने का प्रयास कर रहा है।",
            "action_advice": "याद रखें, पैसे प्राप्त करने के लिए कभी UPI PIN दर्ज नहीं करना पड़ता। कॉल तुरंत काटें और 1930 पर शिकायत करें।"
        },
        "chg": {
            "title": "UPI पिन चुराए के भारी खतरा",
            "danger_banner": "🛑 भारी खतरा: कॉलर पईसा मिले के लालच देके तोर गुप्त UPI पिन मांगे के चाल चलत हे।",
            "action_advice": "सचेत रहव! पईसा पाए बर कभू UPI पिन नइ डारे लगत। कॉल तुरते काटव अउ 1930 म शिकायत करव।"
        },
        "en": {
            "title": "Urgent UPI PIN Theft Fraud",
            "danger_banner": "🛑 CRITICAL HAZARD: Caller is trying to steal your UPI PIN under pretext of cashback/refund.",
            "action_advice": "Never enter or tell your UPI PIN to receive money. Disconnect immediately and call 1930."
        }
    },
    "utility_electricity": {
        "hi": {
            "title": "बिजली बिल / लाइन काटने की फर्जी धमकी",
            "danger_banner": "⚠️ बिजली ठगी का अलर्ट: कॉलर बिजली बिल बकाया होने का झांसा देकर तुरंत लाइन काटने की धमकी दे रहा है।",
            "action_advice": "कॉल पर दिए नंबर पर कभी पैसे न भेजें। CSPDCL के आधिकारिक ऐप या नजदीकी बिजली दफ्तर से जांच करें।"
        },
        "chg": {
            "title": "बिजली बिल / लाइन काटे के फर्जी धमकी",
            "danger_banner": "⚠️ बिजली ठगी के अलर्ट: कॉलर बिजली लाइन काटे के झूठा डर दिखावत हे।",
            "action_advice": "कोनो अनजान नंबर म पईसा झन पटावव। बिजली दफ्तर जाके पता करव।"
        },
        "en": {
            "title": "Electricity Disconnection Extortion Call",
            "danger_banner": "⚠️ UTILITY EXTORTION ALERT: Caller is threatening immediate power cutoff to extort urgent payment.",
            "action_advice": "Never transfer money to personal phone numbers given on call. Check bills strictly on the official CSPDCL portal."
        }
    },
    "lottery_subsidy": {
        "hi": {
            "title": "फर्जी लॉटरी / महतारी वंदन योजना धोखा",
            "danger_banner": "🎁 फर्जी योजना अलर्ट: कॉलर लॉटरी या सरकारी योजना के पैसे दिलाने के नाम पर रजिस्ट्रेशन शुल्क मांग रहा है।",
            "action_advice": "सरकारी योजनाएं कभी अग्रिम शुल्क नहीं मांगतीं। किसी भी खाते में शुल्क जमा न करें। 1930 पर रिपोर्ट करें।"
        },
        "chg": {
            "title": "फर्जी लॉटरी / महतारी वंदन योजना के धोखा",
            "danger_banner": "🎁 फर्जी योजना अलर्ट: योजना के पईसा दिलाए बर पहिले सत्यापन शुल्क मांगे जात हे।",
            "action_advice": "कोनो सरकारी योजना पाए बर पहिले पईसा झन देहू। 1930 म रिपोर्ट करव।"
        },
        "en": {
            "title": "Fake Lottery / Welfare Scheme Scam",
            "danger_banner": "🎁 LOTTERY / WELFARE FRAUD: Caller promises prize money or government subsidies in exchange for an upfront fee.",
            "action_advice": "Never pay registration or clearance fees to claim benefits. Verify with official government portals."
        }
    },
    "remote_access": {
        "hi": {
            "title": "AnyDesk / रिमोट स्क्रीन हैकिंग धोखा",
            "danger_banner": "📱 डिवाइस हैकिंग अलर्ट: कॉलर AnyDesk या अज्ञात APK डाउनलोड कराकर आपका फोन रिमोट कंट्रोल करने का प्रयास कर रहा है।",
            "action_advice": "कोई भी ऐप इंस्टॉल न करें और स्क्रीन शेयर की अनुमति न दें। कॉल तुरंत डिस्कनेक्ट करें।"
        },
        "chg": {
            "title": "AnyDesk / स्क्रीन हैकिंग के धोखा",
            "danger_banner": "📱 मोबाइल हैकिंग अलर्ट: कॉलर AnyDesk या अनजान ऐप डाउनलोड करवा के मोबाइल हैक करे के चाल चलत हे।",
            "action_advice": "कोनो अनजान ऐप डाउनलोड झन करव। फोन तुरते काटव।"
        },
        "en": {
            "title": "Remote Access / APK Screen Takeover",
            "danger_banner": "📱 DEVICE TAKEOVER ALERT: Caller is manipulating you into installing screen-sharing software (AnyDesk/APK) to hijack your phone.",
            "action_advice": "Never install remote control tools or grant permissions. Disconnect immediately."
        }
    },
    "otp_fraud": {
        "hi": {
            "title": "गोपनीय OTP मांग धोखाधड़ी",
            "danger_banner": "🛑 अत्यंत गंभीर खतरा: कॉलर वेरिफिकेशन या लॉटरी के नाम पर आपका गोपनीय 6-अंकीय OTP मांग रहा है।",
            "action_advice": "OTP कभी किसी के साथ साझा न करें। बैंक या पुलिस कभी फोन पर OTP नहीं मांगते। कॉल तुरंत काटें।"
        },
        "chg": {
            "title": "गुप्त OTP मांगे के भारी धोखा",
            "danger_banner": "🛑 भारी खतरा: कॉलर सत्यापन के नाम म तोर गुप्त OTP मांगे के चाल चलत हे।",
            "action_advice": "अपन OTP ककरो ले झन बतावव। बैंक या पुलिस कभू OTP नइ मांगय। फोन तुरते काटव।"
        },
        "en": {
            "title": "Confidential OTP Solicitation Fraud",
            "danger_banner": "🛑 CRITICAL HAZARD: Caller is demanding your 6-digit verification OTP under false pretenses.",
            "action_advice": "Never share your OTP with anyone. Official organizations never ask for OTPs over the phone. Hang up immediately."
        }
    },
    "cyber_reporting": {
        "hi": {
            "title": "राष्ट्रीय साइबर हेल्पलाइन 1930 सहायता",
            "danger_banner": "ℹ️ प्रामाणिक हेल्पलाइन: वित्तीय साइबर अपराध होने पर तुरंत 1930 पर कॉल करें या cybercrime.gov.in पर रिपोर्ट दर्ज करें।",
            "action_advice": "गोल्डन ऑवर (2 घंटे के भीतर) में 1930 पर कॉल करने से ठगी गई राशि को बैंक स्तर पर फ्रीज कराया जा सकता है।"
        },
        "chg": {
            "title": "राष्ट्रीय साइबर हेल्पलाइन 1930 मदद",
            "danger_banner": "ℹ️ असली हेल्पलाइन: पईसा के ठगी होए म तुरते 1930 म फोन लगावव या cybercrime.gov.in म शिकायत करव।",
            "action_advice": "2 घंटा के भीतर 1930 म फोन लगाए ले ठगी के पईसा फ्रीज हो सकत हे।"
        },
        "en": {
            "title": "National Cybercrime Helpline 1930 Assistance",
            "danger_banner": "ℹ️ Official Helpline: In case of financial cyber fraud, dial 1930 immediately or visit cybercrime.gov.in.",
            "action_advice": "Reporting within the golden hour (first 2 hours) enables rapid freezing of defrauded funds across banks."
        }
    },
    "telecom_sim_block": {
        "hi": {
            "title": "TRAI / दूरसंचार सिम डिस्कनेक्शन धमकी",
            "danger_banner": "⚠️ दूरसंचार ठगी अलर्ट: कॉलर TRAI या दूरसंचार विभाग का नाम लेकर 2 घंटे में सिम बंद करने की झूठी धमकी दे रहा है।",
            "action_advice": "कॉल तुरंत डिस्कनेक्ट करें। TRAI उपभोक्ताओं को सिम बंद करने के लिए कभी कॉल नहीं करता। DoT चक्षु पोर्टल (sancharsaathi.gov.in) पर रिपोर्ट करें।"
        },
        "chg": {
            "title": "दूरसंचार सिम बंद करे के फर्जी धमकी",
            "danger_banner": "⚠️ दूरसंचार ठगी अलर्ट: कॉलर ट्राई बनके 2 घंटा म सिम बंद करे के डर दिखावत हे।",
            "action_advice": "फोन ल तुरते काटव। ट्राई कभू उपभोक्ता मन ल फोन नइ करय। 1930 म शिकायत करव।"
        },
        "en": {
            "title": "TRAI / Telecom SIM Disconnection Threat",
            "danger_banner": "⚠️ TELECOM SCAM ALERT: Caller is impersonating TRAI/DoT threatening to block your SIM card in 2 hours.",
            "action_advice": "Hang up immediately. TRAI never calls citizens to threaten disconnection. Report via DoT Chakshu (sancharsaathi.gov.in) or call 1930."
        }
    },
    "job_task_fraud": {
        "hi": {
            "title": "पार्ट-टाइम जॉब व यूट्यूब वीडियो लाइक फ्रॉड",
            "danger_banner": "⚠️ जॉब टास्क ठगी अलर्ट: घर बैठे वीडियो लाइक करने या टेलीग्राम टास्क के नाम पर रजिस्ट्रेशन फीस ऐंठने का प्रयास।",
            "action_advice": "कॉल तुरंत काटें। नौकरी या टास्क के लिए कभी भी अग्रिम पैसे न दें। किसी भी अज्ञात टेलीग्राम ग्रुप में न जुड़ें।"
        },
        "chg": {
            "title": "पार्ट-टाइम काम अउ वीडियो लाइक धोखा",
            "danger_banner": "⚠️ टास्क ठगी अलर्ट: यूट्यूब वीडियो लाइक करके पईसा कमाए के लालच देके ठगे के चाल हे।",
            "action_advice": "फोन ल तुरते काटव। काम पाए बर पहिले पईसा झन देहू। 1930 म शिकायत करव।"
        },
        "en": {
            "title": "Part-Time Job & YouTube Like Scam",
            "danger_banner": "⚠️ TASK SCAM ALERT: Caller promises daily income for liking YouTube videos or completing Telegram tasks to extort upfront fees.",
            "action_advice": "Hang up immediately. Legitimate companies never charge registration fees for work. Never join unsolicited Telegram task groups."
        }
    },
    "credential_prompt_inquiry": {
        "hi": {
            "title": "गोपनीय बैंक क्रेडेंशियल सुरक्षा पूछताछ",
            "danger_banner": "🛡️ सुरक्षा नियम: आरबीआई के दिशानिर्देशानुसार बैंक, पुलिस या कोई भी अधिकारी कभी भी फोन पर पासवर्ड, कार्ड नंबर, CVV या OTP नहीं मांगते।",
            "action_advice": "किसी भी कॉलर को अपने बैंक खाते, कार्ड या ओटीपी की जानकारी कभी न दें। फोन तुरंत काट दें।"
        },
        "chg": {
            "title": "गोपनीय बैंक जानकारी सुरक्षा पड़ताल",
            "danger_banner": "🛡️ सुरक्षा नियम: बैंक या पुलिस कभू फोन म पासवर्ड, पिन या OTP नइ मांगय।",
            "action_advice": "ककरो ले अपन बैंक खाता या OTP झन बतावव। फोन ल तुरते काटव।"
        },
        "en": {
            "title": "Confidential Banking Credential Protection Inquiry",
            "danger_banner": "🛡️ SECURITY DIRECTIVE: Under RBI regulations, banks, police, or government officials NEVER solicit passwords, card CVVs, or OTPs over the phone.",
            "action_advice": "Never share confidential banking credentials. Disconnect immediately."
        }
    },
    "identity_inquiry": {
        "hi": {
            "title": "कॉलर पहचान व आधिकारिक विवरण पड़ताल",
            "danger_banner": "🔍 आधिकारिक पड़ताल: असली बैंक या सरकारी अधिकारी आधिकारिक लैंडलाइन और लिखित नोटिस देते हैं; ठग बहाने बनाते हैं व धमकाते हैं।",
            "action_advice": "कॉलर से लिखित नोटिस और उनके कार्यालय का आधिकारिक लैंडलाइन नंबर मांगें। फोन पर कोई भुगतान न करें।"
        },
        "chg": {
            "title": "कॉलर के पहचान अउ दफ्तर के पड़ताल",
            "danger_banner": "🔍 सही पड़ताल: असली अधिकारी सही पता अउ लिखित नोटिस देथें, ठग मन डरवाथें।",
            "action_advice": "कॉलर ले लिखित नोटिस अउ दफ्तर के सही नंबर मांगव। फोन म कोनो पईसा झन भेजव।"
        },
        "en": {
            "title": "Caller Identity & Authority Verification",
            "danger_banner": "🔍 IDENTITY VERIFICATION: Legitimate bank and police officers provide official landlines and written notices; fraudsters evade and threaten.",
            "action_advice": "Demand official written correspondence and the verified office landline. Never transfer funds or share codes over the phone."
        }
    },
    "banking_inquiry": {
        "hi": {
            "title": "सुरक्षित बैंकिंग सेवा व प्रक्रिया पूछताछ",
            "danger_banner": "🏦 सुरक्षित बैंकिंग: बैलेंस, पासबुक या चेकबुक सेवाओं के लिए केवल बैंक के आधिकारिक ऐप (जैसे YONO, iMobile) या बैंक शाखा का उपयोग करें।",
            "action_advice": "बैंक खाते से संबंधित कार्य हमेशा बैंक की आधिकारिक शाखा में जाकर या प्रमाणित ऐप से ही करें।"
        },
        "chg": {
            "title": "सुरक्षित बैंक सेवा पड़ताल",
            "danger_banner": "🏦 सुरक्षित बैंक सेवा: पासबुक या बैलेंस जांचे बर बैंक के असली ऐप या शाखा म जावव।",
            "action_advice": "अपन बैंक के मुख्य शाखा म जाके ही खाता के काम करव।"
        },
        "en": {
            "title": "Safe Banking Procedures & Inquiry",
            "danger_banner": "🏦 SAFE BANKING: For balance, passbook, or chequebook inquiries, always use official banking apps or visit your local branch.",
            "action_advice": "Conduct banking inquiries exclusively through verified official branch channels."
        }
    }
}


def analyze_call_transcript(
    transcript: str,
    user_lang: str = "hi",
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyzes call transcript using contextual scam detection,
    5-stage timeline tracker, and pipeline classifier.
    Localized in user_lang ('hi', 'chg', or 'en').
    """
    if not session_id or session_id.startswith("static_"):
        sid = "static_call_analysis"
        reset_tracker(sid)
    else:
        sid = session_id

    lang_key = user_lang if user_lang in ("hi", "chg", "en") else "hi"

    # 1. Real-time Scam Engine
    scam_eval = detect_scam_in_transcript(transcript, user_lang=lang_key)

    # 2. 5-Stage Conversation Timeline
    stage_eval = track_conversation_step(sid, transcript)

    # 3. Base Pipeline for classification & highlights
    pipeline_res = run_detection_pipeline(transcript, user_lang=lang_key)

    # Merge verdict and confidence
    eval_key = scam_eval.get("eval_key", "safe")
    is_inquiry = eval_key in ("safe", "identity_inquiry", "banking_inquiry", "cyber_reporting", "credential_prompt_inquiry", "telecom_inquiry")

    if scam_eval["risk_level"] in ("HIGH", "CRITICAL"):
        pipeline_res["verdict"] = "likely_scam"
        pipeline_res["confidence_percent"] = max(pipeline_res.get("confidence_percent", 0), int(scam_eval["confidence"] * 100))
        pipeline_res["explanation"] = scam_eval["reason"]
    elif is_inquiry:
        # Legitimate procedural inquiry / safe query: prevent text ML false positive override
        pipeline_res["verdict"] = "genuine"
        pipeline_res["explanation"] = scam_eval["reason"]
        scam_eval["risk_level"] = "LOW"
        scam_eval["is_scam"] = False
    elif pipeline_res.get("verdict") == "likely_scam":
        # Elevated by hybrid ML/rule pipeline: sync category and explanation
        rule_flags = pipeline_res.get("rule_flags", {})
        if rule_flags.get("digital_arrest"):
            ekey = "digital_arrest"
        elif rule_flags.get("explicit_otp_demand"):
            ekey = "otp_fraud"
        elif rule_flags.get("remote_access_apk"):
            ekey = "remote_access"
        elif rule_flags.get("fake_kyc"):
            ekey = "bank_impersonation"
        else:
            ekey = "moderate_urgency"

        # Import category dictionaries for synchronization
        from app.detect.scam_engine import CATEGORY_MAP, REASON_MAP, ACTION_MAP
        scam_eval["risk_level"] = "HIGH"
        scam_eval["is_scam"] = True
        scam_eval["confidence"] = max(scam_eval.get("confidence", 0.88), float(pipeline_res.get("confidence_percent", 88)) / 100.0)
        scam_eval["scam_category"] = CATEGORY_MAP[ekey].get(lang_key, CATEGORY_MAP[ekey]["hi"])
        scam_eval["scam_category_hi"] = CATEGORY_MAP[ekey]["hi"]
        scam_eval["scam_category_en"] = CATEGORY_MAP[ekey]["en"]
        scam_eval["scam_category_chg"] = CATEGORY_MAP[ekey]["chg"]
        scam_eval["reason"] = REASON_MAP[ekey].get(lang_key, REASON_MAP[ekey]["hi"])
        scam_eval["reason_hi"] = REASON_MAP[ekey]["hi"]
        scam_eval["reason_en"] = REASON_MAP[ekey]["en"]
        scam_eval["reason_chg"] = REASON_MAP[ekey]["chg"]
        scam_eval["recommended_action"] = ACTION_MAP[ekey].get(lang_key, ACTION_MAP[ekey]["hi"])
        scam_eval["recommended_action_hi"] = ACTION_MAP[ekey]["hi"]
        scam_eval["recommended_action_en"] = ACTION_MAP[ekey]["en"]
        scam_eval["recommended_action_chg"] = ACTION_MAP[ekey]["chg"]
        pipeline_res["explanation"] = scam_eval["reason"]
    elif scam_eval["risk_level"] == "MODERATE":
        pipeline_res["verdict"] = "unsure"
        pipeline_res["explanation"] = scam_eval["reason"]
    else:
        pipeline_res["verdict"] = "genuine"
        pipeline_res["explanation"] = scam_eval["reason"]

    # Script metadata mapping with multi-lingual localization
    script_meta = None
    script_key = None
    if scam_eval["risk_level"] == "CRITICAL" and "upi_pin_fraud" in scam_eval.get("matched_categories", []):
        script_key = "upi_pin_fraud"
    elif "otp_fraud" in scam_eval.get("matched_categories", []) or scam_eval.get("eval_key") == "otp_fraud" or pipeline_res.get("rule_flags", {}).get("explicit_otp_demand"):
        script_key = "otp_fraud"
    elif "police_govt_impersonation" in scam_eval.get("matched_categories", []) or "digital_arrest" in transcript.lower() or "digital arrest" in transcript.lower() or scam_eval.get("eval_key") == "digital_arrest":
        script_key = "digital_arrest"
    elif "telecom_sim_block" in scam_eval.get("matched_categories", []) or scam_eval.get("eval_key") == "telecom_sim_block":
        script_key = "telecom_sim_block"
    elif "job_task_fraud" in scam_eval.get("matched_categories", []) or scam_eval.get("eval_key") == "job_task_fraud":
        script_key = "job_task_fraud"
    elif "utility_electricity" in scam_eval.get("matched_categories", []) or scam_eval.get("eval_key") == "utility_electricity":
        script_key = "utility_electricity"
    elif "remote_access" in scam_eval.get("matched_categories", []) or scam_eval.get("eval_key") == "remote_access":
        script_key = "remote_access"
    elif "courier_customs" in scam_eval.get("matched_categories", []) or scam_eval.get("eval_key") == "courier_customs" or any(x in transcript.lower() for x in ["courier", "parcel", "customs", "पार्सल"]):
        script_key = "customs_courier"
    elif "lottery_subsidy" in scam_eval.get("matched_categories", []) or scam_eval.get("eval_key") == "lottery_subsidy":
        script_key = "lottery_subsidy"
    elif "bank_impersonation" in scam_eval.get("matched_categories", []) or scam_eval.get("eval_key") == "bank_impersonation" or "fake_kyc" in transcript.lower():
        script_key = "fake_kyc"
    elif scam_eval.get("eval_key") == "credential_prompt_inquiry":
        script_key = "credential_prompt_inquiry"
    elif scam_eval.get("eval_key") == "identity_inquiry" or "manager" in transcript.lower() or "employee id" in transcript.lower():
        script_key = "identity_inquiry"
    elif scam_eval.get("eval_key") == "banking_inquiry":
        script_key = "banking_inquiry"
    elif scam_eval.get("eval_key") == "cyber_reporting" or "1930" in transcript:
        script_key = "cyber_reporting"

    if script_key and script_key in CALL_SCRIPTS:
        meta_dict = CALL_SCRIPTS[script_key]
        script_meta = meta_dict.get(lang_key, meta_dict.get("hi", meta_dict.get("en")))

    return {
        **pipeline_res,
        "script_meta": script_meta,
        "script_meta_map": CALL_SCRIPTS.get(script_key) if script_key else None,
        "text": transcript,
        "transcript": transcript,
        "risk_level": scam_eval["risk_level"],
        "scam_category": scam_eval["scam_category"],
        "scam_category_hi": scam_eval.get("scam_category_hi", scam_eval["scam_category"]),
        "scam_category_en": scam_eval.get("scam_category_en", scam_eval["scam_category"]),
        "scam_category_chg": scam_eval.get("scam_category_chg", scam_eval["scam_category"]),
        "reason": scam_eval["reason"],
        "reason_hi": scam_eval.get("reason_hi", scam_eval["reason"]),
        "reason_en": scam_eval.get("reason_en", scam_eval["reason"]),
        "reason_chg": scam_eval.get("reason_chg", scam_eval["reason"]),
        "recommended_action": scam_eval["recommended_action"],
        "recommended_action_hi": scam_eval.get("recommended_action_hi", scam_eval["recommended_action"]),
        "recommended_action_en": scam_eval.get("recommended_action_en", scam_eval["recommended_action"]),
        "recommended_action_chg": scam_eval.get("recommended_action_chg", scam_eval["recommended_action"]),
        "audio_warning_hi": scam_eval.get("audio_warning_hi", ""),
        "audio_warning_en": scam_eval.get("audio_warning_en", ""),
        "audio_warning_chg": scam_eval.get("audio_warning_chg", ""),
        "suspicious_phrases": scam_eval.get("suspicious_phrases", []),
        "matched_categories": scam_eval.get("matched_categories", []),
        "stages": stage_eval,
        "claim_contradictions": stage_eval.get("claim_contradictions", [])
    }
