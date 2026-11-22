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
      console.warn('QR image upload check failed:', err);
      if (window.App) window.App.showToast('QR कोड जांचने में समस्या आई (Offline error)');
    }
  },

  async analyzeUpiString(upiStr) {
    const formData = new FormData();
    formData.append('upi_string', upiStr);
    formData.append('language', I18n.currentLang || 'hi');

    try {
      const res = await fetch('/api/detect/qr', { method: 'POST', body: formData });
      const data = await res.json();
      this.renderQrVerdict(data);
    } catch (err) {
      console.warn('QR check failed:', err);
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
          <button class="btn btn-secondary" onclick="window.speechSynthesis.speak(new SpeechSynthesisUtterance('${data.explanation}'))">
            <svg viewBox="0 0 24 24"><use href="#icon-volume"/></svg>
            बोलकर सुनाएं
          </button>
          <button class="btn btn-accent" onclick="window.ReportsManager.openModal('${pa}')">
            <svg viewBox="0 0 24 24"><use href="#icon-alert-triangle"/></svg>
            इस UPI को रिपोर्ट करें
          </button>
        </div>
      </div>
    `;

    box.classList.add('show');
    box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
};
