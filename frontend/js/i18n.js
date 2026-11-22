// Suraksha i18n Localization Engine
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
    await this.loadTranslations(this.currentLang);
    this.applyTranslations();
  },

  async loadTranslations(lang) {
    try {
      const res = await fetch(`/locales/${lang}.json`);
      if (res.ok) {
        this.translations[lang] = await res.json();
      } else {
        console.warn(`Could not load /locales/${lang}.json, using fallback`);
      }
    } catch (err) {
      console.warn('Offline mode or failed to fetch locale:', err);
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
    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
  },

  t(key, defaultVal = '') {
    const dict = this.translations[this.currentLang] || {};
    return dict[key] || defaultVal || key;
  },

  applyTranslations() {
    const dict = this.translations[this.currentLang] || {};
    document.querySelectorAll('[data-i18n]').forEach((el) => {
      const key = el.getAttribute('data-i18n');
      if (dict[key]) {
        el.textContent = dict[key];
      }
    });

    document.querySelectorAll('[data-i18n-attr]').forEach((el) => {
      const attrMapping = el.getAttribute('data-i18n-attr'); // e.g. "placeholder:paste_msg_placeholder"
      const [attr, key] = attrMapping.split(':');
      if (dict[key]) {
        el.setAttribute(attr, dict[key]);
      }
    });
  }
};
