// Jan Suraksha — 3-Minute Hackathon Demo Controller (त्वरित डेमो नियंत्रक)
window.DemoManager = {
  init() {
    const btnDemo = document.getElementById('btnQuickDemo');
    const modal = document.getElementById('quickDemoModalOverlay');
    const btnClose = document.getElementById('btnCloseQuickDemoModal');

    if (btnDemo) {
      btnDemo.addEventListener('click', () => this.openModal());
    }

    if (btnClose) {
      btnClose.addEventListener('click', () => this.closeModal());
    }

    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) this.closeModal();
      });
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modal && modal.classList.contains('open')) {
        this.closeModal();
      }
    });

    // 1-Click Scenario Buttons
    const btnE = document.getElementById('btnDemoElectricity');
    const btnD = document.getElementById('btnDemoDigitalArrest');
    const btnC = document.getElementById('btnDemoChhattisgarhi');
    const btnK = document.getElementById('btnDemoKioskReceipt');

    if (btnE) btnE.addEventListener('click', () => this.runElectricityDemo());
    if (btnD) btnD.addEventListener('click', () => this.runDigitalArrestDemo());
    if (btnC) btnC.addEventListener('click', () => this.runChhattisgarhiDemo());
    if (btnK) btnK.addEventListener('click', () => this.runKioskDemo());
  },

  openModal() {
    const modal = document.getElementById('quickDemoModalOverlay');
    if (modal) modal.classList.add('open');
  },

  closeModal() {
    const modal = document.getElementById('quickDemoModalOverlay');
    if (modal) modal.classList.remove('open');
  },

  runElectricityDemo() {
    this.closeModal();
    if (window.App) {
      window.App.navigate('check');
      window.App.switchSubtab('subtab-sms');
    }
    const input = document.getElementById('smsInput');
    if (input) {
      input.value = "URGENT: CSPDCL Raipur bijli vibhag soochana. Aapka bijli bill pichhle mahine ka baki hai. Aaj raat 9:30 baje bijli kaat di jayegi. Bill turant jama karne hetu 9876543210 par call karein.";
    }
    if (window.MessageDetector) {
      window.MessageDetector.analyzeMessage();
    }
    if (window.App) {
      window.App.showToast("⚡ CSPDCL बिजली बिल ठगी डेमो सक्रिय");
    }
  },

  runDigitalArrestDemo() {
    this.closeModal();
    if (window.App) {
      window.App.navigate('check');
      window.App.switchSubtab('subtab-call');
    }
    if (window.CallDetector) {
      window.CallDetector.loadAudioSample('digital_arrest').then(() => {
        const inp = document.getElementById('callTranscriptInput');
        if (inp) {
          inp.value = "This is CBI Crime Branch officer Sharma. A suspicious parcel containing contraband drugs and passports under your Aadhaar was intercepted at Mumbai customs. You are under DIGITAL ARREST. Transfer fifty thousand rupees bail bond immediately or team will reach your home.";
        }
        window.CallDetector.analyzeTranscript();
      });
    }
    if (window.App) {
      window.App.showToast("🚨 डिजिटल अरेस्ट कॉल डेमो सक्रिय");
    }
  },

  runChhattisgarhiDemo() {
    this.closeModal();
    if (window.App) {
      window.App.navigate('check');
      window.App.switchSubtab('subtab-sms');
    }
    const input = document.getElementById('smsInput');
    if (input) {
      input.value = "महतारी वंदन योजना के 10000 रुपया बोनस तोर बैंक खाता म डाले बर तुरंत लिंक mahtari-cg-bonus.in म अपन आधार अउ बैंक OTP दर्ज करव नइ ते पैसा निरस्त हो जाही।";
    }
    if (window.MessageDetector) {
      window.MessageDetector.analyzeMessage();
    }
    if (window.App) {
      window.App.showToast("🌾 छत्तीसगढ़ी महतारी वंदन ठगी डेमो सक्रिय");
    }
  },

  runKioskDemo() {
    this.closeModal();
    if (window.KioskManager) {
      window.KioskManager.toggleKioskMode(true);
      window.KioskManager.openReceiptModal({
        text: "URGENT: CSPDCL Electricity officer notice. Power disconnection scheduled for tonight at 9:30 PM due to unpaid bill of Rs 1,450. Call officer immediately.",
        is_scam: true,
        confidence: 0.94,
        scam_type: "CSPDCL बिजली बिल ठगी",
        threat_indicators: ["फर्जी बिजली अधिकारी", "बिजली काटने की तत्काल धमकी", "अनधिकृत नंबर पर कॉल करने का दबाव"]
      });
    }
    if (window.App) {
      window.App.showToast("🏛️ ग्राम पंचायत परामर्श पावती डेमो सक्रिय");
    }
  }
};
