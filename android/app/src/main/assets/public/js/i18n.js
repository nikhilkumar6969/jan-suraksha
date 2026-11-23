// Suraksha i18n Localization Engine (Offline-First, Full-Page Translation)
const I18n = {
  currentLang: 'hi',
  translations: {},

  async init() {
    const saved = localStorage.getItem('suraksha_lang');
    if (saved && ['en', 'hi', 'chg'].includes(saved)) {
      this.currentLang = saved;
    }
    const sel = document.getElementById('langSelector');
    if (sel) {
      sel.value = this.currentLang;
      sel.addEventListener('change', (e) => this.setLanguage(e.target.value));
    }

    // Preload all 3 locales so offline language switching is instantaneous & never fails
    await Promise.all([
      this.loadTranslations('hi'),
      this.loadTranslations('en'),
      this.loadTranslations('chg')
    ]);

    this.applyTranslations();
  },

  async loadTranslations(lang) {
    if (this.translations[lang]) return;
    try {
      const res = await fetch(`/locales/${lang}.json`);
      if (res.ok) {
        this.translations[lang] = await res.json();
      }
    } catch (err) {
      console.warn(`Offline mode: unable to fetch /locales/${lang}.json`, err);
    }
  },

  async setLanguage(lang) {
    if (!['en', 'hi', 'chg'].includes(lang)) return;
    this.currentLang = lang;
    localStorage.setItem('suraksha_lang', lang);

    if (!this.translations[lang]) {
      await this.loadTranslations(lang);
    }

    this.applyTranslations();
    document.documentElement.lang = (lang === 'en') ? 'en' : 'hi';

    // Dispatch event so sub-modules (Dashboard, Quiz, Checklist, Call) reactively re-render
    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
  },

  t(key, defaultVal = '') {
    const dict = this.translations[this.currentLang] || {};
    return dict[key] || defaultVal || key;
  },

  applyTranslations() {
    const dict = this.translations[this.currentLang] || {};

    // 1. Text elements
    document.querySelectorAll('[data-i18n]').forEach((el) => {
      const key = el.getAttribute('data-i18n');
      if (!dict[key]) return;

      const svg = el.querySelector('svg');
      if (svg) {
        // Protect SVG icons inside buttons or headers
        const textSpan = el.querySelector('.i18n-text');
        if (textSpan) {
          textSpan.textContent = dict[key];
        } else {
          // Preserve SVG and update text node
          const clonedSvg = svg.cloneNode(true);
          el.innerHTML = '';
          el.appendChild(clonedSvg);
          el.appendChild(document.createTextNode(' ' + dict[key]));
        }
      } else {
        el.textContent = dict[key];
      }
    });

    // 2. Attribute elements (placeholder, title, aria-label)
    document.querySelectorAll('[data-i18n-attr]').forEach((el) => {
      const attrMapping = el.getAttribute('data-i18n-attr');
      if (!attrMapping) return;
      const [attr, key] = attrMapping.split(':');
      if (dict[key]) {
        el.setAttribute(attr, dict[key]);
      }
    });
  }
};

window.I18n = I18n;
