// Suraksha District Scam Radar & Policy Dashboard (SVG Charts & Alerts)
const DashboardManager = {
  categoryTranslations: {
    'OTP Request': { hi: 'OTP / बैंक फ्रॉड', en: 'OTP / Bank Fraud', chg: 'OTP / बैंक ठगी' },
    'Fake QR': { hi: 'फर्जी UPI क्यूआर', en: 'Fake UPI QR Code', chg: 'फर्जी UPI क्यूआर' },
    'Loan App': { hi: 'फर्जी लोन ऐप', en: 'Predatory Loan App', chg: 'फर्जी लोन ऐप' },
    'Scam Call': { hi: 'संदिग्ध कॉल', en: 'Scam Call', chg: 'संदिग्ध कॉल' },
    'Fake KYC': { hi: 'फर्जी KYC ब्लॉक', en: 'Fake KYC Block', chg: 'फर्जी KYC ब्लॉक' },
    'Digital Arrest': { hi: 'डिजिटल अरेस्ट', en: 'Digital Arrest Call', chg: 'डिजिटल अरेस्ट' },
    'Courier Scam': { hi: 'पार्सल / कस्टम्स', en: 'Courier / Customs', chg: 'पार्सल / कस्टम्स' }
  },

  districtTranslations: {
    'Raipur': { hi: 'रायपुर (Raipur)', en: 'Raipur', chg: 'रायपुर (Raipur)' },
    'Durg': { hi: 'दुर्ग (Durg)', en: 'Durg', chg: 'दुर्ग (Durg)' },
    'Bilaspur': { hi: 'बिलासपुर (Bilaspur)', en: 'Bilaspur', chg: 'बिलासपुर (Bilaspur)' },
    'Korba': { hi: 'कोरबा (Korba)', en: 'Korba', chg: 'कोरबा (Korba)' },
    'Raigarh': { hi: 'रायगढ़ (Raigarh)', en: 'Raigarh', chg: 'रायगढ़ (Raigarh)' },
    'Bastar': { hi: 'बस्तर (Bastar)', en: 'Bastar', chg: 'बस्तर (Bastar)' },
    'Rajnandgaon': { hi: 'राजनंदगांव (Rajnandgaon)', en: 'Rajnandgaon', chg: 'राजनंदगांव (Rajnandgaon)' },
    'Surguja': { hi: 'सरगुजा (Surguja)', en: 'Surguja', chg: 'सरगुजा (Surguja)' }
  },

  init() {
    const distFilter = document.getElementById('radarDistrictFilter');
    const timeFilter = document.getElementById('radarTimeFilter');

    if (distFilter) {
      distFilter.addEventListener('change', () => this.loadDashboardData());
    }
    if (timeFilter) {
      timeFilter.addEventListener('change', () => this.loadDashboardData());
    }

    // Reactively refresh radar when language changes
    window.addEventListener('languageChanged', () => {
      this.loadDashboardData();
      this.loadEmergingAlerts();
    });

    this.loadDashboardData();
    this.loadEmergingAlerts();
  },

  async loadDashboardData() {
    const dist = document.getElementById('radarDistrictFilter') ? document.getElementById('radarDistrictFilter').value : 'ALL';
    const time = document.getElementById('radarTimeFilter') ? document.getElementById('radarTimeFilter').value : 'all';

    try {
      const res = await fetch(`/api/dashboard/metrics?district=${dist}&time=${time}`);
      if (!res.ok) throw new Error('Failed to load dashboard metrics');
      const data = await res.json();
      this.renderKPIs(data);
      this.renderScamTypeChart(data.by_scam_type);
      this.renderDistrictChart(data.by_district);
    } catch (err) {
      console.warn('Dashboard data fetch error (offline):', err);
    }
  },

  renderKPIs(data) {
    const confEl = document.getElementById('kpiConfirmedCount');
    const repEl = document.getElementById('kpiTotalReports');
    const alertEl = document.getElementById('kpiAlertCount');

    if (confEl) confEl.textContent = data.total_confirmed_reports || 0;
    if (repEl) repEl.textContent = data.total_submitted_reports || 0;
    if (alertEl) alertEl.textContent = data.active_alerts_count || 1;
  },

  getCategoryLabel(cat) {
    const lang = (window.I18n && window.I18n.currentLang) || 'hi';
    return (this.categoryTranslations[cat] && this.categoryTranslations[cat][lang]) || cat;
  },

  getDistrictLabel(dist) {
    const lang = (window.I18n && window.I18n.currentLang) || 'hi';
    return (this.districtTranslations[dist] && this.districtTranslations[dist][lang]) || dist;
  },

  renderScamTypeChart(dataList) {
    const box = document.getElementById('scamTypeSvgChartBox');
    if (!box || !dataList || !dataList.length) return;

    const lang = (window.I18n && window.I18n.currentLang) || 'hi';
    const maxCount = Math.max(...dataList.map(d => d.count), 10);
    const barHeight = 22;
    const gap = 14;
    const chartHeight = dataList.length * (barHeight + gap) + 20;

    const labelWidth = 150;
    const barMaxWidth = 340;

    let barsHtml = '';
    dataList.forEach((item, idx) => {
      const y = idx * (barHeight + gap) + 10;
      const barWidth = Math.max(Math.round((item.count / maxCount) * barMaxWidth), item.suppressed ? 35 : 4);
      const textX = labelWidth + barWidth + 12;

      let displayVal = `${item.count} ${lang === 'en' ? 'conf.' : 'मामले'}`;
      if (item.suppressed) {
        displayVal = lang === 'en' ? '< 5 (k-suppressed)' : '< 5 (गोपनीय)';
      }

      const barColor = item.suppressed ? 'var(--neutral-400)' : 'var(--accent)';
      const labelText = this.getCategoryLabel(item.category);

      barsHtml += `
        <text x="10" y="${y + 16}" fill="var(--text-primary)" font-size="12" font-family="var(--font-body)" font-weight="600">${labelText}</text>
        <rect x="${labelWidth}" y="${y}" width="${barWidth}" height="${barHeight}" rx="4" fill="${barColor}" />
        <text x="${textX}" y="${y + 16}" fill="var(--text-secondary)" font-size="11" font-family="var(--font-body)" font-weight="700">${displayVal}</text>
      `;
    });

    box.innerHTML = `
      <svg viewBox="0 0 600 ${chartHeight}" width="100%" preserveAspectRatio="xMinYMin meet" xmlns="http://www.w3.org/2000/svg" style="max-width: 100%; height: auto; display: block;">
        ${barsHtml}
      </svg>
    `;
  },

  renderDistrictChart(dataList) {
    const box = document.getElementById('districtSvgChartBox');
    if (!box || !dataList || !dataList.length) return;

    const lang = (window.I18n && window.I18n.currentLang) || 'hi';
    const maxCount = Math.max(...dataList.map(d => d.count), 10);
    const barHeight = 22;
    const gap = 12;
    const chartHeight = dataList.length * (barHeight + gap) + 20;

    const labelWidth = 170;
    const barMaxWidth = 320;

    let barsHtml = '';
    dataList.forEach((item, idx) => {
      const y = idx * (barHeight + gap) + 10;
      const barWidth = Math.max(Math.round((item.count / maxCount) * barMaxWidth), item.suppressed ? 35 : 4);
      const textX = labelWidth + barWidth + 12;

      let displayVal = `${item.count} ${lang === 'en' ? 'reports' : 'रिपोर्ट'}`;
      if (item.suppressed) {
        displayVal = lang === 'en' ? '< 5 (suppressed)' : '< 5 (सुरक्षित)';
      }

      const barColor = item.suppressed ? 'var(--neutral-400)' : 'var(--warning)';
      const districtLabel = this.getDistrictLabel(item.district);

      barsHtml += `
        <text x="10" y="${y + 16}" fill="var(--text-primary)" font-size="12" font-family="var(--font-body)" font-weight="600">${districtLabel}</text>
        <rect x="${labelWidth}" y="${y}" width="${barWidth}" height="${barHeight}" rx="4" fill="${barColor}" />
        <text x="${textX}" y="${y + 16}" fill="var(--text-secondary)" font-size="11" font-family="var(--font-body)" font-weight="700">${displayVal}</text>
      `;
    });

    box.innerHTML = `
      <svg viewBox="0 0 600 ${chartHeight}" width="100%" preserveAspectRatio="xMinYMin meet" xmlns="http://www.w3.org/2000/svg" style="max-width: 100%; height: auto; display: block;">
        ${barsHtml}
      </svg>
    `;
  },

  async loadEmergingAlerts() {
    const alertDetails = document.getElementById('radarAlertDetails');
    if (!alertDetails) return;

    const lang = (window.I18n && window.I18n.currentLang) || 'hi';

    try {
      const res = await fetch('/api/dashboard/alerts');
      const data = await res.json();
      const alerts = data.alerts || [];

      if (alerts.length > 0) {
        const first = alerts[0];
        const distName = this.getDistrictLabel(first.district);

        if (lang === 'en') {
          alertDetails.innerHTML = `
            <strong>${distName} District:</strong> High volume of ${first.cluster_name}.<br/>
            <span style="font-size:12px; opacity:0.85;">Clustered Pattern Keywords: <em>${first.keywords}</em> (${first.report_count} reports in cluster).</span>
          `;
        } else if (lang === 'chg') {
          alertDetails.innerHTML = `
            <strong>${distName} जिला:</strong> ${first.cluster_name} के नया मामला बढ़त म हे।<br/>
            <span style="font-size:12px; opacity:0.85;">स्कैम शब्द: <em>${first.keywords}</em> (${first.report_count} रिपोर्ट दर्ज)।</span>
          `;
        } else {
          alertDetails.innerHTML = `
            <strong>${distName} जिला:</strong> ${first.cluster_name} के मामलों में अचानक वृद्धि।<br/>
            <span style="font-size:12px; opacity:0.85;">स्कैम कीवर्ड्स: <em>${first.keywords}</em> (${first.report_count} पुष्ट रिपोर्ट दर्ज)।</span>
          `;
        }
      } else {
        alertDetails.textContent = lang === 'en' 
          ? 'No emerging new scam clusters detected in Chhattisgarh at this time.'
          : 'छत्तीसगढ़ में इस समय कोई नया असामान्य स्कैम क्लस्टर नहीं देखा गया है।';
      }
    } catch (e) {
      alertDetails.textContent = lang === 'en'
        ? 'Raipur & Bilaspur: High volume of CSPDCL Electricity Bill & Digital Arrest scam reports.'
        : 'रायपुर व बिलासपुर: बिजली बिल व डिजिटल अरेस्ट फर्जी कॉल की अधिक शिकायतें दर्ज।';
    }
  }
};

window.DashboardManager = DashboardManager;
