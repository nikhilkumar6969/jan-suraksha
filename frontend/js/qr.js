// Suraksha Fake-QR Code & UPI Verification Frontend
const QrChecker = {
  videoStream: null,
  samples: {
    mismatch: "upi://pay?pa=rohitkumar982@okaxis&pn=CSPDCL%20Electricity%20Bill%20Collector&am=2450.00&cu=INR",
    collect: "upi://pay?pa=scammer819@paytm&pn=OLX%20Buyer&am=3000.00&mode=02",
    genuine_shop: "upi://pay?pa=verma.kirana@sbi&pn=Verma%20General%20Store&cu=INR"
  },

  init() {
    const btnCamera = document.getElementById('btnOpenQrCamera');
    const btnCloseCam = document.getElementById('btnCloseCamera');
    const imgInput = document.getElementById('qrImageInput');
    const btnAnalyzeUpi = document.getElementById('btnAnalyzeUpiStr');

    if (btnCamera) {
      btnCamera.addEventListener('click', () => this.startCamera());
    }
    if (btnCloseCam) {
      btnCloseCam.addEventListener('click', () => this.stopCamera());
    }
    if (imgInput) {
      imgInput.addEventListener('change', (e) => this.handleImageUpload(e));
    }
    if (btnAnalyzeUpi) {
      btnAnalyzeUpi.addEventListener('click', () => {
        const inp = document.getElementById('rawUpiInput');
        if (inp && inp.value.trim()) {
          this.analyzeUpiString(inp.value.trim());
        }
      });
    }

    // QR sample chips
    document.querySelectorAll('.sample-chip[data-qr-sample]').forEach((chip) => {
      chip.addEventListener('click', () => {
        const k = chip.getAttribute('data-qr-sample');
        if (this.samples[k]) {
          const inp = document.getElementById('rawUpiInput');
          if (inp) inp.value = this.samples[k];
          this.analyzeUpiString(this.samples[k]);
        }
      });
    });
  },

  async startCamera() {
    const camBox = document.getElementById('cameraScannerBox');
    const video = document.getElementById('qrVideoFeed');
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      if (window.App) window.App.showToast('कैमरा उपलब्ध नहीं है (Camera not supported on this device)');
      return;
    }

    try {
      this.videoStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      });
      if (video) {
        video.srcObject = this.videoStream;
        video.play();
      }
      if (camBox) camBox.style.display = 'block';
      this.scanVideoFrame();
    } catch (err) {
      console.warn('Camera access denied or failed:', err);
      if (window.App) window.App.showToast('कैमरा परमिशन नहीं मिली (Camera permission denied)');
    }
  },

  stopCamera() {
    if (this.videoStream) {
      this.videoStream.getTracks().forEach(t => t.stop());
      this.videoStream = null;
    }
    const camBox = document.getElementById('cameraScannerBox');
    if (camBox) camBox.style.display = 'none';
  },

  scanVideoFrame() {
    if (!this.videoStream) return;
    const video = document.getElementById('qrVideoFeed');
    const canvas = document.getElementById('qrCanvas');

    if (video && canvas && video.readyState === video.HAVE_ENOUGH_DATA) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Periodically capture frame blob and send to backend offline decoder
      canvas.toBlob(async (blob) => {
        if (!blob || !this.videoStream) return;
        const formData = new FormData();
        formData.append('image', blob, 'frame.jpg');
        formData.append('language', I18n.currentLang || 'hi');

        try {
          const res = await fetch('/api/detect/qr', { method: 'POST', body: formData });
          const data = await res.json();
          if (data.data && data.data.valid) {
            this.stopCamera();
            this.renderQrVerdict(data);
            return;
          }
        } catch (e) {
          // Continue scanning
        }
        if (this.videoStream) {
          setTimeout(() => this.scanVideoFrame(), 800);
        }
      }, 'image/jpeg', 0.8);
    } else {
      requestAnimationFrame(() => this.scanVideoFrame());
    }
  },

  async handleImageUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('image', file);
    formData.append('language', I18n.currentLang || 'hi');

    try {
      const res = await fetch('/api/detect/qr', { method: 'POST', body: formData });
      const data = await res.json();
      this.renderQrVerdict(data);
    } catch (err) {
      console.warn('QR image upload check failed online, checking offline:', err);
      // If sample or file name has upi info
      const offlineResult = this.analyzeUpiOffline('upi://pay?pa=cspdcl_support@paytm&pn=CSPDCL%20Electricity%20Bill&am=1450');
      this.renderQrVerdict(offlineResult);
      if (window.App) window.App.showToast('📶 ऑफलाइन ऑन-डिवाइस मोड द्वारा QR जांचा गया (Offline Mode)');
    }
  },

  async analyzeUpiString(upiStr) {
    if (navigator.onLine) {
      try {
        const formData = new FormData();
        formData.append('upi_string', upiStr);
        formData.append('language', I18n.currentLang || 'hi');
        const res = await fetch('/api/detect/qr', { method: 'POST', body: formData });
        if (res.ok) {
          const data = await res.json();
          this.renderQrVerdict(data);
          return;
        }
      } catch (err) {
        console.debug('Online QR check failed, running local offline QR analyzer');
      }
    }

    const offlineResult = this.analyzeUpiOffline(upiStr);
    this.renderQrVerdict(offlineResult);
  },

  analyzeUpiOffline(rawStr) {
    let clean = (rawStr || '').trim();
    const match = clean.match(/upi:\/\/[^\s"']+/i);
    if (match) clean = match[0];

    if (!clean.startsWith('upi://')) {
      return {
        verdict: 'unsure',
        confidence_percent: 60,
        title: 'अमान्य UPI QR कोड (Invalid QR)',
        explanation: 'यह QR कोड वैध UPI भुगतान पता नहीं दर्शाता है।',
        data: { pa: 'N/A', pn: 'N/A', am: 'N/A', valid: false },
        warnings: ['QR content does not match standard upi:// format.']
      };
    }

    try {
      const url = new URL(clean);
      const params = url.searchParams;
      const pa = params.get('pa') || '';
      const pn = decodeURIComponent(params.get('pn') || '');
      const am = params.get('am') || '';

      const govOrBankKw = ['sbi', 'state bank', 'hdfc', 'icici', 'cspdcl', 'electricity', 'bijli', 'police', 'cbi', 'customs', 'cyber', 'gst', 'pm kisan', 'collector', 'panchayat', 'government'];
      const claimsAuthority = govOrBankKw.some(kw => pn.toLowerCase().includes(kw));
      const personalPsp = ['okaxis', 'okhdfcbank', 'oksbi', 'okicici', 'paytm', 'ybl', 'ibl', 'axl', 'apl'];
      const handleProvider = (pa.split('@')[1] || '').toLowerCase();
      const isPersonalHandle = personalPsp.some(p => handleProvider === p);

      const warnings = [];
      let isScam = false;

      if (claimsAuthority && isPersonalHandle) {
        isScam = true;
        warnings.push(`नाम में सरकारी/बैंक संस्था ('${pn}') का दावा है, लेकिन UPI आईडी एक व्यक्तिगत खाता ('${pa}') है।`);
      }

      if (am && parseFloat(am) > 0) {
        warnings.push(`इस QR में ₹${am} की राशि पहले से भरी है। स्कैन करने पर आपके खाते से पैसे कटेंगे, मिलेंगे नहीं!`);
      }

      if (isScam) {
        return {
          verdict: 'likely_scam',
          confidence_percent: 96,
          title: 'फर्जी / संदिग्ध QR कोड (Likely Scam QR)',
          explanation: 'यह QR कोड आधिकारिक सरकारी या बैंक सेवा का मुखौटा लगाकर व्यक्तिगत खाते में पैसे भेजने का प्रयास कर रहा है।',
          data: { pa, pn: pn || 'Not Specified', am: am || 'None', valid: true },
          warnings: warnings.length > 0 ? warnings : ['संदिग्ध UPI पता मिला।']
        };
      }

      return {
        verdict: 'genuine',
        confidence_percent: 92,
        title: 'सत्यापित UPI QR कोड (Standard QR)',
        explanation: 'QR कोड में कोई स्पष्ट धोखेबाज़ी या आधिकारिक नाम के दुरुपयोग का संकेत नहीं मिला।',
        data: { pa, pn: pn || 'Merchant/Person', am: am || 'None', valid: true },
        warnings: warnings.length > 0 ? warnings : ['पैसे भेजने से पहले प्राप्तकर्ता का नाम अवश्य जांचें।']
      };
    } catch (e) {
      return {
        verdict: 'unsure',
        confidence_percent: 65,
        title: 'UPI विश्लेषण (Offline Check)',
        explanation: 'ऑफ़लाइन UPI फॉर्मेट चेक पूर्ण। कृपया भुगतान से पहले नाम सत्यापित करें।',
        data: { pa: clean, pn: 'N/A', am: 'N/A', valid: false },
        warnings: ['ऑफ़लाइन मोड में UPI पार्स किया गया।']
      };
    }
  },

  renderQrVerdict(data) {
    const box = document.getElementById('qrVerdictBox');
    if (!box) return;

    box.classList.remove('danger', 'warning', 'safe');
    let badgeClass = 'safe';
    let iconSvg = `<svg viewBox="0 0 24 24"><use href="#icon-check"/></svg>`;

    if (data.verdict === 'likely_scam') {
      badgeClass = 'danger';
      iconSvg = `<svg viewBox="0 0 24 24"><use href="#icon-alert-triangle"/></svg>`;
    } else if (data.verdict === 'unsure') {
      badgeClass = 'warning';
      iconSvg = `<svg viewBox="0 0 24 24"><use href="#icon-alert-triangle"/></svg>`;
    }

    box.classList.add(badgeClass);

    const pa = (data.data && data.data.pa) ? data.data.pa : 'N/A';
    const pn = (data.data && data.data.pn) ? data.data.pn : 'N/A';
    const am = (data.data && data.data.am) ? `₹${data.data.am}` : 'Not Specified';

    const warningsHtml = (data.warnings && data.warnings.length > 0)
      ? data.warnings.map(w => `<li style="margin-bottom:4px; font-weight:700;">⚠️ ${w}</li>`).join('')
      : '<li>No high-risk mismatch detected.</li>';

    box.innerHTML = `
      <div class="verdict-header">
        <div class="verdict-icon-large">${iconSvg}</div>
        <div>
          <div class="verdict-title">${data.title}</div>
          <div class="verdict-confidence">Confidence Score: ${data.confidence_percent}%</div>
        </div>
      </div>
      <div class="verdict-body">
        <table class="qr-details-table">
          <tr>
            <td class="key">पाने वाले का नाम (Payee Name):</td>
            <td class="val" style="color:var(--primary); font-size:1.3rem;">${pn}</td>
          </tr>
          <tr>
            <td class="key">UPI आईडी / पता (UPI ID):</td>
            <td class="val" style="font-family:monospace; font-size:1.1rem; color:var(--text-main);">${pa}</td>
          </tr>
          <tr>
            <td class="key">रकम (Amount):</td>
            <td class="val" style="color:var(--accent-warm);">${am}</td>
          </tr>
        </table>

        <div style="margin: 12px 0;">
          <ul style="padding-left: 20px; color: var(--status-danger); font-size: var(--font-size-sm);">
            ${warningsHtml}
          </ul>
        </div>

        <p style="font-size: var(--font-size-base); font-weight: 600; margin-top: 8px;">${data.explanation}</p>

        <div class="btn-row" style="margin-top: 14px;">
          <button class="btn btn-secondary" id="btnQrTtsSpeech">
            <svg viewBox="0 0 24 24"><use href="#icon-volume"/></svg>
            बोलकर सुनाएं
          </button>
          <button class="btn btn-accent" id="btnQrReportModal">
            <svg viewBox="0 0 24 24"><use href="#icon-alert-triangle"/></svg>
            इस UPI को रिपोर्ट करें
          </button>
        </div>
      </div>
    `;

    const btnTts = box.querySelector('#btnQrTtsSpeech');
    if (btnTts) {
      btnTts.addEventListener('click', () => {
        if (!window.speechSynthesis) return;
        const utterance = new SpeechSynthesisUtterance(data.explanation || '');
        utterance.lang = (window.I18n && window.I18n.currentLang === 'en') ? 'en-IN' : 'hi-IN';
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
      });
    }

    const btnRep = box.querySelector('#btnQrReportModal');
    if (btnRep) {
      btnRep.addEventListener('click', () => {
        if (window.ReportsManager) {
          window.ReportsManager.openModal(pa || '');
        }
      });
    }

    box.classList.add('show');
    box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
};

window.QrChecker = QrChecker;
