const VoiceMatcher = require('../frontend/js/voice_matcher.js');
const fs = require('fs');

const intentsData = JSON.parse(fs.readFileSync('frontend/content/voice_intents.json', 'utf8'));
VoiceMatcher.intentsData = intentsData;

const testCases = [
  // Chhattisgarhi phrases (Devanagari)
  { text: "मोला व्हाट्सएप म मैसेज आइस", expected: "whatsapp_or_sms_message" },
  { text: "व्हाट्सएप म संदेश आए हे", expected: "whatsapp_or_sms_message" },
  { text: "व्हाट्सएप म लिंक भेजे हे", expected: "whatsapp_or_sms_message" },
  { text: "मोला मैसेज आइस हे", expected: "whatsapp_or_sms_message" },
  { text: "ककरो संदेश आए हे", expected: "whatsapp_or_sms_message" },
  { text: "मोला मैसेज भेजे हे ओला जांचव", expected: "whatsapp_or_sms_message" },
  { text: "चिट्ठी आए हे मैसेज म", expected: "whatsapp_or_sms_message" },
  { text: "मोला एक ठो मैसेज आइस हे", expected: "whatsapp_or_sms_message" },
  { text: "मोला फोन आइस", expected: "phone_call" },
  { text: "ककरो फोन आए हे", expected: "phone_call" },
  { text: "थाना ले फोन आइस", expected: "phone_call" },
  { text: "कोतवाली ले फोन आइस", expected: "phone_call" },
  { text: "पुलिस बनके फोन करे हे", expected: "phone_call" },
  { text: "कॉल ल जांचव", expected: "phone_call" },
  { text: "फोन म पईसा मांगत हे", expected: "phone_call" },
  { text: "वारंट निकल गे बोलत हे फोन म", expected: "phone_call" },
  { text: "कॉल ल झन काटव बोलत हे", expected: "phone_call" },
  { text: "क्यूआर कोड जांचव", expected: "qr_payment" },
  { text: "क्यूआर स्कैन करव", expected: "qr_payment" },
  { text: "पईसा पाए बर क्यूआर स्कैन", expected: "qr_payment" },
  { text: "स्कैन करे बर बोलत हे", expected: "qr_payment" },
  { text: "पईसा कट गे", expected: "lost_money" },
  { text: "मोर संग ठगी होगे", expected: "lost_money" },
  { text: "खाता ले पईसा उड़ गे", expected: "lost_money" },
  { text: "ठग लिस मोला", expected: "lost_money" },
  { text: "पईसा लुट गे", expected: "lost_money" },
  { text: "मोर खाता ले रुपिया कट गे", expected: "lost_money" },
  { text: "सिखाव मोला", expected: "learn" },
  { text: "पाठ दिखाव", expected: "learn" },
  { text: "सुरक्षा सीखबो", expected: "learn" },
  { text: "ठगी ले कइसे बचबो", expected: "learn" },
  { text: "मोला सिखाव कइसे सुरक्षित रहबो", expected: "learn" },

  // Natural colloquial Chhattisgarhi variations (what someone might say casually)
  { text: "मोला एक मैसेज आइस हे ओला देख लेते", expected: "whatsapp_or_sms_message" },
  { text: "व्हाट्सएप म कोनो लिंक भेजे हे", expected: "whatsapp_or_sms_message" },
  { text: "अंजान नंबर ले फोन आइस हे", expected: "phone_call" },
  { text: "दरोगा बनके फोन करत हे", expected: "phone_call" },
  { text: "पईसा भेजे बर क्यूआर कोड स्कैन करे बर कहत हे", expected: "qr_payment" },
  { text: "मोर पइसा कट गे हे मदद करव", expected: "lost_money" },
  { text: "साइबर ठगी के रिपोर्ट करना हे", expected: "lost_money" },
  { text: "सुरक्षा के गोठ बताओ", expected: "learn" },
  { text: "ठगी से कइसे बचबो सिखावव", expected: "learn" },

  // Hindi phrases
  { text: "मुझे व्हाट्सएप मैसेज आया", expected: "whatsapp_or_sms_message" },
  { text: "व्हाट्सएप पर लिंक आया है", expected: "whatsapp_or_sms_message" },
  { text: "एसएमएस आया है चेक करो", expected: "whatsapp_or_sms_message" },
  { text: "फर्जी पुलिस की कॉल आई है", expected: "phone_call" },
  { text: "डिजिटल अरेस्ट का फोन आया", expected: "phone_call" },
  { text: "सीबीआई अफसर बोलकर कॉल किया", expected: "phone_call" },
  { text: "क्यूआर कोड स्कैन करना है", expected: "qr_payment" },
  { text: "पेमेंट रिक्वेस्ट आई है यूपीआई से", expected: "qr_payment" },
  { text: "पैसे कट गए फ्रॉड हो गया", expected: "lost_money" },
  { text: "1930 पर कॉल करो ठगी हो गई", expected: "lost_money" },
  { text: "मुझे साइबर सुरक्षा सीखना है", expected: "learn" },
  { text: "क्विज खेलना है और पाठ दिखाओ", expected: "learn" },

  // Romanized Chhattisgarhi / Hinglish
  { text: "mola whatsapp ma message aayis", expected: "whatsapp_or_sms_message" },
  { text: "mola phone aayis", expected: "phone_call" },
  { text: "qr scan karav", expected: "qr_payment" },
  { text: "paisa kat ge mor sang thagi hoge", expected: "lost_money" },
  { text: "sikhav mola", expected: "learn" }
];

let passed = 0;
let failed = 0;

for (const tc of testCases) {
  const res = VoiceMatcher.match(tc.text);
  if (res.intent === tc.expected) {
    passed++;
  } else {
    failed++;
    console.log(`FAIL: "${tc.text}" -> Got: ${res.intent} (score: ${res.score}), Expected: ${tc.expected}`);
  }
}

console.log(`\nResults: ${passed} / ${testCases.length} passed (${failed} failed).`);
