"""
Synthetic Dataset Generator for Suraksha
Generates 3,300+ balanced samples across English, Hindi (Devanagari), and Hinglish.
Scam categories: OTP, KYC, Digital Arrest, Electricity, Loan, Courier, Lottery/Cashback, Job scam.
Genuine categories: Real Bank OTP warnings (DO NOT SHARE), Debit/Credit alerts, Delivery, CSPDCL receipts, Normal chats.
"""

import json
import random
from pathlib import Path

def generate_synthetic_dataset(output_path: Path = None, target_count: int = 3300):
    random.seed(42)
    
    # Templates for English Scams
    en_scam_templates = [
        "Dear customer, your SBI account {ac} is suspended due to incomplete KYC. Click {link} to update immediately or account will be permanently blocked.",
        "URGENT: CSPDCL Electricity officer notice. Your electricity power will be disconnected tonight at 9:30 PM due to unpaid bill of Rs {amt}. Call immediate officer at {phone}.",
        "CBI Cyber Crime Cell Notice: A parcel containing contraband drugs and {num} passports registered to your Aadhaar has been intercepted at Mumbai airport. You are placed under DIGITAL ARREST. Do not disconnect this call or tell anyone. Pay clearance bond of Rs {amt} immediately.",
        "Congratulations! Your mobile number won Rs {amt_high} in Kaun Banega Crorepati Lottery. To claim prize, share 6-digit verification code OTP sent to your phone with KBC manager at {phone}.",
        "Dear User, your HDFC netbanking is blocked. Call our executive immediately at {phone} and share your debit card CVV and OTP to restore access.",
        "Pre-approved personal loan of Rs {amt_high} credited to your wallet without documents. Download instant APK app at {link} and grant contact access to withdraw cash.",
        "FedEx Courier Alert: Your international parcel from UK is held by Indian Customs for customs duty of Rs {amt}. Pay duty immediately at {link} to avoid arrest.",
        "Work from home opportunity: Earn Rs 3000 to 5000 daily by reviewing hotel maps. Pay one-time security deposit of Rs {amt} via UPI to activate your VIP tasks.",
        "Dear customer, your SIM card will be deactivated within 2 hours. Kindly install AnyDesk or QuickSupport app and enter 9-digit code to verify KYC.",
        "Income Tax Refund of Rs {amt} approved for your PAN card. Claim direct refund to bank account by submitting netbanking password and OTP at {link}."
    ]

    # Templates for Hindi Scams
    hi_scam_templates = [
        "प्रिय ग्राहक, आपका एसबीआई बैंक खाता KYC न होने के कारण बंद कर दिया गया है। चालू रखने के लिए तुरंत {link} पर क्लिक करें अथवा 2 घंटे में खाता हमेशा के लिए सील हो जाएगा।",
        "अति आवश्यक सूचना: बिजली विभाग (CSPDCL)। आपका पिछला बिजली बिल जमा न होने से आज रात 9:30 बजे बिजली कनेक्शन काट दिया जाएगा। तुरंत बिजली अधिकारी {phone} पर कॉल करें।",
        "क्राइम ब्रांच व CBI डिजिटल अरेस्ट वारंट: आपके आधार कार्ड से मुंबई कस्टम्स में नशीली दवाओं और फर्जी पासपोर्ट का पार्सल पकड़ा गया है। आप घर पर डिजिटल अरेस्ट में हैं। वीडियो कॉल बंद न करें और तुरंत जमानत राशि रु {amt} जमा करें।",
        "बधाई हो! आपके मोबाइल नंबर ने KBC लकी ड्रॉ में रु {amt_high} जीते हैं। पुरस्कार राशि खाते में पाने के लिए अपने फोन पर आया 6 अंकों का OTP नंबर इस {phone} पर बताएं।",
        "आपका एटीएम कार्ड ब्लॉक हो गया है। इसे तुरंत अनब्लॉक करने के लिए अपने कार्ड का सीवीवी (CVV) और वन टाइम पासवर्ड (OTP) हमारे बैंक प्रतिनिधि को बताएं।",
        "आसान लोन! केवल आधार कार्ड पर 5 मिनट में रु {amt_high} का लोन पाएं। बिना ब्याज। तुरंत हमारा ऐप डाउनलोड करें: {link}",
        "कूरियर पार्सल सूचना: आपका विदेश से आया कीमती पार्सल कस्टम ड्यूटी न भरने से रोक दिया गया है। पार्सल छुड़ाने के लिए तुरंत रु {amt} का भुगतान करें: {link}",
        "घर बैठे पार्ट टाइम नौकरी: यूट्यूब वीडियो लाइक करके रोजाना 2000 से 4000 रुपये कमाएं। रजिस्ट्रेशन के लिए मात्र रु {amt} ट्रांसफर करें।",
        "सावधान! आपका 5G सिम कार्ड आज रात बंद हो जाएगा। सिम चालू रखने के लिए अपने फोन में AnyDesk ऐप इंस्टॉल करें और 9-अंकों का कोड शेयर करें।",
        "प्रधानमंत्री मुद्रा योजना के तहत आपको रु {amt_high} की सब्सिडी मिली है। इसे अपने खाते में ट्रांसफर करने के लिए UPI पिन दर्ज करें।"
    ]

    # Templates for Hinglish Scams
    hinglish_scam_templates = [
        "Dear user, aapka SBI YONO account block ho gaya hai. KYC update karne ke liye turant is link {link} par click kare ya account seal ho jayega.",
        "Important Alert: CSPDCL Bijli vibhag. Aapka bijli bill pending hai, aaj raat 9:30 baje bijli kaat di jayegi. Turant officer {phone} par call kare.",
        "Mumbai Crime Branch notice: Aapke naam par drugs parcel pakda gaya hai. Aap DIGITAL ARREST me hain. Call cut mat karna aur clearance fee rs {amt} turant pay karo.",
        "Badhai ho! Aapka number KBC lottery me select hua hai rs {amt_high} ke liye. Prize lene ke liye phone par aaya 6 digit OTP officer {phone} ko send kare.",
        "Aapka ATM card block ho gaya hai. Turant unblock karne ke liye apna 16 digit card number aur OTP verify karwaye.",
        "Instant loan offer! Rs {amt_high} approved without CIBIL score. Download cash apk from {link} and allow full contacts permission.",
        "FedEx Parcel Notice: London se aapka parcel customs me atka hai. Rs {amt} tax bharne ke liye {link} par payment kare nahi toh police case hoga.",
        "Ghar baithe paise kamaye: Daily 3000 rs earning just by liking videos. Join VIP telegram group and pay rs {amt} registration fees.",
        "Aapka SIM card 2 hours me block ho jayega. QuickSupport ya AnyDesk app download karke code bataye for instant KYC.",
        "Income tax department ne aapka refund rs {amt} approve kiya hai. Receive karne ke liye link {link} par UPI pin enter kare."
    ]

    # Templates for Genuine English
    en_genuine_templates = [
        "{otp} is your secret One Time Password (OTP) for online purchase of Rs {amt} at Amazon. DO NOT SHARE WITH ANYONE. Bank never calls to ask OTP.",
        "Dear Customer, your A/C XX{ac_short} is debited by Rs {amt} on {date}. Available Balance: Rs {bal}. If not done by you, SMS BLOCK to 567676. -SBI",
        "Your package with tracking number {trk} is out for delivery today. Delivery agent will call before arrival. Please keep payment ready if COD.",
        "Dear Consumer, thank you for your payment of Rs {amt} towards CSPDCL Electricity Bill for consumer no {cnum}. Receipt no: {rcpt}.",
        "Your transaction of Rs {amt} using UPI ID {upi} was successful on {date}. Ref no: {ref}. -HDFC Bank",
        "Hey Ramesh, are you attending the gram panchayat meeting tomorrow morning in Raipur?",
        "Please bring 2 copies of land patta document and ration card for tractor subsidy verification at tehsil office.",
        "Dear User, your 1.5 GB daily data pack is 50% exhausted. Recharge anytime with unlimited plans on official operator app.",
        "Meeting with the agricultural loan officer has been rescheduled to Friday 11:30 AM at Durg branch.",
        "Happy Diwali to you and your family! May the festival of lights bring health and prosperity to your village."
    ]

    # Templates for Genuine Hindi
    hi_genuine_templates = [
        "{otp} आपका भारतीय स्टेट बैंक का गुप्त OTP है। राशि रु {amt}। यह कोड किसी के साथ साझा न करें। बैंक कभी भी OTP नहीं पूछता।",
        "प्रिय ग्राहक, आपके खाता संख्या XX{ac_short} से रु {amt} की निकासी हुई है। शेष राशि रु {bal}। यदि यह आपने नहीं किया तो तुरंत 1800112211 पर सूचित करें। -एसबीआई",
        "आपका फ्लिपकार्ट ऑर्डर ट्रैकिंग संख्या {trk} आज डिलीवरी के लिए निकल चुका है। डिलीवरी बॉय आपसे संपर्क करेगा।",
        "धन्यवाद! CSPDCL बिजली बिल भुगतान रु {amt} सफलतापूर्वक प्राप्त हुआ। रसीद संख्या: {rcpt}।",
        "आपके UPI से रु {amt} का भुगतान किराना स्टोर को सफलतापूर्वक हो गया है। UTR संख्या: {ref}।",
        "नमस्ते भैया, कल सुबह रायपुर मंडी में धान बेचने जा रहे हैं क्या? साथ में चलेंगे।",
        "तहसीलदार कार्यालय में किसान सम्मान निधि के सत्यापन के लिए आधार और खतौनी की प्रतिलिपि अवश्य ले आएं।",
        "आपका दैनिक डेटा पैक 90% समाप्त हो चुका है। अधिक जानकारी के लिए आधिकारिक ऐप पर जाएं।",
        "जिला सहकारी बैंक बिलासपुर की शाखा कल सार्वजनिक अवकाश के कारण बंद रहेगी।",
        "होली के पावन पर्व पर आपको और आपके समस्त परिवार को हार्दिक शुभकामनाएं एवं जोहार।"
    ]

    # Templates for Genuine Hinglish
    hinglish_genuine_templates = [
        "{otp} is your secret OTP for transaction of Rs {amt} at Flipkart. Kripya kisi ko na bataye. Bank kabhi phone par OTP nahi mangta.",
        "Aapke account XX{ac_short} se Rs {amt} debit hua hai on {date}. Avail bal Rs {bal}. Fraud report karne ke liye 1930 par call kare. -SBI",
        "Aapka parcel out for delivery hai. Hamara delivery agent jald hi call karega.",
        "CSPDCL Bijli bill payment of Rs {amt} successfully receive ho gaya hai. Consumer ID {cnum}. Thank you.",
        "UPI payment of Rs {amt} to Verma General Store successful. UTR no {ref}.",
        "Bhaiya kal subah Bilaspur station par milte hain, train 8 baje pahunchegi.",
        "Kisan credit card ka renewal form branch manager ke paas submit kar diya hai.",
        "Mummy ki dawai medical store se le li hai, shaam ko gaon aate waqt le aaunga.",
        "Gram sabha meeting Friday ko 2 baje panchayat bhavan me rakhi gayi hai.",
        "Durg bypass road par traffic jam hai, dusre raste se aana."
    ]

    # Synthetic variable generators
    def random_phone():
        prefixes = ["98", "97", "94", "70", "81", "91", "62", "88"]
        return random.choice(prefixes) + "".join([str(random.randint(0, 9)) for _ in range(8)])

    def random_link():
        domains = ["bit.ly/sbi-kyc-verify", "tinyurl.com/cspdcl-pay", "cbi-arrest-online.in", 
                   "sbi-yono-update.top", "kbc-lucky-winner.site", "apk-fast-loan.vip", 
                   "fedex-customs-pay.cc", "cspdcl-bill-clear.xyz"]
        return random.choice(domains)

    records = []

    # Target: 3300 total -> 1100 English, 1100 Hindi, 1100 Hinglish
    # In each language: 550 Scam, 550 Genuine
    languages = [
        ("en", en_scam_templates, en_genuine_templates),
        ("hi", hi_scam_templates, hi_genuine_templates),
        ("hinglish", hinglish_scam_templates, hinglish_genuine_templates)
    ]

    samples_per_category = target_count // (len(languages) * 2) # ~550 each

    for lang, scam_temps, gen_temps in languages:
        # Generate Scams
        for i in range(samples_per_category):
            temp = random.choice(scam_temps)
            msg = temp.format(
                ac=f"XX{random.randint(1000, 9999)}",
                link=random_link(),
                phone=random_phone(),
                amt=random.randint(450, 48000),
                amt_high=random.choice([25000, 50000, 100000, 2500000]),
                num=random.randint(3, 12)
            )
            records.append({
                "id": f"{lang}_scam_{i:04d}",
                "text": msg,
                "label": 1,
                "label_name": "scam",
                "language": lang
            })

        # Generate Genuine
        for i in range(samples_per_category):
            temp = random.choice(gen_temps)
            msg = temp.format(
                otp=f"{random.randint(100000, 999999)}",
                amt=random.randint(50, 8500),
                ac_short=f"{random.randint(1000, 9999)}",
                bal=random.randint(1200, 95000),
                date=f"{random.randint(1, 28)}-Nov-2026",
                trk=f"IN{random.randint(10000000, 99999999)}",
                cnum=f"10{random.randint(100000, 999999)}",
                rcpt=f"RCP{random.randint(100000, 999999)}",
                upi=f"merchant{random.randint(100, 999)}@bank",
                ref=f"{random.randint(100000000000, 999999999999)}"
            )
            records.append({
                "id": f"{lang}_gen_{i:04d}",
                "text": msg,
                "label": 0,
                "label_name": "genuine",
                "language": lang
            })

    # Shuffle dataset
    random.shuffle(records)

    if output_path is None:
        output_path = Path(__file__).resolve().parent.parent.parent / "data" / "dataset.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"[Dataset Generator] Generated {len(records)} balanced samples saved to {output_path}")
    return records

if __name__ == "__main__":
    generate_synthetic_dataset()
