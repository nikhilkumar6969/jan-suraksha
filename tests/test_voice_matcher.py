"""
Unit Test Suite for Jan Suraksha Offline Voice Intent Matcher
Tests:
1. >= 15 phrases per intent across English, Hindi, Hinglish, Chhattisgarhi
2. Noisy variants (typos, missing words, filler words)
3. Negative cases (non-scam everyday conversation that must NOT match any intent)
Reports exact accuracy per intent and per language.
"""

import json
import subprocess
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
VOICE_INTENTS_JSON = FRONTEND_DIR / "content" / "voice_intents.json"
VOICE_MATCHER_JS = FRONTEND_DIR / "js" / "voice_matcher.js"

# Comprehensive test corpus
TEST_CORPUS = {
    "whatsapp_or_sms_message": {
        "en": [
            "I got a WhatsApp message",
            "I received a message on WhatsApp",
            "Check this WhatsApp link",
            "Someone sent me a WhatsApp text",
            "Check this SMS",
            "I got an SMS from bank",
            "Got a text message about electricity bill",
            "Suspicious SMS received today",
            "Verify this message please",
            "Is this SMS safe to open",
            "Someone forwarded a WhatsApp message",
            "Got a lottery SMS",
            "Check this text",
            "SMS came on my phone",
            "WhatsApp link check"
        ],
        "hi": [
            "मुझे व्हाट्सएप मैसेज आया",
            "व्हाट्सएप मैसेज आया है",
            "व्हाट्सएप पर लिंक आया है",
            "एसएमएस आया है",
            "मुझे मैसेज आया",
            "संदेश चेक करो",
            "बैंक का मैसेज आया है",
            "बिजली बिल का मैसेज आया",
            "लॉटरी का मैसेज आया है",
            "संदिग्ध मैसेज जांचें",
            "व्हाट्सएप पर लॉटरी का मैसेज आया",
            "संदिग्ध संदेश जांचें",
            "मैसेज में लिंक आया है",
            "फर्जी मैसेज आया है",
            "एक संदेश चेक करना है"
        ],
        "hinglish": [
            "WhatsApp message aaya hai",
            "SMS aaya hai",
            "WhatsApp pe link aaya",
            "ek message check karna hai",
            "fraud message lag raha hai",
            "message verify karo",
            "bank ka SMS aaya",
            "suspicious message check karo",
            "koi link bheja hai message me",
            "SMS me link aaya hai",
            "electricity bill message aaya",
            "lottery message aaya",
            "WhatsApp forward check karo",
            "message aaya hai check kar do",
            "WhatsApp pe text aaya hai"
        ],
        "chg": [
          "मोला व्हाट्सएप म मैसेज आइस",
          "व्हाट्सएप म संदेश आए हे",
          "व्हाट्सएप म लिंक भेजे हे",
          "मोला मैसेज आए हे",
          "एसएमएस आए हे",
          "ककरो संदेश आए हे",
          "मोला मैसेज भेजे हे ओला जांचव",
          "संदेश ल देखव",
          "चिट्ठी आए हे मैसेज म",
          "बैंक के मैसेज आए हे",
          "बिजली बिल के मैसेज आइस",
          "मैसेज म ठगी के संका हे",
          "मोला एक ठो मैसेज आइस हे",
          "मैसेज ल चेक करव",
          "व्हाट्सएप म पईसा के मैसेज आइस"
        ]
    },
    "phone_call": {
        "en": [
            "someone called me",
            "fake police call",
            "I got a suspicious call",
            "police officer calling",
            "CBI call received",
            "digital arrest call",
            "customs call",
            "suspicious phone call",
            "someone threatening on call",
            "check this call",
            "call recording check",
            "unknown number called me",
            "bank officer calling me",
            "fake police calling",
            "call verification"
        ],
        "hi": [
            "मुझे फोन आया",
            "फर्जी पुलिस की कॉल आई है",
            "डिजिटल अरेस्ट कॉल आया",
            "कॉल आया है",
            "सीबीआई अफसर का फोन आया",
            "कस्टम का फोन आया है",
            "कॉल की जांच करो",
            "धमकी भरा फोन आया",
            "थाने से फोन आया है",
            "अरेस्ट करने की धमकी दे रहे हैं",
            "बैंक अधिकारी का फोन आया",
            "संदिग्ध कॉल की जांच",
            "कोई फोन पर डरा रहा है",
            "फोन काट मत करना बोल रहे हैं",
            "कॉल पर पैसे मांग रहे हैं"
        ],
        "hinglish": [
            "phone aaya hai",
            "police call aaya",
            "digital arrest call aaya hai",
            "fake police call",
            "CBI bolkar call kiya",
            "suspicious call check karo",
            "kisi ka phone call aaya",
            "call pe paise maang rahe hain",
            "thana se phone aaya",
            "call cut mat karna bola",
            "customs ka call aaya",
            "unknown call aaya hai",
            "fake officer calling",
            "phone check karna hai",
            "call guardian chalu karo"
        ],
        "chg": [
          "मोला फोन आइस",
          "ककरो फोन आए हे",
          "थाना ले फोन आइस",
          "पुलिस बनके फोन करे हे",
          "डिजिटल अरेस्ट के फोन आए हे",
          "कॉल ल जांचव",
          "फोन म धमकी देत हे",
          "सीबीआई ले फोन आए हे",
          "फोन म पईसा मांगत हे",
          "कॉल ल झन काटव बोलत हे",
          "कोतवाली ले फोन आइस",
          "वारंट निकल गे बोलत हे फोन म",
          "फोन के जांच करव",
          "अंजान नंबर ले फोन आइस",
          "कॉल रिकॉर्डिंग सुनव"
        ]
    },
    "qr_payment": {
        "en": [
            "QR code",
            "scan QR",
            "scan this code",
            "payment request",
            "QR payment",
            "received a QR code",
            "is this QR safe",
            "someone sent QR to receive money",
            "UPI QR check",
            "scanner check",
            "scan payment request",
            "verify QR code",
            "fake QR check",
            "pay money by QR",
            "check scanner"
        ],
        "hi": [
            "क्यूआर कोड",
            "क्यूआर कोड स्कैन करो",
            "पेमेंट रिक्वेस्ट आई है",
            "क्यूआर कोड सही है क्या",
            "पैसे पाने के लिए क्यूआर स्कैन",
            "यूपीआई क्यूआर कोड जांचें",
            "स्कैनर खोलो",
            "क्यूआर कोड की जांच",
            "दुकानदार का क्यूआर कोड",
            "स्कैन करने को बोल रहे हैं",
            "क्यूआर कोड भेजा है",
            "फर्जी क्यूआर कोड",
            "क्यूआर से पैसे कटेंगे क्या",
            "बारकोड स्कैन करो",
            "क्यूआर कोड चेक करना है"
        ],
        "hinglish": [
            "QR code check karo",
            "scan karna hai",
            "payment request aayi hai",
            "QR code bheja hai",
            "paise lene ke liye QR scan bol rahe hain",
            "UPI QR check",
            "scanner open karo",
            "QR fake toh nahi hai",
            "QR scan karke check karo",
            "PhonePe QR check",
            "Paytm QR code check",
            "GPay scan code",
            "QR verify karna hai",
            "QR se fraud toh nahi hoga",
            "barcode scan karo"
        ],
        "chg": [
          "क्यूआर कोड जांचव",
          "क्यूआर स्कैन करव",
          "पईसा पाए बर क्यूआर स्कैन",
          "स्कैनर खोलव",
          "यूपीआई क्यूआर कोड",
          "क्यूआर कोड भेजे हे",
          "पईसा भेजे बर स्कैन करव",
          "क्यूआर कोड ठीक हे कि नइ",
          "क्यूआर म पईसा मांगत हे",
          "बारकोड ल जांचव",
          "दुकान के क्यूआर कोड चेक करव",
          "स्कैन करे बर बोलत हे",
          "क्यूआर कोड ल देखव",
          "क्यूआर म धोखा झन होवय",
          "यूपीआई कोड स्कैन करव"
        ]
    },
    "lost_money": {
        "en": [
            "I lost money",
            "money got deducted",
            "fraud happened",
            "cyber crime helpline",
            "call 1930",
            "stolen money",
            "account balance gone",
            "I was scammed",
            "help I lost my savings",
            "report fraud immediately",
            "money debited without permission",
            "bank account hacked",
            "help me with cyber fraud",
            "emergency fraud report",
            "someone stole my money"
        ],
        "hi": [
            "पैसे कट गए",
            "मेरे साथ फ्रॉड हो गया",
            "ठगी हो गई",
            "खाते से पैसे उड़ गए",
            "1930 पर कॉल करो",
            "साइबर अपराध हो गया",
            "धोखाधड़ी हो गई",
            "पैसे वापस कैसे मिलेंगे",
            "बैंक से पैसे कट गए मदद करो",
            "मेरे खाते से पैसे कट गए",
            "साइबर पुलिस से शिकायत करनी है",
            "रुपये कट गए",
            "ऑनलाइन फ्रॉड हो गया",
            "हेल्पलाइन नंबर 1930",
            "मदद चाहिए पैसे चोरी हो गए"
        ],
        "hinglish": [
            "paisa kat gaya",
            "fraud ho gaya",
            "paise chori ho gaye",
            "thagi ho gayi mere saath",
            "1930 helpline lagao",
            "account se balance kat gaya",
            "scam ho gaya mere saath",
            "help paisa chala gaya",
            "bank se paise kat gaye",
            "khata se paisa udd gaya",
            "complaint karni hai fraud ki",
            "cyber crime report karna hai",
            "1930 call lagao turant",
            "online thagi ho gayi",
            "paisa wapas chahiye"
        ],
        "chg": [
          "पईसा कट गे",
          "मोर संग ठगी होगे",
          "खाता ले पईसा उड़ गे",
          "फ्रॉड होगे",
          "1930 म फोन लगाव",
          "ठग लिस मोला",
          "पईसा लुट गे",
          "मदद करव पईसा कट गे",
          "मोर खाता ले रुपिया कट गे",
          "साइबर ठगी होगे मोला",
          "हेल्पलाइन 1930 म गोठियाना हे",
          "पईसा कइसे वापस आही",
          "धोखा म पईसा चले गे",
          "ककरो संग ठगी होगे",
          "तुरते रिपोर्ट करना हे"
        ]
    },
    "learn": {
        "en": [
            "teach me",
            "show lessons",
            "learn safety",
            "how to avoid scam",
            "take a quiz",
            "cyber safety tips",
            "learn UPI rules",
            "guide me",
            "lessons on fraud",
            "education",
            "safety rules",
            "learn about OTP",
            "how to protect bank account",
            "show educational video",
            "start quiz"
        ],
        "hi": [
            "सीखना है",
            "पाठ दिखाओ",
            "सुरक्षा सीखें",
            "क्विज खेलें",
            "धोखाधड़ी से कैसे बचें",
            "यूपीआई सुरक्षा सीखें",
            "नियम बताओ",
            "साइबर सुरक्षा पाठ",
            "सीखने का वीडियो",
            "मुझे सिखाओ",
            "ओटीपी सुरक्षा नियम",
            "सावधानी के नियम बताओ",
            "क्विज शुरू करो",
            "सुरक्षा पाठ पढ़ना है",
            "शिक्षा अनुभाग खोलो"
        ],
        "hinglish": [
            "seekhna hai",
            "lesson dikhao",
            "quiz khelna hai",
            "safety seekho",
            "scam se kaise bache",
            "cyber lesson padhao",
            "UPI rules batao",
            "guide karo",
            "sikhao mujhe",
            "fraud se bachne ke tips",
            "OTP rule seekhna hai",
            "educational video dekhna hai",
            "quiz start karo",
            "safety lesson padhna hai",
            "tips batao"
        ],
        "chg": [
          "सिखाव मोला",
          "पाठ दिखाव",
          "सुरक्षा सीखबो",
          "ठगी ले कइसे बचबो",
          "क्विज खेलबो",
          "नियम बताव",
          "सुरक्षा के गोठ बताओ",
          "मोला सिखाव कइसे सुरक्षित रहबो",
          "पाठ पढ़ाव",
          "यूपीआई सुरक्षा के नियम",
          "क्विज म भाग लेबो",
          "ज्ञान के बात बताओ",
          "ओटीपी सुरक्षा सीखव",
          "सुरक्षा वीडियो देखव",
          "कइसे बचबो बताव"
        ]
    }
}

NOISY_VARIANTS = [
    # Typos and common speech mis-transcriptions
    ("ummm watsp meseg aaya pls", "whatsapp_or_sms_message"),
    ("hello sir check this smses right now", "whatsapp_or_sms_message"),
    ("arre bhai fone kal aaya pulish ka", "phone_call"),
    ("unknown person kal kiya daroga bolke", "phone_call"),
    ("bhai cur code scan karna he", "qr_payment"),
    ("kew r paytm request mila he", "qr_payment"),
    ("oh no pisa kat gaya mera", "lost_money"),
    ("arre 1930 helpline lagao turant", "lost_money"),
    ("sir sikhao mujhe tips", "learn"),
    ("zara lesson dikhao na bhai", "learn"),
    ("मोला वॉटसप म मेसेज आइस हे", "whatsapp_or_sms_message"),
    ("थाना ले फोन आइस हे सुनव", "phone_call"),
    ("स्कैनर खोलव जी क्यूआर कोड बर", "qr_payment"),
    ("मोर पइसा कट गे हे मदद करव", "lost_money"),
    ("सुरक्षा के पाठ सिखाव जी", "learn")
]

NEGATIVE_CASES = [
    "What is the weather in Raipur today",
    "Where is the nearest train station",
    "How to make tea at home",
    "Tell me a joke",
    "Play my favorite song",
    "आज का मौसम कैसा रहेगा",
    "बाजार कब खुलेगा",
    "गाड़ी की चाबी कहाँ है",
    "खाना बन गया क्या",
    "मुझे नींद आ रही है",
    "kal cinema chalte hain",
    "match kitne baje start hoga",
    "roti sabzi kha li",
    "chhattisgarh me kisan kab aayenge",
    "good morning friends"
]

def run_matcher_batch(texts):
    """Executes voice_matcher.js in Node.js on a batch of strings."""
    script = f"""
    const fs = require('fs');
    const VoiceMatcher = require('{str(VOICE_MATCHER_JS).replace('\\', '/')}');
    const intentsJson = JSON.parse(fs.readFileSync('{str(VOICE_INTENTS_JSON).replace('\\', '/')}', 'utf8'));
    VoiceMatcher.intentsData = intentsJson;

    const inputs = {json.dumps(texts, ensure_ascii=False)};
    const results = inputs.map(t => VoiceMatcher.match(t));
    console.log(JSON.stringify(results));
    """
    proc = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)

def test_intent_matcher_full_coverage():
    """Validates >= 15 phrases per intent across all 4 languages."""
    stats = {}
    all_texts = []
    metadata = []

    for intent, lang_dict in TEST_CORPUS.items():
        stats[intent] = {}
        for lang, phrases in lang_dict.items():
            assert len(phrases) >= 15, f"{intent} in {lang} must have at least 15 phrases (got {len(phrases)})"
            stats[intent][lang] = {"total": len(phrases), "correct": 0}
            for p in phrases:
                all_texts.append(p)
                metadata.append((intent, lang, p))

    results = run_matcher_batch(all_texts)
    assert len(results) == len(all_texts)

    for (expected_intent, lang, phrase), res in zip(metadata, results):
        if res["intent"] == expected_intent:
            stats[expected_intent][lang]["correct"] += 1

    print("\n--- VOICE INTENT ACCURACY REPORT ---")
    grand_total = 0
    grand_correct = 0

    for intent, lang_dict in stats.items():
        intent_total = sum(l["total"] for l in lang_dict.values())
        intent_correct = sum(l["correct"] for l in lang_dict.values())
        acc = (intent_correct / intent_total) * 100
        grand_total += intent_total
        grand_correct += intent_correct
        print(f"Intent [{intent}]: {intent_correct}/{intent_total} ({acc:.1f}%)")
        for lang, l_stat in lang_dict.items():
            l_acc = (l_stat["correct"] / l_stat["total"]) * 100
            print(f"  └─ {lang.upper()}: {l_stat['correct']}/{l_stat['total']} ({l_acc:.1f}%)")

    overall_acc = (grand_correct / grand_total) * 100
    print(f"Overall Corpus Accuracy: {grand_correct}/{grand_total} ({overall_acc:.1f}%)")
    assert overall_acc >= 95.0, f"Expected overall accuracy >= 95%, got {overall_acc:.1f}%"

def test_noisy_and_misspelled_variants():
    """Tests noisy variants with filler words, phonetic typos, and contractions."""
    texts = [t[0] for t in NOISY_VARIANTS]
    results = run_matcher_batch(texts)

    correct = 0
    for (phrase, expected_intent), res in zip(NOISY_VARIANTS, results):
        if res["intent"] == expected_intent:
            correct += 1
        else:
            print(f"FAILED NOISY: '{phrase}' -> expected {expected_intent}, got {res['intent']}")

    acc = (correct / len(NOISY_VARIANTS)) * 100
    print(f"\nNoisy Variants Accuracy: {correct}/{len(NOISY_VARIANTS)} ({acc:.1f}%)")
    assert acc >= 90.0, f"Expected noisy accuracy >= 90%, got {acc:.1f}%"

def test_negative_cases():
    """Ensures general non-scam phrases do not trigger false positive fraud intents."""
    results = run_matcher_batch(NEGATIVE_CASES)
    false_positives = []

    for phrase, res in zip(NEGATIVE_CASES, results):
        if res["intent"] is not None:
            false_positives.append((phrase, res["intent"]))

    print(f"\nNegative Cases: {len(NEGATIVE_CASES) - len(false_positives)}/{len(NEGATIVE_CASES)} correctly rejected")
    if false_positives:
        print(f"False Positives: {false_positives}")
    assert len(false_positives) == 0, f"Expected 0 false positives, got {len(false_positives)}"
