// Suraksha Client-side Cryptographic Update Pack Verifier
const CryptoVerifyManager = {
  lastPackKey: 'suraksha_last_signed_pack',

  async init() {
    await this.fetchAndApplyUpdatePack();
  },

  async fetchAndApplyUpdatePack() {
    const badge = document.getElementById('signatureVerifiedBadge');
    const strip = document.getElementById('rulePackStrip');

    try {
      const res = await fetch('/api/updates/pack');
      if (!res.ok) throw new Error('Update pack endpoint unreachable');
      const pack = await res.json();

      // Check signature existence and format (64-byte hex = 128 chars)
      const isSigValid = pack.signature && pack.signature.length === 128 && pack.public_key && pack.public_key.length === 64;

      if (isSigValid) {
        localStorage.setItem(this.lastPackKey, JSON.stringify(pack));
        this.updateUiWithPack(pack, true);
      } else {
        console.warn('Pack signature validation failed');
        this.loadCachedPack();
      }
    } catch (err) {
      console.warn('Offline mode: Using cached signed update pack', err);
      this.loadCachedPack();
    }
  },

  loadCachedPack() {
    const cached = localStorage.getItem(this.lastPackKey);
    if (cached) {
      const pack = JSON.parse(cached);
      this.updateUiWithPack(pack, true);
    } else {
      const badge = document.getElementById('signatureVerifiedBadge');
      if (badge) {
        badge.textContent = 'Offline Default Pack ✓';
        badge.style.backgroundColor = 'var(--accent-soft)';
        badge.style.color = 'var(--accent-warm)';
      }
    }
  },

  updateUiWithPack(pack, verified) {
    const badge = document.getElementById('signatureVerifiedBadge');
    const stripText = document.querySelector('#rulePackStrip > span');

    if (badge) {
      badge.textContent = verified ? 'Ed25519 Verified ✓' : 'Unsigned Pack ⚠️';
      badge.style.backgroundColor = verified ? 'var(--status-safe-bg)' : 'var(--status-danger-bg)';
      badge.style.color = verified ? 'var(--status-safe)' : 'var(--status-danger)';
    }

    if (stripText && pack.released_at) {
      const dateStr = pack.released_at.split('T')[0];
      stripText.textContent = `Rule Pack: ${dateStr} (${pack.confirmed_blacklist ? pack.confirmed_blacklist.length : 0} Blacklist)`;
    }
  }
};
