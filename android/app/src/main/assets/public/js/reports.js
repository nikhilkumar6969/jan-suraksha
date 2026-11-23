// Suraksha Anonymous Reporting & Offline Queue Service
const ReportsManager = {
  queueKey: 'suraksha_offline_report_queue',
  deviceIdKey: 'suraksha_device_uuid',

  init() {
    this.ensureDeviceId();

    const openTile = document.getElementById('openReportModalTile');
    const closeBtn = document.getElementById('btnCloseReportModal');
    const submitBtn = document.getElementById('btnSubmitReportModal');

    if (openTile) openTile.addEventListener('click', () => this.openModal(''));
    if (closeBtn) closeBtn.addEventListener('click', () => this.closeModal());
    if (submitBtn) submitBtn.addEventListener('click', () => this.submitReport());

    window.addEventListener('online', () => this.syncOfflineQueue());
    this.syncOfflineQueue();
  },

  ensureDeviceId() {
    let devId = localStorage.getItem(this.deviceIdKey);
    if (!devId) {
      devId = 'dev_' + Math.random().toString(36).substring(2, 12) + '_' + Date.now().toString(36);
      localStorage.setItem(this.deviceIdKey, devId);
    }
    return devId;
  },

  openModal(prefillIndicator = '') {
    const overlay = document.getElementById('reportModalOverlay');
    const indInput = document.getElementById('modalIndicator');
    if (indInput && prefillIndicator) {
      indInput.value = prefillIndicator;
    }
    if (overlay) overlay.classList.add('open');
  },

  closeModal() {
    const overlay = document.getElementById('reportModalOverlay');
    if (overlay) overlay.classList.remove('open');
  },

  async submitReport() {
    const sType = document.getElementById('modalScamType').value;
    const district = document.getElementById('modalDistrict').value;
    const indicator = document.getElementById('modalIndicator').value.trim();
    const deviceId = this.ensureDeviceId();

    if (!indicator) {
      if (window.App) window.App.showToast('कृपया संदिग्ध नंबर या UPI पता दर्ज करें (Enter indicator)');
      return;
    }

    const payload = {
      scam_type: sType,
      district,
      indicator,
      device_id: deviceId
    };

    if (!navigator.onLine) {
      this.enqueueOfflineReport(payload);
      this.closeModal();
      if (window.App) window.App.showToast('📶 रिपोर्ट फोन में सुरक्षित है। इंटरनेट आते ही पहुंच जाएगी (Saved Offline)');
      return;
    }

    try {
      const res = await fetch('/api/reports/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      this.closeModal();
      if (data.success) {
        if (window.App) window.App.showToast('✓ गुमनाम रिपोर्ट सफलतापूर्वक दर्ज हुई (Report submitted anonymously)');
      } else {
        if (window.App) window.App.showToast(`Notice: ${data.error || 'Failed'}`);
      }
    } catch (err) {
      console.warn('Network error, enqueuing report for later sync:', err);
      this.enqueueOfflineReport(payload);
      this.closeModal();
      if (window.App) window.App.showToast('📶 रिपोर्ट फोन में सुरक्षित रख ली गई है (Queued Offline)');
    }
  },

  enqueueOfflineReport(payload) {
    const queue = JSON.parse(localStorage.getItem(this.queueKey) || '[]');
    queue.push(payload);
    localStorage.setItem(this.queueKey, JSON.stringify(queue));
  },

  async syncOfflineQueue() {
    if (!navigator.onLine) return;
    const queue = JSON.parse(localStorage.getItem(this.queueKey) || '[]');
    if (!queue.length) return;

    console.log(`[ReportsManager] Syncing ${queue.length} queued offline reports...`);
    const remaining = [];

    for (const item of queue) {
      try {
        const res = await fetch('/api/reports/submit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(item)
        });
        if (!res.ok) remaining.push(item);
      } catch (err) {
        remaining.push(item);
      }
    }

    localStorage.setItem(this.queueKey, JSON.stringify(remaining));
    if (queue.length > remaining.length) {
      console.log(`[ReportsManager] Successfully synced ${queue.length - remaining.length} reports!`);
      if (window.App) window.App.showToast(`✓ ऑफलाइन सहेजी गई ${queue.length - remaining.length} रिपोर्ट सर्वर पर दर्ज हो गई`);
    }
  }
};
