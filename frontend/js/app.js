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

    // 3. Setup Navigation
    this.setupNavigation();

    // 4. Setup Theme Toggle
    this.setupTheme();

    // 5. Setup Network Status Monitoring
    this.setupNetworkStatus();

    // 6. Register Service Worker
    this.registerServiceWorker();

    // 7. Load Evaluation Metrics
    this.loadEvaluationMetrics();
  },

  setupNavigation() {
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
      if (btn.getAttribute('data-nav') === viewName) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
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
