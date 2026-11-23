// Suraksha Master App Controller
window.App = {
  currentView: 'home',

  async init() {
    // 1. Initialize i18n
    await I18n.init();

    // 2. Initialize Subsystems
    MessageDetector.init();
    QrChecker.init();
    CallDetector.init();
    LearnManager.init();
    HelpManager.init();
    ReportsManager.init();
    DashboardManager.init();
    CryptoVerifyManager.init();
    if (window.HeroSlider) {
      window.HeroSlider.init();
    }

    // 3. Setup Navigation
    this.setupNavigation();

    // 4. Setup 1930 Emergency Helpline Modal (Laptop & Desktop Fix)
    this.setupHelplineModal();

    // 5. Setup Theme Toggle
    this.setupTheme();

    // 6. Setup Network Status Monitoring
    this.setupNetworkStatus();

    // 7. Register Service Worker
    this.registerServiceWorker();

    // 8. Load Evaluation Metrics
    this.loadEvaluationMetrics();
  },

  setupNavigation() {
    // Desktop nav
    document.querySelectorAll('.desktop-nav .desktop-nav-link').forEach((item) => {
      item.addEventListener('click', () => {
        const targetView = item.getAttribute('data-nav');
        this.navigate(targetView);
      });
    });

    // Bottom nav
    document.querySelectorAll('.bottom-nav .nav-item').forEach((item) => {
      item.addEventListener('click', () => {
        const targetView = item.getAttribute('data-nav');
        this.navigate(targetView);
      });
    });

    // Home action tiles navigation
    document.querySelectorAll('.action-tile[data-nav]').forEach((tile) => {
      tile.addEventListener('click', () => {
        const targetView = tile.getAttribute('data-nav');
        const subtab = tile.getAttribute('data-subtab');
        this.navigate(targetView);
        if (subtab) {
          this.switchSubtab(`subtab-${subtab}`);
        }
      });
    });

    // Brand logo returns home
    const brandHome = document.getElementById('brandHomeLink');
    if (brandHome) {
      brandHome.addEventListener('click', (e) => {
        e.preventDefault();
        this.navigate('home');
      });
    }

    // Emergency red card triggers help view
    const emgCard = document.getElementById('homeEmergencyCard');
    if (emgCard) {
      emgCard.addEventListener('click', (e) => {
        if (!e.target.closest('a')) {
          this.navigate('help');
        }
      });
    }

    // Subtabs inside Check view
    document.querySelectorAll('.subtab-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const target = btn.getAttribute('data-target');
        this.switchSubtab(target);
      });
    });

    // Quick Fraud Search in Header (MyGov Search)
    const searchForm = document.getElementById('headerSearchForm');
    const searchInput = document.getElementById('headerSearchInput');
    if (searchForm && searchInput) {
      searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const val = searchInput.value.trim();
        if (!val) return;
        this.navigate('check');
        this.switchSubtab('subtab-sms');
        const scamInput = document.getElementById('smsInput') || document.getElementById('scamTextInput');
        if (scamInput) {
          scamInput.value = val;
          const btn = document.getElementById('btnAnalyzeSms') || document.getElementById('btnAnalyzeScam');
          if (btn) btn.click();
        }
      });
    }

    // Floating Civic Dock buttons
    const flReport = document.getElementById('floatingReportBtn');
    if (flReport) {
      flReport.addEventListener('click', () => {
        if (window.ReportsManager) ReportsManager.openModal();
      });
    }
    const flTop = document.getElementById('floatingScrollTopBtn');
    if (flTop) {
      flTop.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }

    // Accessibility Font Size Controls
    const a11yDec = document.getElementById('btnA11yDecrease');
    const a11yReset = document.getElementById('btnA11yReset');
    const a11yInc = document.getElementById('btnA11yIncrease');
    const setA11ySize = (size, activeBtn) => {
      document.documentElement.setAttribute('data-a11y-size', size);
      localStorage.setItem('suraksha_a11y_size', size);
      [a11yDec, a11yReset, a11yInc].forEach(b => b && b.classList.remove('active'));
      if (activeBtn) activeBtn.classList.add('active');
    };
    if (a11yDec) a11yDec.addEventListener('click', () => setA11ySize('small', a11yDec));
    if (a11yReset) a11yReset.addEventListener('click', () => setA11ySize('normal', a11yReset));
    if (a11yInc) a11yInc.addEventListener('click', () => setA11ySize('large', a11yInc));

    const savedSize = localStorage.getItem('suraksha_a11y_size') || 'normal';
    if (savedSize === 'small' && a11yDec) setA11ySize('small', a11yDec);
    else if (savedSize === 'large' && a11yInc) setA11ySize('large', a11yInc);
  },

  setupHelplineModal() {
    const modal = document.getElementById('helpline1930ModalOverlay');
    const btnClose = document.getElementById('btnClose1930Modal');
    const btnCopy = document.getElementById('btnCopy1930Number');
    const copyText = document.getElementById('copy1930BtnText');
    const btnChecklist = document.getElementById('btnModalOpenChecklist');
    const btnTryPcCall = document.getElementById('btnModalTryPcCall');

    const openModal = () => {
      if (modal) modal.classList.add('open');
    };

    const closeModal = () => {
      if (modal) modal.classList.remove('open');
    };

    this.open1930Modal = openModal;
    this.close1930Modal = closeModal;

    // Detect if the user is on mobile
    const isMobileDevice = () => {
      return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
             (window.matchMedia && window.matchMedia('(max-width: 768px) and (pointer: coarse)').matches);
    };

    // Attach to all tel:1930 links
    document.querySelectorAll('a[href="tel:1930"]').forEach((link) => {
      link.addEventListener('click', (e) => {
        // On laptop/desktop, tel: links don't dial naturally -> always show the helpful emergency guidance modal!
        if (!isMobileDevice()) {
          e.preventDefault();
          openModal();
        }
      });
    });

    if (btnClose) {
      btnClose.addEventListener('click', closeModal);
    }

    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
      });
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modal && modal.classList.contains('open')) {
        closeModal();
      }
    });

    // Copy number action
    if (btnCopy) {
      btnCopy.addEventListener('click', async () => {
        try {
          if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText('1930');
          } else {
            const ta = document.createElement('textarea');
            ta.value = '1930';
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
          }
          const copiedLabel = window.I18n ? window.I18n.t('helpline_modal_copied', '✓ Copied!') : '✓ Copied!';
          const defaultLabel = window.I18n ? window.I18n.t('helpline_modal_copy_btn', 'Copy Number') : 'Copy Number';
          const toastMsg = window.I18n ? window.I18n.t('helpline_modal_toast_copied', '✓ 1930 copied to clipboard') : '✓ 1930 copied to clipboard';

          if (copyText) copyText.textContent = copiedLabel;
          this.showToast(toastMsg);
          setTimeout(() => {
            if (copyText) copyText.textContent = defaultLabel;
          }, 2500);
        } catch (err) {
          console.warn('Clipboard write failed:', err);
          this.showToast('1930 डायल करें');
        }
      });
    }

    // Open checklist action
    if (btnChecklist) {
      btnChecklist.addEventListener('click', () => {
        closeModal();
        this.navigate('help');
      });
    }

    // Try PC Call action
    if (btnTryPcCall) {
      btnTryPcCall.addEventListener('click', () => {
        window.location.href = 'tel:1930';
      });
    }
  },

  navigate(viewName) {
    this.currentView = viewName;
    document.querySelectorAll('.view-panel').forEach((panel) => {
      panel.classList.remove('active');
    });

    const activePanel = document.getElementById(`view-${viewName}`);
    if (activePanel) {
      activePanel.classList.add('active');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Update bottom nav active state
    document.querySelectorAll('.bottom-nav .nav-item').forEach((btn) => {
      btn.classList.toggle('active', btn.getAttribute('data-nav') === viewName);
    });

    // Update desktop nav active state
    document.querySelectorAll('.desktop-nav .desktop-nav-link').forEach((btn) => {
      btn.classList.toggle('active', btn.getAttribute('data-nav') === viewName);
    });

    if (viewName === 'insights') {
      DashboardManager.loadDashboardData();
    } else if (viewName === 'eval') {
      this.loadEvaluationMetrics();
    }
  },

  switchSubtab(subtabId) {
    document.querySelectorAll('.subtab-btn').forEach((b) => {
      b.classList.remove('active');
      b.setAttribute('aria-selected', 'false');
      if (b.getAttribute('data-target') === subtabId) {
        b.classList.add('active');
        b.setAttribute('aria-selected', 'true');
      }
    });

    document.querySelectorAll('.subtab-content').forEach((content) => {
      content.style.display = 'none';
    });

    const activeContent = document.getElementById(subtabId);
    if (activeContent) {
      activeContent.style.display = 'block';
    }
  },

  setupTheme() {
    const savedTheme = localStorage.getItem('suraksha_theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);

    const toggleBtn = document.getElementById('themeToggleBtn');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        const cur = document.documentElement.getAttribute('data-theme');
        const next = cur === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('suraksha_theme', next);
      });
    }
  },

  setupNetworkStatus() {
    const badge = document.getElementById('netStatusBadge');
    const text = document.getElementById('netStatusText');

    const updateStatus = () => {
      const isOnline = navigator.onLine;
      if (badge && text) {
        if (isOnline) {
          badge.classList.remove('offline');
          text.textContent = I18n.t('working_online', 'ऑनलाइन');
        } else {
          badge.classList.add('offline');
          text.textContent = I18n.t('working_offline', 'ऑफलाइन');
        }
      }
    };

    window.addEventListener('online', () => {
      updateStatus();
      this.showToast('🟢 ऑनलाइन जुड़ गए (Connected to Network)');
    });

    window.addEventListener('offline', () => {
      updateStatus();
      this.showToast('📶 ऑफलाइन मोड सक्रिय (Working completely offline)');
    });

    updateStatus();
  },

  registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').then((reg) => {
        console.log('[Suraksha] ServiceWorker registered successfully:', reg.scope);
      }).catch((err) => {
        console.warn('[Suraksha] ServiceWorker registration failed:', err);
      });
    }
  },

  showToast(msg) {
    const toast = document.getElementById('appToast');
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add('show');
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => {
      toast.classList.remove('show');
    }, 3200);
  },

  async loadEvaluationMetrics() {
    try {
      const res = await fetch('/api/evaluation/metrics');
      if (!res.ok) return;
      const data = await res.json();
      const o = data.overall;

      const accEl = document.getElementById('evalAcc');
      const precEl = document.getElementById('evalPrec');
      const recEl = document.getElementById('evalRec');
      const f1El = document.getElementById('evalF1');
      const fprEl = document.getElementById('evalFPR');

      if (accEl) accEl.textContent = `${(o.accuracy * 100).toFixed(1)}%`;
      if (precEl) precEl.textContent = `${(o.precision * 100).toFixed(1)}%`;
      if (recEl) recEl.textContent = `${(o.recall * 100).toFixed(1)}%`;
      if (f1El) f1El.textContent = `${(o.f1 * 100).toFixed(1)}%`;
      if (fprEl) fprEl.textContent = `${(o.false_positive_rate * 100).toFixed(1)}%`;

      // Language table
      const tbody = document.getElementById('evalLangTbody');
      if (tbody && data.per_language) {
        tbody.innerHTML = '';
        for (const [lang, m] of Object.entries(data.per_language)) {
          const row = document.createElement('tr');
          row.style.borderBottom = '1px solid var(--border-color)';
          row.innerHTML = `
            <td style="padding:8px; font-weight:700;">${lang.toUpperCase()}</td>
            <td style="padding:8px;">${m.sample_count}</td>
            <td style="padding:8px; color:var(--status-safe); font-weight:700;">${(m.accuracy * 100).toFixed(1)}%</td>
            <td style="padding:8px;">${(m.precision * 100).toFixed(1)}%</td>
            <td style="padding:8px;">${(m.recall * 100).toFixed(1)}%</td>
            <td style="padding:8px;">${(m.f1 * 100).toFixed(1)}%</td>
            <td style="padding:8px; color:var(--status-danger);">${(m.false_positive_rate * 100).toFixed(1)}%</td>
          `;
          tbody.appendChild(row);
        }
      }

      // Confusion matrix box
      const cmBox = document.getElementById('confusionMatrixBox');
      if (cmBox && o.confusion_matrix) {
        const cm = o.confusion_matrix;
        cmBox.innerHTML = `
          <div style="display:inline-block; border:1px solid var(--border-color); padding:10px; border-radius:8px; background:var(--bg-card-subtle);">
            <div><strong>True Negative (Genuine recognized):</strong> ${cm.tn}</div>
            <div><strong>False Positive (False Alarm on Genuine):</strong> ${cm.fp}</div>
            <div><strong>False Negative (Missed Scams):</strong> ${cm.fn}</div>
            <div><strong>True Positive (Scams Detected):</strong> ${cm.tp}</div>
          </div>
        `;
      }
    } catch (e) {
      console.warn('Could not load evaluation metrics offline:', e);
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  window.App.init();
});
