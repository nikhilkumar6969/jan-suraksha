// Suraksha Official Help & Evidence Checklist Frontend
const HelpManager = {
  storageKey: 'suraksha_evidence_checklist',

  init() {
    this.loadChecklistState();

    const btnSave = document.getElementById('btnSaveChecklist');
    const btnPrint = document.getElementById('btnPrintChecklist');

    if (btnSave) {
      btnSave.addEventListener('click', () => this.saveChecklistState());
    }
    if (btnPrint) {
      btnPrint.addEventListener('click', () => this.printOrDownloadSummary());
    }

    // Notice for offline status on external links
    document.querySelectorAll('.ext-link').forEach((link) => {
      link.addEventListener('click', (e) => {
        if (!navigator.onLine) {
          e.preventDefault();
          if (window.App) {
            window.App.showToast('यह लिंक खोलने के लिए इंटरनेट आवश्यक है (Needs Internet Connection)');
          }
        }
      });
    });
  },

  loadChecklistState() {
    try {
      const data = JSON.parse(localStorage.getItem(this.storageKey) || '{}');
      document.querySelectorAll('.checklist-checkbox').forEach((chk) => {
        const key = chk.getAttribute('data-key');
        if (data[key] !== undefined) {
          chk.checked = data[key];
        }
      });
    } catch (e) {
      console.warn('Could not load checklist state:', e);
    }
  },

  saveChecklistState() {
    const data = {};
    document.querySelectorAll('.checklist-checkbox').forEach((chk) => {
      const key = chk.getAttribute('data-key');
      data[key] = chk.checked;
    });
    localStorage.setItem(this.storageKey, JSON.stringify(data));
    if (window.App) window.App.showToast('चेकलिस्ट सुरक्षित कर ली गई है (Checklist Saved)');
  },

  printOrDownloadSummary() {
    this.saveChecklistState();
    const data = JSON.parse(localStorage.getItem(this.storageKey) || '{}');
    const items = [
      { key: 'utr', label: 'Transaction ID / UTR Number' },
      { key: 'amt', label: 'Exact Amount, Date & Time' },
      { key: 'num', label: "Scammer's Phone Number" },
      { key: 'upi', label: 'Fraudulent UPI ID / Account' },
      { key: 'ss', label: 'Screenshots of Chat & SMS' },
      { key: 'stmt', label: 'Bank Statement / Passbook Copy' }
    ];

    let summaryText = `=================================================\n`;
    summaryText += `SURAKSHA (सुरक्षा) - CYBER FRAUD EVIDENCE CHECKLIST\n`;
    summaryText += `Date: ${new Date().toLocaleString()}\n`;
    summaryText += `National Cyber Crime Helpline: 1930 | Portal: cybercrime.gov.in\n`;
    summaryText += `=================================================\n\n`;

    items.forEach((item, idx) => {
      const status = data[item.key] ? '[READY]' : '[PENDING]';
      summaryText += `${idx + 1}. ${item.label}: ${status}\n`;
    });

    summaryText += `\nINSTRUCTIONS FOR CITIZEN:\n`;
    summaryText += `1. Call 1930 immediately within the first 1-2 hours of fraud.\n`;
    summaryText += `2. Provide the UTR number, your bank account details, and scammer UPI ID.\n`;
    summaryText += `3. Visit your nearest police station or cyber cell with this checklist.\n`;

    // Download as a text file
    const blob = new Blob([summaryText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Suraksha_Cyber_Evidence_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    if (window.App) window.App.showToast('साक्ष्य सारांश डाउनलोड हो गया है (Evidence Summary Downloaded)');
  }
};
