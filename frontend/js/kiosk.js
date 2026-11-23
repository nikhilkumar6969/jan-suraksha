// Jan Suraksha — Village Kiosk & CSC Assisted Mode (ग्राहक सेवा केंद्र / चॉइस सेंटर सहायक मोड)
window.KioskManager = {
  isKioskActive: false,
  lastAssessment: null,

  init() {
    const btnToggle = document.getElementById('btnToggleKiosk');
    const btnExit = document.getElementById('btnKioskExit');
    const btnLog = document.getElementById('btnKioskLogModal');

    if (btnToggle) {
      btnToggle.addEventListener('click', () => {
        this.toggleKioskMode(!this.isKioskActive);
      });
    }

    if (btnExit) {
      btnExit.addEventListener('click', () => {
        this.toggleKioskMode(false);
      });
    }

    if (btnLog) {
      btnLog.addEventListener('click', () => {
        this.openLogModal();
      });
    }

    // Receipt Modal Actions
    const btnCloseReceipt = document.getElementById('btnCloseReceiptModal');
    const btnPrint = document.getElementById('btnPrintReceipt');
    const btnDownloadText = document.getElementById('btnDownloadReceiptText');

    if (btnCloseReceipt) {
      btnCloseReceipt.addEventListener('click', () => this.closeReceiptModal());
    }
    if (btnPrint) {
      btnPrint.addEventListener('click', () => window.print());
    }
    if (btnDownloadText) {
      btnDownloadText.addEventListener('click', () => this.downloadReceiptText());
    }

    // Log Modal Actions
    const btnCloseLog = document.getElementById('btnCloseKioskLogModal');
    const btnExportCsv = document.getElementById('btnExportKioskLogCsv');
    const btnClearLog = document.getElementById('btnClearKioskLog');

    if (btnCloseLog) {
      btnCloseLog.addEventListener('click', () => this.closeLogModal());
    }
    if (btnExportCsv) {
      btnExportCsv.addEventListener('click', () => this.exportLogCsv());
    }
    if (btnClearLog) {
      btnClearLog.addEventListener('click', () => this.clearLog());
    }

    // Keyboard Escape handler
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.closeReceiptModal();
        this.closeLogModal();
      }
    });

    // Restore saved kiosk mode if previously active
    const savedKiosk = localStorage.getItem('suraksha_kiosk_mode');
    if (savedKiosk === 'true') {
      this.toggleKioskMode(true, false);
    }

    this.updateIncidentCounter();
  },

  toggleKioskMode(enable, showToastMsg = true) {
    this.isKioskActive = enable;
    localStorage.setItem('suraksha_kiosk_mode', enable ? 'true' : 'false');

    document.body.classList.toggle('kiosk-mode-active', enable);

    const banner = document.getElementById('kioskTopBanner');
    if (banner) {
      banner.style.display = enable ? 'block' : 'none';
    }

    const btnToggle = document.getElementById('btnToggleKiosk');
    if (btnToggle) {
      btnToggle.classList.toggle('active', enable);
      btnToggle.setAttribute('aria-pressed', enable ? 'true' : 'false');
    }

    if (showToastMsg && window.App) {
      if (enable) {
        window.App.showToast('🏛️ ग्राहक सेवा केंद्र (CSC) सहायक मोड सक्रिय');
      } else {
        window.App.showToast('नागरिक मोड पर वापस आ गए');
      }
    }
  },

  generateRefId() {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    let code = '';
    for (let i = 0; i < 5; i++) {
      code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    const d = new Date();
    const yr = d.getFullYear();
    const mo = String(d.getMonth() + 1).padStart(2, '0');
    return `JS-CG-${yr}${mo}-${code}`;
  },

  openReceiptModal(assessment) {
    this.lastAssessment = assessment || this.lastAssessment;
    const a = this.lastAssessment;
    if (!a) {
      if (window.App) window.App.showToast('पहले कोई संदेश या कॉल जांचें');
      return;
    }

    const refId = a.refId || this.generateRefId();
    a.refId = refId;
    const dateStr = a.timestamp || new Date().toLocaleString('hi-IN', {
      timeZone: 'Asia/Kolkata',
      dateStyle: 'medium',
      timeStyle: 'short'
    });

    // Populate Receipt Fields
    const elRef = document.getElementById('rcptRefId');
    const elDate = document.getElementById('rcptDate');
    const elRiskBadge = document.getElementById('rcptRiskBadge');
    const elType = document.getElementById('rcptScamType');
    const elConfidence = document.getElementById('rcptConfidence');
    const elSnippet = document.getElementById('rcptMessageSnippet');
    const elThreats = document.getElementById('rcptThreatList');
    const elAction = document.getElementById('rcptActionAdvice');

    if (elRef) elRef.textContent = refId;
    if (elDate) elDate.textContent = dateStr;

    const isScam = a.is_scam !== undefined ? a.is_scam : (a.risk_level === 'high' || a.confidence > 0.6);
    const riskText = isScam ? 'सावधान! उच्च जोखिम (HIGH RISK SCAM)' : 'सुरक्षित / सामान्य (SAFE / LOW RISK)';
    const riskClass = isScam ? 'danger' : 'safe';

    if (elRiskBadge) {
      elRiskBadge.textContent = riskText;
      elRiskBadge.className = `rcpt-risk-badge ${riskClass}`;
    }

    if (elType) {
      elType.textContent = a.scam_type || a.category || 'सामान्य साइबर जांच';
    }

    if (elConfidence) {
      const confVal = Math.round((a.confidence || 0.85) * 100);
      elConfidence.textContent = `${confVal}% विश्वास स्तर`;
    }

    if (elSnippet) {
      const snip = (a.text || a.transcript || 'जांच की गई सामग्री').trim();
      elSnippet.textContent = snip.length > 280 ? snip.substring(0, 280) + '...' : snip;
    }

    if (elThreats) {
      elThreats.innerHTML = '';
      const list = a.threat_indicators || a.reasons || a.indicators || [];
      if (list.length === 0) {
        const li = document.createElement('li');
        li.textContent = isScam ? 'संदिग्ध वित्तीय दबाव या अनाधिकृत मांग' : 'कोई ज्ञात खतरा नहीं पाया गया';
        elThreats.appendChild(li);
      } else {
        list.forEach(item => {
          const li = document.createElement('li');
          li.textContent = item;
          elThreats.appendChild(li);
        });
      }
    }

    if (elAction) {
      if (isScam) {
        elAction.innerHTML = `
          <strong>नागरिक को निर्देश:</strong><br>
          1. कोई भी पैसा या UPI PIN दर्ज <strong>न करें</strong>।<br>
          2. फोन पर बात कर रहे व्यक्ति को तुरंत ब्लॉक करें।<br>
          3. यदि बिजली/बैंक का मामला हो तो स्वयं नजदीकी बिजली दफ्तर / शाखा में जाएं।<br>
          4. वित्तीय नुकसान होने पर तुरंत <strong>1930</strong> पर कॉल करें।
        `;
      } else {
        elAction.innerHTML = `
          <strong>नागरिक को निर्देश:</strong><br>
          संदेश में कोई प्रत्यक्ष वित्तीय धोखाधड़ी नहीं पाई गई। फिर भी किसी अनजान व्यक्ति को अपना OTP, बैंक पासवर्ड या ATM कार्ड नंबर कभी न बताएं।
        `;
      }
    }

    // Save to Offline Log
    this.saveIncidentToLog({
      refId,
      timestamp: dateStr,
      type: a.scam_type || a.category || 'Message/SMS',
      risk: isScam ? 'SCAM' : 'SAFE',
      confidence: Math.round((a.confidence || 0.85) * 100) + '%'
    });

    // Open Modal
    const modal = document.getElementById('advisoryReceiptModalOverlay');
    if (modal) {
      modal.classList.add('open');
    }
  },

  closeReceiptModal() {
    const modal = document.getElementById('advisoryReceiptModalOverlay');
    if (modal) {
      modal.classList.remove('open');
    }
  },

  downloadReceiptText() {
    const a = this.lastAssessment;
    if (!a) return;

    const refId = a.refId || 'JS-CG-UNKNOWN';
    const isScam = a.is_scam !== undefined ? a.is_scam : true;

    const text = `=====================================================
छत्तीसगढ़ शासन • जन सुरक्षा नागरिक साइबर परामर्श पावती
GOVT OF CHHATTISGARH — CITIZEN CYBER ADVISORY SLIP
=====================================================
पावती संदर्भ क्रमांक (Ref ID) : ${refId}
दिनांक व समय (Date/Time)       : ${new Date().toLocaleString('hi-IN')}
जांच केंद्र / CSC चॉइस सेंटर   : ग्राम पंचायत कियोस्क (Assisted Mode)

[जांच परिणाम / EVALUATION RESULT]
जोखिम मूल्यांकन (Risk Level)   : ${isScam ? 'सावधान! वित्तीय धोखाधड़ी का खतरा (HIGH RISK SCAM)' : 'सुरक्षित (SAFE)'}
श्रेणी (Category)             : ${a.scam_type || 'संदिग्ध संदेश'}
विश्वास स्तर (Confidence)      : ${Math.round((a.confidence || 0.85) * 100)}%

[जांच किया गया विवरण / ANALYZED CONTENT]
"${(a.text || a.transcript || '').substring(0, 300)}"

[नागरिक को परामर्श व सावधानियां]
1. किसी भी अनजान व्यक्ति को OTP, UPI PIN या बैंक विवरण न दें।
2. बिजली बिल या बैंक खाते से संबंधित कॉल आने पर सीधे आधिकारिक कार्यालय जाएं।
3. साइबर ठगी होने पर तुरंत राष्ट्रीय हेल्पलाइन 1930 डायल करें।
4. औपचारिक ऑनलाइन शिकायत: https://cybercrime.gov.in

जारीकर्ता: जन सुरक्षा (Jan Suraksha) — छत्तीसगढ़ शासन
=====================================================`;

    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `JanSuraksha_Receipt_${refId}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    if (window.App) window.App.showToast('पावती (.txt) डाउनलोड हो गई');
  },

  saveIncidentToLog(incident) {
    try {
      const logs = JSON.parse(localStorage.getItem('suraksha_kiosk_log') || '[]');
      logs.unshift(incident);
      if (logs.length > 50) logs.pop(); // keep latest 50
      localStorage.setItem('suraksha_kiosk_log', JSON.stringify(logs));
      this.updateIncidentCounter();
    } catch (e) {
      console.warn('Could not save incident to local log:', e);
    }
  },

  updateIncidentCounter() {
    try {
      const logs = JSON.parse(localStorage.getItem('suraksha_kiosk_log') || '[]');
      const countEl = document.getElementById('kioskIncidentCount');
      if (countEl) {
        countEl.textContent = logs.length;
      }
    } catch (e) {}
  },

  openLogModal() {
    const modal = document.getElementById('kioskLogModalOverlay');
    const tbody = document.getElementById('kioskLogTbody');
    if (!modal || !tbody) return;

    try {
      const logs = JSON.parse(localStorage.getItem('suraksha_kiosk_log') || '[]');
      tbody.innerHTML = '';

      if (logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 24px; color: var(--text-muted);">कोई पूर्व परामर्श रिकॉर्ड नहीं मिला।</td></tr>';
      } else {
        logs.forEach(item => {
          const tr = document.createElement('tr');
          const isScam = item.risk === 'SCAM';
          tr.innerHTML = `
            <td style="padding: 10px 12px; font-family: monospace; font-weight: 700;">${item.refId}</td>
            <td style="padding: 10px 12px; font-size: 0.85rem;">${item.timestamp}</td>
            <td style="padding: 10px 12px;">${item.type}</td>
            <td style="padding: 10px 12px;"><span class="badge ${isScam ? 'badge-danger' : 'badge-success'}" style="font-size:0.75rem; padding: 2px 8px; border-radius: 4px; font-weight:700;">${item.risk}</span></td>
            <td style="padding: 10px 12px; font-size: 0.85rem;">${item.confidence}</td>
          `;
          tbody.appendChild(tr);
        });
      }

      modal.classList.add('open');
    } catch (e) {
      console.error('Error opening kiosk log:', e);
    }
  },

  closeLogModal() {
    const modal = document.getElementById('kioskLogModalOverlay');
    if (modal) {
      modal.classList.remove('open');
    }
  },

  exportLogCsv() {
    try {
      const logs = JSON.parse(localStorage.getItem('suraksha_kiosk_log') || '[]');
      if (logs.length === 0) {
        if (window.App) window.App.showToast('निर्यात के लिए कोई रिकॉर्ड नहीं है');
        return;
      }

      let csv = 'Ref_ID,Date_Time,Scam_Type,Risk_Level,Confidence\n';
      logs.forEach(l => {
        csv += `"${l.refId}","${l.timestamp}","${l.type}","${l.risk}","${l.confidence}"\n`;
      });

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `JanSuraksha_Kiosk_Log_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      if (window.App) window.App.showToast('CSV रिपोर्ट डाउनलोड हो गई');
    } catch (e) {
      console.error('CSV export failed:', e);
    }
  },

  clearLog() {
    if (confirm('क्या आप सभी परामर्श रिकॉर्ड हटाना चाहते हैं?')) {
      localStorage.removeItem('suraksha_kiosk_log');
      this.updateIncidentCounter();
      this.openLogModal();
      if (window.App) window.App.showToast('रिकॉर्ड सफलतापूर्वक हटा दिए गए');
    }
  }
};
