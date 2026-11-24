const { chromium } = require('playwright');
const assert = require('assert');

(async () => {
  console.log('🚀 Starting Bilingual Voice Assistant (Hindi & Chhattisgarhi) E2E Test Suite...');
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:\\Users\\jt332\\AppData\\Local\\ms-playwright\\chromium-1254\\chrome-win64\\chrome.exe',
    args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream']
  });

  const context = await browser.newContext({
    permissions: ['clipboard-read', 'clipboard-write', 'microphone']
  });
  const page = await context.newPage();

  page.on('console', msg => {
    if (msg.type() === 'error') {
      if (!msg.text().includes('status of 503') && !msg.text().includes('status of 408')) {
        console.log(`[Browser Error]:`, msg.text());
      }
    }
  });

  try {
    console.log('Step 1: Loading application at http://127.0.0.1:8000/');
    await page.goto('http://127.0.0.1:8000/', { waitUntil: 'networkidle' });
    await page.waitForSelector('#homeVoiceMicBtn', { state: 'visible' });

    // Ensure language selector pills are present
    console.log('Step 2: Checking Language Mode Pills inside voice modal...');
    await page.click('#homeVoiceMicBtn');
    await page.waitForSelector('#voiceModalOverlay.open');
    await page.waitForSelector('#voiceLangBar', { state: 'visible' });
    const pillsCount = await page.locator('#voiceLangBar .voice-lang-pill').count();
    assert.strictEqual(pillsCount, 4, 'Should render 4 language mode pills (Auto, Hindi, Chhattisgarhi, English)');
    console.log('✓ Verified 4 language mode pills in modal');

    // Test pill switching
    await page.click('#btnVoiceLangChg');
    const chgActive = await page.$eval('#btnVoiceLangChg', el => el.classList.contains('active'));
    assert(chgActive, 'Chhattisgarhi pill should be active');
    const titleTextChg = await page.textContent('#voiceStatusTitle');
    assert(titleTextChg.includes('सुनत हन'), 'Title should show Chhattisgarhi listening text');
    console.log(`✓ Chhattisgarhi mode activated: "${titleTextChg.trim()}"`);

    await page.click('#btnVoiceLangHi');
    const hiActive = await page.$eval('#btnVoiceLangHi', el => el.classList.contains('active'));
    assert(hiActive, 'Hindi pill should be active');
    const titleTextHi = await page.textContent('#voiceStatusTitle');
    assert(titleTextHi.includes('सुन रहे हैं'), 'Title should show Hindi listening text');
    console.log(`✓ Hindi mode activated: "${titleTextHi.trim()}"`);

    // Reset to Auto mode (Both Hindi & Chhattisgarhi)
    await page.click('#btnVoiceLangAuto');
    await page.click('#btnVoiceModalClose');
    await page.waitForFunction(() => !document.getElementById('voiceModalOverlay').classList.contains('open'));

    // Step 3: Test Chhattisgarhi Voice Input: "मोला व्हाट्सएप म मैसेज आइस"
    console.log('Step 3: Testing Chhattisgarhi input "मोला व्हाट्सएप म मैसेज आइस"...');
    await page.evaluate(() => {
      window.App.navigate('home');
      window.VoiceEngine.setMockTranscript("मोला व्हाट्सएप म मैसेज आइस");
    });
    await page.click('#homeVoiceMicBtn');
    await page.waitForFunction(() => !document.getElementById('voiceModalOverlay').classList.contains('open'), { timeout: 6000 });

    await page.waitForSelector('#view-check.active');
    await page.waitForSelector('#voicePasteBanner.active');
    const chgBannerText = await page.textContent('#voicePastePromptText');
    console.log(`✓ Chhattisgarhi WhatsApp banner displayed: "${chgBannerText.trim()}"`);
    assert(chgBannerText.includes('व्हाट्सएप') && (chgBannerText.includes('पेस्ट करव') || chgBannerText.includes('पेस्ट करें')), 'Banner text should prompt paste in Chhattisgarhi');
    const isFocusedChg = await page.evaluate(() => document.activeElement && document.activeElement.id === 'smsInput');
    assert(isFocusedChg, 'smsInput must be focused');

    // Step 4: Test Hindi Voice Input: "मुझे व्हाट्सएप मैसेज आया है"
    console.log('Step 4: Testing Hindi input "मुझे व्हाट्सएप मैसेज आया है"...');
    await page.evaluate(() => {
      window.App.navigate('home');
      window.VoiceEngine.setMockTranscript("मुझे व्हाट्सएप मैसेज आया है");
    });
    await page.click('#homeVoiceMicBtn');
    await page.waitForFunction(() => !document.getElementById('voiceModalOverlay').classList.contains('open'), { timeout: 6000 });

    await page.waitForSelector('#view-check.active');
    await page.waitForSelector('#voicePasteBanner.active');
    const hiBannerText = await page.textContent('#voicePastePromptText');
    console.log(`✓ Hindi WhatsApp banner displayed: "${hiBannerText.trim()}"`);
    assert(hiBannerText.includes('व्हाट्सएप') && hiBannerText.includes('पेस्ट करें'), 'Banner text should prompt paste in Hindi');

    // Step 5: Test Chhattisgarhi Call Input: "थाना ले फोन आइस"
    console.log('Step 5: Testing Chhattisgarhi call input "थाना ले फोन आइस"...');
    await page.evaluate(() => {
      window.App.navigate('home');
      window.VoiceEngine.setMockTranscript("थाना ले फोन आइस");
    });
    await page.click('#homeVoiceMicBtn');
    await page.waitForFunction(() => !document.getElementById('voiceModalOverlay').classList.contains('open'), { timeout: 6000 });
    await page.waitForSelector('#view-check.active');
    const callSubtabActive1 = await page.$eval('#subtab-call', el => el.classList.contains('active') || el.style.display === 'block');
    assert(callSubtabActive1, 'Call subtab should be active for Chhattisgarhi call input');
    console.log('✓ Routed to Call subtab from Chhattisgarhi input');

    // Step 6: Test Hindi Call Input: "फर्जी पुलिस की कॉल आई है"
    console.log('Step 6: Testing Hindi call input "फर्जी पुलिस की कॉल आई है"...');
    await page.evaluate(() => {
      window.App.navigate('home');
      window.VoiceEngine.setMockTranscript("फर्जी पुलिस की कॉल आई है");
    });
    await page.click('#homeVoiceMicBtn');
    await page.waitForFunction(() => !document.getElementById('voiceModalOverlay').classList.contains('open'), { timeout: 6000 });
    await page.waitForSelector('#view-check.active');
    const callSubtabActive2 = await page.$eval('#subtab-call', el => el.classList.contains('active') || el.style.display === 'block');
    assert(callSubtabActive2, 'Call subtab should be active for Hindi call input');
    console.log('✓ Routed to Call subtab from Hindi input');

    // Step 7: Test Chhattisgarhi Lost Money: "पईसा कट गे मोर संग ठगी होगे"
    console.log('Step 7: Testing Chhattisgarhi lost money input "पईसा कट गे मोर संग ठगी होगे"...');
    await page.evaluate(() => {
      window.App.navigate('home');
      window.VoiceEngine.setMockTranscript("पईसा कट गे मोर संग ठगी होगे");
    });
    await page.click('#homeVoiceMicBtn');
    await page.waitForFunction(() => !document.getElementById('voiceModalOverlay').classList.contains('open'), { timeout: 6000 });
    await page.waitForSelector('#view-help.active');
    console.log('✓ Routed to Help view (1930) from Chhattisgarhi input');

    // Step 8: Test Hindi Lost Money: "पैसे कट गए फ्रॉड हो गया"
    console.log('Step 8: Testing Hindi lost money input "पैसे कट गए फ्रॉड हो गया"...');
    await page.evaluate(() => {
      window.App.navigate('home');
      window.VoiceEngine.setMockTranscript("पैसे कट गए फ्रॉड हो गया");
    });
    await page.click('#homeVoiceMicBtn');
    await page.waitForFunction(() => !document.getElementById('voiceModalOverlay').classList.contains('open'), { timeout: 6000 });
    await page.waitForSelector('#view-help.active');
    console.log('✓ Routed to Help view (1930) from Hindi input');

    // Step 9: Test Chhattisgarhi Learn: "सुरक्षा सीखबो"
    console.log('Step 9: Testing Chhattisgarhi learn input "सुरक्षा सीखबो"...');
    await page.evaluate(() => {
      window.App.navigate('home');
      window.VoiceEngine.setMockTranscript("सुरक्षा सीखबो");
    });
    await page.click('#homeVoiceMicBtn');
    await page.waitForFunction(() => !document.getElementById('voiceModalOverlay').classList.contains('open'), { timeout: 6000 });
    await page.waitForSelector('#view-learn.active');
    console.log('✓ Routed to Learn view from Chhattisgarhi input');

    // Step 10: Test Hindi Learn: "सुरक्षा पाठ सीखना है"
    console.log('Step 10: Testing Hindi learn input "सुरक्षा पाठ सीखना है"...');
    await page.evaluate(() => {
      window.App.navigate('home');
      window.VoiceEngine.setMockTranscript("सुरक्षा पाठ सीखना है");
    });
    await page.click('#homeVoiceMicBtn');
    await page.waitForFunction(() => !document.getElementById('voiceModalOverlay').classList.contains('open'), { timeout: 6000 });
    await page.waitForSelector('#view-learn.active');
    console.log('✓ Routed to Learn view from Hindi input');

    console.log('\n======================================================');
    console.log('🎉 ALL BILINGUAL (HINDI & CHHATTISGARHI) TESTS PASSED!');
    console.log('======================================================\n');
  } catch (err) {
    console.error('❌ TEST FAILED:', err);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
