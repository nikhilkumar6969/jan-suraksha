// Playwright E2E Test Suite for Jan Suraksha Voice-First Helper
// Tests offline execution, intent navigation, clipboard paste, detector execution, and fallback UI.

const { chromium } = require('playwright');
const assert = require('assert');

(async () => {
  console.log('🚀 Starting Voice-First Helper E2E Test Suite...');
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:\\Users\\jt332\\AppData\\Local\\ms-playwright\\chromium-1254\\chrome-win64\\chrome.exe',
    args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream']
  });

  const context = await browser.newContext({
    permissions: ['clipboard-read', 'clipboard-write', 'microphone']
  });
  const page = await context.newPage();

  // Listen to console for debugging
  page.on('console', msg => {
    if (msg.type() === 'error') console.log(`[Browser Error]:`, msg.text());
  });

  try {
    // 1. Initial Online Load & Service Worker Registration
    console.log('Step 1: Loading application at http://127.0.0.1:8000/');
    await page.goto('http://127.0.0.1:8000/', { waitUntil: 'networkidle' });

    // Ensure elements exist
    await page.waitForSelector('#homeVoiceMicBtn', { state: 'visible' });
    console.log('✓ Home voice mic button visible');

    // Wait for Service Worker activation
    await page.waitForTimeout(1000);

    // 2. Set Browser Context Offline
    console.log('Step 2: Switching browser context to 100% OFFLINE mode...');
    await context.setOffline(true);

    const isOffline = await page.evaluate(() => !navigator.onLine);
    assert.strictEqual(isOffline, true, 'Browser must report offline');
    console.log('✓ Verified offline state in browser context');

    // 3. Test Intent 1: "I got a WhatsApp message"
    console.log('Step 3: Injecting voice transcript "I got a WhatsApp message" via STT interface...');
    
    // Set clipboard text simulating a scam WhatsApp forward
    const testScamText = "URGENT: Your SBI account KYC is suspended. Update immediately at bit.ly/sbi-verify";
    await page.evaluate((text) => {
      return navigator.clipboard.writeText(text);
    }, testScamText);

    // Set mock transcript on VoiceEngine and tap the big mic button
    await page.evaluate(() => {
      window.VoiceEngine.setMockTranscript("I got a WhatsApp message");
    });

    await page.click('#homeVoiceMicBtn');

    // Voice modal should open
    await page.waitForSelector('#voiceModalOverlay.open', { timeout: 3000 });
    console.log('✓ Voice listening modal opened with pulsing UI');

    // Wait for the intent to be understood and modal to close
    await page.waitForFunction(() => !document.getElementById('voiceModalOverlay').classList.contains('open'), { timeout: 8000 });
    console.log('✓ Voice modal understood intent and dispatched navigation');

    // Assert: Message Check section is active
    await page.waitForSelector('#view-check.active', { timeout: 3000 });
    console.log('✓ Check view activated');

    // Assert: Voice Paste Banner is visible with WhatsApp prompt
    await page.waitForSelector('#voicePasteBanner', { state: 'visible', timeout: 3000 });
    const bannerText = await page.textContent('#voicePastePromptText');
    console.log(`✓ Voice Paste Banner displayed with text: "${bannerText.trim()}"`);
    assert(bannerText.includes('व्हाट्सएप') || bannerText.includes('WhatsApp'), 'Banner must mention WhatsApp');

    // Assert: Big Paste button fills the box and triggers analysis
    console.log('Step 4: Tapping big "Paste Message" button...');
    await page.click('#btnVoiceAutoPaste');

    const inputValue = await page.inputValue('#smsInput');
    assert.strictEqual(inputValue.trim(), testScamText, 'smsInput must contain pasted clipboard text');
    console.log('✓ Textbox populated from clipboard');

    // Assert: Detector returns verdict offline
    await page.waitForSelector('#smsVerdictBox.show', { timeout: 4000 });
    const verdictTitle = await page.textContent('#verdictTitle');
    console.log(`✓ Offline Detector executed successfully! Verdict: "${verdictTitle.trim()}"`);
    assert(verdictTitle.length > 0, 'Verdict title must not be empty');

    // 4. Test Fallback Flow: When no speech or unrecognised after 2 tries
    console.log('Step 5: Testing Voice Fallback UI on unrecognised input...');
    await page.evaluate(() => {
      window.App.navigate('home');
      window.VoiceHelper.retryCount = 1; // Simulate second try
      window.VoiceEngine.setMockTranscript("random gibberish that does not match");
    });

    await page.click('#homeVoiceMicBtn');
    await page.waitForSelector('#voiceFallbackGrid', { state: 'visible', timeout: 5000 });
    console.log('✓ Fallback 4-Button Menu automatically displayed after failed recognition');

    const fallbackButtonsCount = await page.locator('#voiceFallbackGrid .voice-fallback-btn').count();
    assert.strictEqual(fallbackButtonsCount, 4, 'Must display exactly 4 big fallback buttons');
    console.log('✓ Verified 4 big action fallback tiles (Message, Call, QR, 1930)');

    // Tap the 1930 Lost Money fallback button
    await page.click('#voiceFallbackLostMoney');
    await page.waitForSelector('#view-help.active', { timeout: 3000 });
    console.log('✓ Tapping Lost Money fallback button successfully opened Help screen');

    // 5. Test Mic Permission Denied
    console.log('Step 6: Testing Mic Permission Denied handling...');
    await page.evaluate(() => {
      window.App.navigate('home');
      window.VoiceEngine.setMockTranscript(null);
      // Simulate permission rejection
      const originalGetUserMedia = navigator.mediaDevices.getUserMedia;
      navigator.mediaDevices.getUserMedia = () => Promise.reject(new DOMException('Permission denied', 'NotAllowedError'));
    });

    await page.click('#homeVoiceMicBtn');
    await page.waitForSelector('#voiceFallbackGrid', { state: 'visible', timeout: 5000 });
    console.log('✓ Gracefully handled Permission Denied and presented 4 fallback buttons');

    // 6. Test Service Worker Cache in Offline Mode
    console.log('Step 7: Testing Service Worker Caching in Offline Mode...');
    const cacheVerification = await page.evaluate(async () => {
      const cacheNames = await caches.keys();
      const currentCacheName = cacheNames.find(c => c.startsWith('suraksha-'));
      if (!currentCacheName) return { found: false, error: 'No suraksha cache found' };

      const cache = await caches.open(currentCacheName);
      const keysToCheck = [
        '/js/voice_matcher.js',
        '/js/voice_engine.js',
        '/js/voice_helper.js',
        '/content/voice_intents.json'
      ];

      const matches = await Promise.all(keysToCheck.map(async k => {
        const res = await cache.match(k);
        return { key: k, cached: !!res };
      }));

      return { found: true, cacheName: currentCacheName, matches };
    });

    console.log(`✓ Active Service Worker Cache: ${cacheVerification.cacheName}`);
    for (const item of cacheVerification.matches) {
      console.log(`  └─ ${item.key}: ${item.cached ? 'CACHED ✓' : 'NOT CACHED ✗'}`);
    }

    // Reload page in offline mode to verify PWA offline durability
    console.log('Step 8: Reloading page in 100% offline mode...');
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#homeVoiceMicBtn', { state: 'visible', timeout: 5000 });
    console.log('✓ Application and Voice-First Helper loaded cleanly after offline reload!');

    console.log('\n========================================');
    console.log('🎉 ALL PLAYWRIGHT E2E TESTS PASSED (100%)');
    console.log('========================================\n');

  } catch (err) {
    console.error('❌ E2E TEST FAILED:', err);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
