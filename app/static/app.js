// app/static/app.js
// GridSense — Dashboard JavaScript
// Atmospheric Glassmorphism Energy Intelligence Dashboard

/* ============================================================
   GLOBALS
   ============================================================ */
let loadChart = null;
let socChart = null;
let gridDoughnut = null;
let energyRouteChart = null;
let overloadChart = null;
let currentForecast = null;

/* ============================================================
   CHART.JS DEFAULTS (dark theme)
   ============================================================ */
Chart.defaults.color = '#A5B4CC';
Chart.defaults.borderColor = 'rgba(52, 71, 94, 0.35)';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 11;
Chart.defaults.font.weight = 450;
Chart.defaults.plugins.legend.display = false;
Chart.defaults.plugins.tooltip.backgroundColor = '#20294B';
Chart.defaults.plugins.tooltip.borderColor = '#FF7B6E';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.cornerRadius = 10;
Chart.defaults.plugins.tooltip.padding = 12;
Chart.defaults.plugins.tooltip.titleColor = '#FFFFFF';
Chart.defaults.plugins.tooltip.bodyColor = '#F7F3FF';
Chart.defaults.plugins.tooltip.titleFont = { family: "'Inter', sans-serif", size: 12, weight: 600 };
Chart.defaults.plugins.tooltip.bodyFont = { family: "'Inter', sans-serif", size: 11, weight: 450 };
Chart.defaults.elements.point.radius = 3;
Chart.defaults.elements.point.hoverRadius = 6;
Chart.defaults.elements.point.borderWidth = 2;
Chart.defaults.elements.line.borderWidth = 2.5;

/* ============================================================
   COLORS
   ============================================================ */
const C = {
  teal: '#91A99A',
  aqua: '#91A99A',
  violet: '#A99BCB',
  amber: '#B88762',
  coral: '#E45F65',
  white: '#F1E9DF',
  muted: '#AAA9A1',
  dim: '#777A72',
  glass: '#202622',
};

/* ============================================================
   INITIALIZATION
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {
  setDate();
  setGreeting();
  initTabs();
  initManualGrid();
  initDropZone();
  initNavigation();
  const initialPage = getPageFromHash();
  updatePageGuide(initialPage);
  applyPageView(initialPage);
  activateNavigationPage(initialPage);
  window.addEventListener('hashchange', () => activateNavigationPage(getPageFromHash()));
  initMobileNavigation();
  initCustomCursor();
  initQuickActions();
  bindButtons();
  loadDemo({ showResult: false }); // Seed the dashboard without interrupting the first visit
  fetchLogs();
});

/* ============================================================
   DATE & GREETING
   ============================================================ */
function setDate() {
  const now = new Date();
  const opts = { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' };
  document.getElementById('dateText').textContent = now.toLocaleDateString('en-IN', opts);
}

function updateOverloadChart(rows, summary) {
  const labels = rows.map(r => {
    const hour = timestampHour(r.timestamp);
    return `${String(hour).padStart(2, '0')}:00`;
  });
  const overloadValues = rows.map(r => r.overload ? 1 : 0);
  const total = overloadValues.reduce((sum, value) => sum + value, 0);
  const totalElement = document.getElementById('overloadChartTotal');
  if (totalElement) {
    totalElement.textContent = `${total} hour${total === 1 ? '' : 's'} flagged`;
  }

  const canvas = document.getElementById('overloadChart');
  if (!canvas) return;
  if (overloadChart) overloadChart.destroy();

  overloadChart = new Chart(canvas.getContext('2d'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Overload risk',
        data: overloadValues,
        backgroundColor: rows.map(r => r.overload ? 'rgba(228, 95, 101, 0.88)' : 'rgba(145, 169, 154, 0.16)'),
        borderColor: rows.map(r => r.overload ? C.coral : 'rgba(145, 169, 154, 0.38)'),
        borderWidth: 1,
        borderRadius: 5,
        borderSkipped: false,
        barPercentage: 0.72,
        categoryPercentage: 0.86,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (item) => item.raw
              ? 'Critical overload · 200+ kW threshold'
              : 'Within critical threshold'
          }
        }
      },
      scales: {
        y: {
          min: 0,
          max: 1,
          ticks: {
            stepSize: 1,
            color: '#AAA9A1',
            callback: value => value === 1 ? 'Flagged' : 'Safe'
          },
          title: { display: true, text: 'Risk status', color: '#AAA9A1' },
          grid: { color: 'rgba(170, 169, 161, 0.12)' }
        },
        x: {
          grid: { display: false },
          ticks: {
            color: '#AAA9A1',
            autoSkip: false,
            maxRotation: 0,
            callback: (value, index) => index % 4 === 0 ? labels[index] : ''
          }
        }
      }
    }
  });
}

function setGreeting() {
  const h = new Date().getHours();
  let greeting = 'Good Evening';
  if (h < 12) greeting = 'Good Morning';
  else if (h < 17) greeting = 'Good Afternoon';
  document.getElementById('greetingText').textContent = `${greeting}, Sansriti ✨`;
}

/* ============================================================
   UNIQUE FUTURISTIC SCI-FI ENERGY CURSOR
   ============================================================ */
function initCustomCursor() {
  const dot = document.getElementById('cursorDot');
  const ring = document.getElementById('cursorRing');
  if (!dot || !ring || window.matchMedia('(pointer: coarse)').matches) return;

  let mouseX = -100, mouseY = -100;
  let ringX = -100, ringY = -100;

  window.addEventListener('mousemove', e => {
    mouseX = e.clientX;
    mouseY = e.clientY;
    document.body.classList.add('custom-cursor-visible');

    // Immediate tracking for the core energy dot
    dot.style.left = `${mouseX}px`;
    dot.style.top = `${mouseY}px`;
  }, { passive: true });

  window.addEventListener('mousedown', () => {
    document.body.classList.add('custom-cursor-active');
  });

  window.addEventListener('mouseup', () => {
    document.body.classList.remove('custom-cursor-active');
  });

  document.addEventListener('mouseleave', () => {
    document.body.classList.remove('custom-cursor-visible');
  });

  document.addEventListener('mouseenter', () => {
    document.body.classList.add('custom-cursor-visible');
  });

  // Track hover on interactive elements
  const interactiveSelector = 'button, a, input, select, textarea, [role="button"], .nav-item, .mobile-nav-item, .kpi-card, .action-row, .sculpture-card, .chart-select, .chart-expand-btn, tr';
  document.addEventListener('mouseover', e => {
    if (e.target.closest(interactiveSelector)) {
      document.body.classList.add('custom-cursor-hover');
    }
  });

  document.addEventListener('mouseout', e => {
    if (e.target.closest(interactiveSelector)) {
      document.body.classList.remove('custom-cursor-hover');
    }
  });

  // Smooth lerp loop for the lagging targeting ring
  function renderCursor() {
    const ease = 0.24;
    ringX += (mouseX - ringX) * ease;
    ringY += (mouseY - ringY) * ease;

    ring.style.left = `${ringX}px`;
    ring.style.top = `${ringY}px`;

    requestAnimationFrame(renderCursor);
  }
  requestAnimationFrame(renderCursor);
}

/* ============================================================
   MOBILE NAVIGATION & DRAWER
   ============================================================ */
function initMobileNavigation() {
  const menuBtn = document.getElementById('mobileMenuBtn');
  const sidebar = document.getElementById('sidebar');
  const backdrop = document.getElementById('sidebarBackdrop');

  if (menuBtn && sidebar && backdrop) {
    const toggleDrawer = (open) => {
      sidebar.classList.toggle('open', open);
      backdrop.classList.toggle('active', open);
      document.body.style.overflow = open ? 'hidden' : '';
    };

    menuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = sidebar.classList.contains('open');
      toggleDrawer(!isOpen);
    });

    backdrop.addEventListener('click', () => toggleDrawer(false));

    // Close drawer when any nav item clicked on mobile
    sidebar.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
          toggleDrawer(false);
        }
      });
    });
  }

  // Mobile Bottom Dock buttons sync with page navigation
  document.querySelectorAll('.mobile-nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.mobile-nav-item').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const page = btn.dataset.page;
      const desktopNav = document.querySelector(`.nav-item[data-page="${page}"]`);
      if (desktopNav) desktopNav.click();
    });
  });
}

/* ============================================================
   NAVIGATION
   ============================================================ */
function initNavigation() {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      item.classList.add('active');
      const page = item.dataset.page;
      if (window.location.hash !== `#${page}`) {
        history.pushState({ page }, '', `#${page}`);
      }
      updatePageGuide(page);
      applyPageView(page);
      // Also sync mobile bottom dock active state
      document.querySelectorAll('.mobile-nav-item').forEach(m => {
        m.classList.toggle('active', m.dataset.page === page);
      });
      // Scroll to relevant section or show tab
      if (page === 'upload') {
        scrollToSection('inputSection');
        activateTab('csv');
      } else if (page === 'forecast') {
        scrollToSection('demandChartPanel');
      } else if (page === 'controller') {
        scrollToSection('controllerSection');
      } else if (page === 'history') {
        scrollToSection('tableSection');
      } else if (page === 'dashboard') {
        document.getElementById('mainContent').scrollTo({ top: 0, behavior: 'smooth' });
      } else if (page === 'about') {
        scrollToSection('pageGuide');
      }

    });
  });
}

function getPageFromHash() {
  const page = window.location.hash.replace('#', '');
  return ['dashboard', 'forecast', 'upload', 'controller', 'history', 'about'].includes(page) ? page : 'dashboard';
}

function activateNavigationPage(page) {
  const item = document.querySelector(`.nav-item[data-page="${page}"]`);
  if (item) item.click();
}

function applyPageView(page) {
  const views = {
    dashboard: ['pageGuide', 'alertBanner', 'heroSection', 'kpiRow', '.analytics-row', '.bottom-row'],
    forecast: ['pageGuide', 'alertBanner', '.analytics-row', 'overloadSection'],
    upload: ['pageGuide', 'inputSection'],
    controller: ['pageGuide', 'alertBanner', 'controllerSection'],
    history: ['pageGuide', 'tableSection', '.dual-row', 'qualitySection'],
    about: ['pageGuide', 'aboutSection']
  };
  const visible = new Set(views[page] || views.dashboard);
  document.querySelectorAll('#mainContent > *').forEach(element => {
    const matches = visible.has(element.id) || visible.has(`.${element.classList[0]}`);
    element.classList.toggle('page-view-hidden', !matches);
  });
  requestAnimationFrame(() => {
    [loadChart, gridDoughnut, energyRouteChart, socChart, overloadChart].forEach(chart => chart?.resize());
  });
}

function updatePageGuide(page) {
  const guides = {
    dashboard: {
      eyebrow: 'ORIENTATION',
      title: 'Grid intelligence at a glance',
      description: 'This dashboard turns weather telemetry into a 24-hour demand forecast, then explains the controller decision that protects the microgrid.',
      significance: 'One view connects prediction, dispatch, battery reserve, and risk.'
    },
    forecast: {
      eyebrow: 'FORECAST / DEMAND OUTLOOK',
      title: 'Understand the next 24 hours',
      description: 'The demand chart shows predicted electrical load against the 160 kW reserve and 200 kW critical thresholds.',
      significance: 'A peak forecast gives operators time to prepare storage before a local overload becomes an outage.'
    },
    upload: {
      eyebrow: 'INPUT / TELEMETRY INGESTION',
      title: 'Give the model clean hourly weather data',
      description: 'Upload a CSV, enter weather manually, use a typical-day profile, or load the demonstration dataset.',
      significance: 'The same validated input contract feeds QuickML, the controller, and every downstream chart.'
    },
    controller: {
      eyebrow: 'CONTROL / POWER DISPATCH',
      title: 'See why each source is selected',
      description: 'The controller compares predicted demand, solar availability, battery reserve, and the evening operating window.',
      significance: 'This is the decision layer that changes a forecast into an actionable grid, battery, and solar route.'
    },
    history: {
      eyebrow: 'EVIDENCE / FORECAST DETAILS',
      title: 'Inspect the evidence behind the decision',
      description: 'The hourly table and control signals expose the exact inputs, prediction, mode change, battery state, and overload status.',
      significance: 'Traceability makes the result explainable instead of leaving operators with an unexplained chart.'
    },
    about: {
      eyebrow: 'ABOUT / SYSTEM ARCHITECTURE',
      title: 'How GridSense works',
      description: 'Browser inputs pass through Flask ingestion and feature preparation, QuickML prediction, controller rules, battery simulation, and Catalyst persistence.',
      significance: 'The architecture keeps forecasting, decision rules, and presentation separate so each result can be tested and trusted.'
    }
  };
  const guide = guides[page] || guides.dashboard;
  const eyebrow = document.getElementById('pageGuideEyebrow');
  const title = document.getElementById('pageGuideTitle');
  const description = document.getElementById('pageGuideDescription');
  const significance = document.getElementById('pageGuideSignificance');
  if (eyebrow) eyebrow.textContent = guide.eyebrow;
  if (title) title.textContent = guide.title;
  if (description) description.textContent = guide.description;
  if (significance) significance.textContent = guide.significance;
  document.title = `GridSense · ${guide.title}`;
}

function scrollToSection(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/* ============================================================
   QUICK ACTIONS
   ============================================================ */
function initQuickActions() {
  document.getElementById('actionUpload').addEventListener('click', () => {
    document.getElementById('navUpload').click();
  });
  document.getElementById('actionSimulation').addEventListener('click', () => {
    document.getElementById('navSimulation').click();
  });
  document.getElementById('actionHistory').addEventListener('click', () => {
    document.getElementById('navHistory').click();
  });
}

/* ============================================================
   TAB SYSTEM
   ============================================================ */
function initTabs() {
  document.querySelectorAll('.tab-btn[role="tab"]').forEach(btn => {
    btn.addEventListener('click', () => {
      activateTab(btn.dataset.tab);
    });
  });
}

function activateTab(tabId) {
  // Update buttons
  document.querySelectorAll('#inputTabs .tab-btn').forEach(b => {
    b.classList.remove('active');
    b.setAttribute('aria-selected', 'false');
  });
  const btn = document.querySelector(`#inputTabs .tab-btn[data-tab="${tabId}"]`);
  if (btn) {
    btn.classList.add('active');
    btn.setAttribute('aria-selected', 'true');
  }

  // Update panels
  document.querySelectorAll('#inputSection .tab-panel').forEach(p => {
    p.hidden = true;
  });
  const panel = document.getElementById(`panel-${tabId}`);
  if (panel) panel.hidden = false;
}

/* ============================================================
   MANUAL GRID
   ============================================================ */
function initManualGrid() {
  const grid = document.getElementById('manualGrid');
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  for (let h = 0; h < 24; h++) {
    const ts = new Date(today.getTime() + h * 3600000);
    const hh = String(h).padStart(2, '0');

    const row = document.createElement('div');
    row.className = 'manual-row';
    row.innerHTML = `
      <input type="text" value="${hh}:00" readonly>
      <input type="number" step="0.1" placeholder="Temp" class="manual-temp" value="20.0">
      <input type="number" step="0.1" placeholder="Hum" class="manual-hum" value="60.0">
      <input type="number" step="0.1" placeholder="Solar" class="manual-sol" value="0.0">
    `;
    grid.appendChild(row);
  }
}

/* ============================================================
   DROP ZONE
   ============================================================ */
function initDropZone() {
  const zone = document.getElementById('dropZone');
  const input = document.getElementById('csvFile');

  zone.addEventListener('click', () => input.click());
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) uploadCSV(file);
  });

  input.addEventListener('change', e => {
    const file = e.target.files[0];
    if (file) uploadCSV(file);
  });
}

/* ============================================================
   BUTTON BINDINGS
   ============================================================ */
function bindButtons() {
  document.getElementById('btnManualForecast')?.addEventListener('click', submitManual);
  document.getElementById('btnFillTypical')?.addEventListener('click', () => loadTypicalDay());
  document.getElementById('btnTypicalDay')?.addEventListener('click', () => loadTypicalDay());
  document.getElementById('btnLoadDemo')?.addEventListener('click', loadDemo);
  document.getElementById('demoViewResults')?.addEventListener('click', () => {
    document.getElementById('tableSection')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
  document.getElementById('demoModalClose')?.addEventListener('click', closeDemoModal);
  document.getElementById('demoModalDismiss')?.addEventListener('click', closeDemoModal);
  document.getElementById('demoModalViewResults')?.addEventListener('click', () => {
    closeDemoModal();
    document.getElementById('tableSection')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
  document.getElementById('demoModal')?.addEventListener('click', event => {
    if (event.target.id === 'demoModal') closeDemoModal();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !document.getElementById('demoModal')?.hidden) {
      closeDemoModal();
    }
  });
  document.getElementById('downloadCsv')?.addEventListener('click', downloadCSV);
  document.getElementById('clearLogs')?.addEventListener('click', () => {
    document.getElementById('logsList').innerHTML = '<div class="empty-state"><p>Logs cleared</p></div>';
  });

  // Table search
  document.getElementById('tableSearch')?.addEventListener('input', e => {
    filterTable(e.target.value);
  });
}

/* ============================================================
   API CALLS
   ============================================================ */
async function loadDemo({ showResult = true } = {}) {
  const demoButton = document.getElementById('btnLoadDemo');
  const demoButtonText = document.getElementById('loadDemoText');
  const demoResult = document.getElementById('demoResult');
  if (demoButton) demoButton.disabled = true;
  if (demoButtonText) demoButtonText.textContent = 'Loading demo…';
  if (demoResult) demoResult.hidden = true;
  showLoading('Loading demo forecast…');
  try {
    const res = await fetch('/api/demo');
    const data = await res.json();
    if (res.ok) {
      renderForecast(data);
      if (showResult) {
        showForecastResult(data, 'Demo forecast', 'Your 24-hour demo scenario has been processed.');
      }
    } else {
      showError(data.error || 'Failed to load demo');
    }
  } catch (e) {
    showError('Demo load failed: ' + e.message);
  }
  hideLoading();
  if (demoButton) demoButton.disabled = false;
  if (demoButtonText) demoButtonText.textContent = 'Load Demo Forecast';
}

function showForecastResult(data, source, description) {
  const rows = Array.isArray(data.rows) ? data.rows : [];
  const summary = data.summary || {};
  const avgTemp = rows.length
    ? rows.reduce((total, row) => total + Number(row.ambient_temp_c || 0), 0) / rows.length
    : 0;
  const overloadHours = Number(summary.overload_hours || 0);
  const result = document.getElementById('demoResult');
  const title = document.getElementById('demoResultTitle');
  const text = document.getElementById('demoResultText');

  if (!result || !title || !text) return;

  title.textContent = `${source} is ready`;
  text.textContent = `${rows.length} hours analyzed · Peak ${Number(summary.peak_kw || 0).toFixed(1)} kW · Avg. temperature ${avgTemp.toFixed(1)}°C${overloadHours ? ` · ${overloadHours} overload hour${overloadHours === 1 ? '' : 's'} flagged` : ' · No overload expected'}`;
  result.classList.toggle('has-warning', overloadHours > 0);
  result.hidden = false;
  result.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  showForecastModal(rows.length, summary.peak_kw, avgTemp, overloadHours, source, description);
  showToast(`✅ ${source} ready: ${rows.length} hours analyzed`);
}

function showForecastModal(hours, peak, avgTemp, overloadHours, source, description) {
  const modal = document.getElementById('demoModal');
  if (!modal) return;

  document.getElementById('demoModalKicker').textContent = `${source.toUpperCase()} COMPLETE`;
  document.getElementById('demoModalTitle').textContent = `${source} is ready`;
  document.getElementById('demoModalDescription').textContent = description;
  document.getElementById('demoModalHours').textContent = hours;
  document.getElementById('demoModalPeak').textContent = `${Number(peak || 0).toFixed(1)} kW`;
  document.getElementById('demoModalTemperature').textContent = `${avgTemp.toFixed(1)}°C`;

  const status = document.getElementById('demoModalStatus');
  if (overloadHours > 0) {
    status.className = 'demo-modal-status warning';
    status.textContent = `⚠ ${overloadHours} overload hour${overloadHours === 1 ? '' : 's'} detected. Review the highlighted hours in the detailed table.`;
  } else {
    status.className = 'demo-modal-status success';
    status.textContent = '✓ No overload expected. The system is operating within safe limits.';
  }

  modal.hidden = false;
  document.body.classList.add('modal-open');
  document.getElementById('demoModalDismiss')?.focus();
}

function closeDemoModal() {
  const modal = document.getElementById('demoModal');
  if (!modal) return;
  modal.hidden = true;
  document.body.classList.remove('modal-open');
}

async function loadTypicalDay() {
  const dateInput = document.getElementById('typicalDate');
  const date = dateInput?.value || new Date().toISOString().split('T')[0];
  showLoading('Generating typical day…');
  try {
    const res = await fetch('/api/typical-day?date=' + date);
    const data = await res.json();
    if (res.ok) {
      renderForecast(data);
      showForecastResult(data, 'Typical-day forecast', `The typical weather profile for ${date} has been processed.`);
      if (data.note) showToast('ℹ️ ' + data.note);
    } else {
      showError(data.error || 'Failed to generate typical day');
    }
  } catch (e) {
    showError('Typical day failed: ' + e.message);
  }
  hideLoading();
}

async function uploadCSV(file) {
  showLoading('Processing CSV…');
  const formData = new FormData();
  formData.append('file', file);
  try {
    const res = await fetch('/api/forecast', { method: 'POST', body: formData });
    const data = await res.json();
    if (res.ok) {
      renderForecast(data);
      showForecastResult(data, 'CSV forecast', `Your uploaded file "${file.name}" has been processed.`);
      showInputConfirmation(data.rows, file.name);
      showToast(`✅ Forecast generated for ${data.rows.length} hours`);
    } else {
      showError(data.error || 'Upload failed');
    }
  } catch (e) {
    showError('Upload failed: ' + e.message);
  }
  hideLoading();
}

async function submitManual() {
  const rows = [];
  const today = new Date().toISOString().split('T')[0];

  document.querySelectorAll('.manual-row').forEach((row, i) => {
    const inputs = row.querySelectorAll('input');
    const hh = String(i).padStart(2, '0');
    rows.push({
      timestamp: `${today} ${hh}:00:00`,
      ambient_temp_c: parseFloat(inputs[1].value) || 0,
      humidity_pct: parseFloat(inputs[2].value) || 0,
      solar_irradiance_wm2: parseFloat(inputs[3].value) || 0,
    });
  });

  showLoading('Generating forecast…');
  try {
    const res = await fetch('/api/forecast', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rows })
    });
    const data = await res.json();
    if (res.ok) {
      renderForecast(data);
      showForecastResult(data, 'Manual forecast', 'Your manually entered weather data has been processed.');
      showInputConfirmation(rows);
      showToast('✅ Manual forecast generated');
    } else {
      showError(data.error || 'Forecast failed');
    }
  } catch (e) {
    showError('Forecast failed: ' + e.message);
  }
  hideLoading();
}

function showInputConfirmation(rows, sourceName) {
  if (!Array.isArray(rows) || rows.length === 0) return;

  const firstRow = rows[0];
  const source = sourceName ? ` from ${sourceName}` : '';
  const values = [
    `Temperature ${formatInputValue(firstRow.ambient_temp_c, '°C')}`,
    `Humidity ${formatInputValue(firstRow.humidity_pct, '%')}`,
    `Solar ${formatInputValue(firstRow.solar_irradiance_wm2, ' W/m²')}`,
  ].join(' · ');

  showToast(`📥 Input received${source}: ${rows.length} hourly rows. First row — ${values}`);
}

function formatInputValue(value, suffix) {
  const number = Number(value);
  return Number.isFinite(number) ? `${number}${suffix}` : `not provided${suffix}`;
}

/* ============================================================
   RENDER FORECAST
   ============================================================ */
function renderForecast(data) {
  currentForecast = data;

  const hours = data.rows?.length || 0;
  document.getElementById('forecastHorizonText').textContent =
    `Hourly microgrid forecast for ${hours} hour${hours === 1 ? '' : 's'}.`;

  updateKPIs(data);
  updateDemandChart(data.rows);
  updateOverloadChart(data.rows, data.summary);
  updateGridState(data.summary, data.rows);
  updateEnergyRouteChart(data.rows);
  updateSOCChart(data.rows);
  updateSystemStatus(data.summary, data.rows);
  updateTable(data.rows);
  updateSignals(data.signals);
  updateQuality(data.quality);
  updateAlertBanner(data.summary, data.rows);
  drawSparklines(data.rows);
  fetchLogs();
}

/* ============================================================
   KPI UPDATES
   ============================================================ */
function updateKPIs(data) {
  const rows = data.rows;
  const summary = data.summary;

  // The API sums hourly kW readings into forecast-horizon energy (kWh).
  const totalEnergy = Number.isFinite(summary.total_energy_kwh)
    ? summary.total_energy_kwh
    : rows.reduce((sum, r) => sum + r.predicted_kw, 0);
  document.getElementById('kpiDemand').innerHTML = `${totalEnergy.toFixed(1)}<span class="kpi-unit">kWh</span>`;
  document.getElementById('kpiDemandTrend').textContent = `${rows.length}-hour forecast`;

  // Peak demand
  const peakRow = rows.reduce((max, r) => r.predicted_kw > max.predicted_kw ? r : max, rows[0]);
  document.getElementById('kpiPeak').innerHTML = `${summary.peak_kw.toFixed(1)}<span class="kpi-unit">kW</span>`;
  const peakHour = timestampHour(peakRow.timestamp);
  document.getElementById('kpiPeakSub').textContent = `at ${String(peakHour).padStart(2, '0')}:00`;
  document.getElementById('heroPeakValue').textContent = summary.peak_kw.toFixed(1);
  document.getElementById('heroPeakTime').textContent = `${String(peakHour).padStart(2, '0')}:00`;

  // Average temperature
  const avgTemp = rows.reduce((sum, r) => sum + r.ambient_temp_c, 0) / rows.length;
  document.getElementById('kpiTemp').innerHTML = `${avgTemp.toFixed(1)}<span class="kpi-unit">°C</span>`;
  document.getElementById('kpiTempSub').textContent = `${rows.length} forecast inputs`;

  // Overload hours
  document.getElementById('kpiOverload').textContent = summary.overload_hours;
  document.getElementById('kpiOverloadSub').textContent = `Out of ${rows.length} forecast hours`;

  // Update weather card temperature
  const currentHour = new Date().getHours();
  const currentRow = rows.find(r => timestampHour(r.timestamp) === currentHour) || rows[0];
  document.querySelector('.weather-temp').innerHTML = `${Math.round(currentRow.ambient_temp_c)}<sup>°C</sup>`;
  document.getElementById('weatherSource').textContent = 'Forecast inputs';
  document.getElementById('weatherDesc').textContent = `Forecast hour ${String(timestampHour(currentRow.timestamp)).padStart(2, '0')}:00`;
}

function timestampHour(timestamp) {
  const match = String(timestamp).match(/(?:T|\s)(\d{1,2}):/);
  if (match) return Number(match[1]);
  const parsed = new Date(timestamp);
  return Number.isNaN(parsed.getTime()) ? 0 : parsed.getHours();
}

/* ============================================================
   DEMAND CHART
   ============================================================ */
function updateDemandChart(rows) {
  const labels = rows.map(r => {
    const h = timestampHour(r.timestamp);
    return String(h).padStart(2, '0') + ':00';
  });
  const predicted = rows.map(r => r.predicted_kw);

  const ctx = document.getElementById('loadChart').getContext('2d');
  if (loadChart) loadChart.destroy();

  loadChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Predicted Demand',
          data: predicted,
          borderColor: C.teal,
          backgroundColor: C.teal,
          fill: false,
          tension: 0.25,
          borderWidth: 4,
          pointBackgroundColor: '#ffffff',
          pointBorderColor: C.teal,
          pointBorderWidth: 2,
          pointRadius: rows.map((r) => {
            const max = Math.max(...predicted);
            return r.predicted_kw === max ? 7 : 4;
          }),
          pointHoverRadius: 8,
          pointHoverBackgroundColor: C.coral,
          pointHoverBorderColor: '#FFFFFF',
          pointHoverBorderWidth: 3,
        },
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => items[0].label,
            label: (item) => {
              const r = rows[item.dataIndex];
              const lines = [
                `Predicted: ${r.predicted_kw.toFixed(1)} kW`,
                `Mode: ${r.mode}`,
              ];
              if (r.overload) lines.push('⚠️ OVERLOAD');
              return lines;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          suggestedMax: 250,
          title: { display: true, text: 'Demand (kW)', color: '#8E9CAE', font: { family: "'Inter', sans-serif", size: 11, weight: 500 } },
          grid: { color: 'rgba(139, 156, 255, 0.16)', drawBorder: false },
          ticks: { color: '#8E9CAE', stepSize: 50, font: { family: "'Inter', sans-serif", size: 11, weight: 500 } }
        },
        x: {
          grid: { display: false },
          ticks: {
            color: '#8E9CAE',
            font: { family: "'Inter', sans-serif", size: 11, weight: 500 },
            callback: function(val, index) {
              const label = this.getLabelForValue(val);
              return (index % 4 === 0) ? label : '';
            },
            autoSkip: false,
            maxRotation: 0
          }
        }
      }
    },
    plugins: [
      {
        id: 'hoverGuide',
        afterDraw(chart) {
          const active = chart.tooltip?.getActiveElements?.() || [];
          if (!active.length) return;
          const { ctx, chartArea } = chart;
          const x = active[0].element.x;
          ctx.save();
          ctx.setLineDash([4, 4]);
          ctx.strokeStyle = C.coral;
          ctx.lineWidth = 2;
          ctx.globalAlpha = 0.8;
          ctx.beginPath();
          ctx.moveTo(x, chartArea.top);
          ctx.lineTo(x, chartArea.bottom);
          ctx.stroke();
          ctx.restore();
        }
      },
      // Threshold lines plugin
      {
        id: 'thresholdLines',
        afterDatasetsDraw(chart) {
          const { ctx, chartArea: area, scales: { y } } = chart;

          // 160 kW threshold (amber)
          const y160 = y.getPixelForValue(160);
          if (y160 >= area.top && y160 <= area.bottom) {
            ctx.save();
            ctx.setLineDash([6, 4]);
            ctx.strokeStyle = C.amber;
            ctx.lineWidth = 1.5;
            ctx.globalAlpha = 0.7;
            ctx.beginPath();
            ctx.moveTo(area.left, y160);
            ctx.lineTo(area.right, y160);
            ctx.stroke();
            ctx.restore();
          }

          // 200 kW threshold (coral)
          const y200 = y.getPixelForValue(200);
          if (y200 >= area.top && y200 <= area.bottom) {
            ctx.save();
            ctx.setLineDash([6, 4]);
            ctx.strokeStyle = C.coral;
            ctx.lineWidth = 1.5;
            ctx.globalAlpha = 0.7;
            ctx.beginPath();
            ctx.moveTo(area.left, y200);
            ctx.lineTo(area.right, y200);
            ctx.stroke();
            ctx.restore();
          }
        }
      },
      // Peak annotation plugin
      {
        id: 'peakAnnotation',
        afterDatasetsDraw(chart) {
          const { ctx, chartArea: area, scales: { x, y } } = chart;
          const data = chart.data.datasets[0].data;
          const maxVal = Math.max(...data);
          const maxIdx = data.indexOf(maxVal);

          const px = x.getPixelForValue(maxIdx);
          const py = y.getPixelForValue(maxVal);

          // Tooltip box
          const text = `${maxVal.toFixed(1)} kW`;
          const timeText = chart.data.labels[maxIdx];
          ctx.save();

          ctx.font = '600 12px Inter, sans-serif';
          const tw = ctx.measureText(text).width;
          const boxW = Math.max(tw + 22, 85);
          const boxH = 40;
          const boxX = Math.max(area.left, Math.min(area.right - boxW, px - boxW / 2));
          const boxY = Math.max(area.top + 4, py - boxH - 12);

          // Background
          ctx.fillStyle = '#20294B';
          ctx.strokeStyle = C.teal;
          ctx.lineWidth = 1;
          roundRect(ctx, boxX, boxY, boxW, boxH, 8);
          ctx.fill();
          ctx.stroke();

          // Value
          ctx.fillStyle = '#FFFFFF';
          ctx.textAlign = 'center';
          ctx.fillText(text, boxX + boxW / 2, boxY + 16);

          // Time
          ctx.font = '400 10px Inter, sans-serif';
          ctx.fillStyle = '#D6D8F0';
          ctx.fillText(timeText, boxX + boxW / 2, boxY + 30);

          ctx.restore();
        }
      }
    ]
  });
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

/* ============================================================
   GRID STATE DOUGHNUT
   ============================================================ */
function updateGridState(summary, rows) {
  const total = rows.length;
  const gridHours = summary.grid_hours ?? 0;
  const batteryHours = summary.renewable_hours ?? 0;

  const gridPct = total ? Math.round((gridHours / total) * 100) : 0;
  document.getElementById('gridPct').textContent = `${gridPct}%`;
  document.getElementById('gsGrid').textContent = `${gridHours} hrs`;
  document.getElementById('gsBattery').textContent = `${batteryHours} hrs`;
  document.getElementById('gridStateTitle').textContent = `Grid State (${total}h forecast)`;
  document.getElementById('controllerGridHours').textContent = `${gridHours} hrs`;
  document.getElementById('controllerBatteryHours').textContent = `${Math.max(0, batteryHours)} hrs`;
  document.getElementById('controllerRenewableHours').textContent = `${Math.max(0, total - gridHours - batteryHours)} hrs`;
  const controllerStatus = document.getElementById('controllerStatusText');
  const controllerPill = document.getElementById('controllerStatusPill');
  if (controllerStatus && controllerPill) {
    controllerStatus.textContent = summary.overload_hours > 0 ? 'Attention required' : 'Balanced operation';
    controllerPill.classList.toggle('warning', summary.overload_hours > 0);
  }

  const ctx = document.getElementById('gridDoughnut').getContext('2d');
  if (gridDoughnut) gridDoughnut.destroy();

  gridDoughnut = new Chart(ctx, {
    type: 'doughnut',
    data: {
        labels: ['Main Grid', 'Renewable Storage'],
      datasets: [{
        data: [gridHours, batteryHours],
        backgroundColor: [C.teal, C.amber],
        borderColor: 'transparent',
        borderWidth: 0,
        borderRadius: 6,
        spacing: 4,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '72%',
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (item) => `${item.label}: ${item.raw} hrs`
          }
        }
      }
    }
  });
}

function updateEnergyRouteChart(rows) {
  const canvas = document.getElementById('energyRouteChart');
  if (!canvas || !rows.length) return;
  const labels = rows.map(r => `${String(timestampHour(r.timestamp)).padStart(2, '0')}:00`);
  const grid = rows.map(row => routeValue(row, 'grid_kw', 'grid'));
  const battery = rows.map(row => routeValue(row, 'battery_supply_kw', 'battery'));
  const solar = rows.map(row => routeValue(row, 'solar_kw', 'solar'));

  const ctx = canvas.getContext('2d');
  if (energyRouteChart) energyRouteChart.destroy();
  const chartHeight = canvas.parentElement.clientHeight;
  const gradients = {
    grid: routeGradient(ctx, '#8B9CFF', chartHeight),
    battery: routeGradient(ctx, '#FFC46B', chartHeight),
    solar: routeGradient(ctx, '#FF7B6E', chartHeight)
  };
  energyRouteChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        routeDataset('Grid', grid, '#8B9CFF', gradients.grid),
        routeDataset('Battery', battery, '#FFC46B', gradients.battery),
        routeDataset('Solar', solar, '#FF7B6E', gradients.solar),
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: items => `${items[0].label} · energy routing`,
            label: item => `${item.dataset.label}: ${item.raw.toFixed(1)} kW`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: 'Energy contribution (kW)', color: '#D6D8F0' },
          grid: { color: 'rgba(139, 156, 255, 0.14)' },
          ticks: { color: '#B6B7D0' }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#B6B7D0', autoSkip: false, maxRotation: 0, callback: (value, index) => index % 4 === 0 ? labels[index] : '' }
        }
      }
    }
  });
}

function routeValue(row, field, fallback) {
  if (Number.isFinite(Number(row[field]))) return Number(row[field]);
  const demand = Math.max(0, Number(row.predicted_kw) || 0);
  const solar = Math.min(demand, Math.max(0, (Number(row.solar_irradiance_wm2) || 0) * 120 / 1000));
  const battery = Math.min(Math.max(0, -(Number(row.battery_kw) || 0)), Math.max(0, demand - solar));
  if (fallback === 'solar') return Number(solar.toFixed(1));
  if (fallback === 'battery') return Number(battery.toFixed(1));
  return Number(Math.max(0, demand - solar - battery).toFixed(1));
}

function routeGradient(ctx, color, height) {
  const gradient = ctx.createLinearGradient(0, 0, 0, height || 280);
  gradient.addColorStop(0, `${color}66`);
  gradient.addColorStop(1, `${color}05`);
  return gradient;
}

function routeDataset(label, data, color, fillColor) {
  return {
    label,
    data,
    borderColor: color,
    backgroundColor: fillColor,
    borderWidth: 3,
    pointRadius: 3,
    pointHoverRadius: 7,
    pointBackgroundColor: color,
    pointHoverBackgroundColor: '#FFFFFF',
    pointHoverBorderColor: color,
    pointHoverBorderWidth: 3,
    tension: 0.25,
    fill: 'origin'
  };
}

/* ============================================================
   BATTERY SOC CHART
   ============================================================ */
function updateSOCChart(rows) {
  const labels = rows.map(r => {
    const h = timestampHour(r.timestamp);
    return String(h).padStart(2, '0') + ':00';
  });
  const socValues = rows.map(r => r.soc_pct);

  // Update badge
  const lastSoc = socValues[socValues.length - 1] || socValues[0];
  const badge = document.getElementById('batteryBadge');
  const badgePct = document.getElementById('batteryPct');
  badgePct.textContent = `${Math.round(lastSoc)}%`;

  if (lastSoc <= 15) {
    badge.className = 'battery-badge critical';
  } else if (lastSoc <= 30) {
    badge.className = 'battery-badge warning';
  } else {
    badge.className = 'battery-badge good';
  }

  const ctx = document.getElementById('socChart').getContext('2d');
  if (socChart) socChart.destroy();

  socChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'SoC (%)',
        data: socValues,
        borderColor: C.violet,
        backgroundColor: C.violet,
        fill: false,
        tension: 0.4,
        pointBackgroundColor: C.violet,
        pointBorderColor: C.violet,
        pointRadius: 2,
        pointHoverRadius: 5,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (item) => `SoC: ${item.raw.toFixed(1)}%`
          }
        }
      },
      scales: {
        y: {
          min: 0,
          max: 100,
          title: { display: true, text: 'SoC (%)', color: '#8E9CAE', font: { family: "'Inter', sans-serif", size: 10, weight: 500 } },
          grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false },
          ticks: { color: '#8E9CAE', stepSize: 50, font: { family: "'Inter', sans-serif", size: 10, weight: 500 } }
        },
        x: {
          grid: { display: false },
          ticks: {
            color: '#8E9CAE',
            font: { family: "'Inter', sans-serif", size: 10, weight: 500 },
            callback: function(val, index) {
              const label = this.getLabelForValue(val);
              return (index % 4 === 0) ? label : '';
            },
            autoSkip: false,
            maxRotation: 0
          }
        }
      }
    },
    plugins: [{
      id: 'reserveLine',
      afterDatasetsDraw(chart) {
        const { ctx, chartArea: area, scales: { y } } = chart;
        const y10 = y.getPixelForValue(10);
        if (y10 >= area.top && y10 <= area.bottom) {
          ctx.save();
          ctx.setLineDash([4, 3]);
          ctx.strokeStyle = C.coral;
          ctx.lineWidth = 1;
          ctx.globalAlpha = 0.6;
          ctx.beginPath();
          ctx.moveTo(area.left, y10);
          ctx.lineTo(area.right, y10);
          ctx.stroke();
          ctx.restore();
        }
      }
    }]
  });
}

/* ============================================================
   SYSTEM STATUS
   ============================================================ */
function updateSystemStatus(summary, rows) {
  const indicator = document.getElementById('statusIndicator');
  const heading = document.getElementById('statusHeading');
  const desc = document.getElementById('statusDesc');

  if (summary.overload_hours > 0) {
    const firstOverload = rows.find(r => r.overload);
    const overloadTime = firstOverload
      ? new Date(firstOverload.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      : 'unknown';

    if (summary.overload_hours >= 4) {
      indicator.className = 'status-indicator critical';
      heading.className = 'status-heading critical';
      heading.textContent = 'Critical Overload';
      desc.textContent = `${summary.overload_hours} hours ≥ 200 kW detected. First at ${overloadTime}. Immediate action required.`;
    } else {
      indicator.className = 'status-indicator warning';
      heading.className = 'status-heading warning';
      heading.textContent = 'Warning — Overload Expected';
      desc.textContent = `${summary.overload_hours} hour(s) ≥ 200 kW predicted. First at ${overloadTime}.`;
    }
  } else {
    indicator.className = 'status-indicator normal';
    heading.className = 'status-heading normal';
    heading.textContent = 'Operating Normally';
    desc.textContent = 'All parameters within safe limits. No overload expected.';
  }

  // Update wave color
  const wave = document.getElementById('statusWave');
  if (summary.overload_hours > 0) {
    const color = summary.overload_hours >= 4 ? 'rgba(255,100,124,' : 'rgba(255,184,77,';
    wave.innerHTML = `<svg viewBox="0 0 400 30" preserveAspectRatio="none">
      <path d="M0,15 C40,5 80,25 120,15 C160,5 200,25 240,15 C280,5 320,25 360,15 C380,10 400,15 400,15" fill="none" stroke="${color}0.25)" stroke-width="1.5"/>
      <path d="M0,18 C50,8 100,28 150,18 C200,8 250,28 300,18 C350,8 400,18 400,18" fill="none" stroke="${color}0.12)" stroke-width="1"/>
    </svg>`;
  } else {
    wave.innerHTML = `<svg viewBox="0 0 400 30" preserveAspectRatio="none">
      <path d="M0,15 C40,5 80,25 120,15 C160,5 200,25 240,15 C280,5 320,25 360,15 C380,10 400,15 400,15" fill="none" stroke="rgba(57,245,208,0.25)" stroke-width="1.5"/>
      <path d="M0,18 C50,8 100,28 150,18 C200,8 250,28 300,18 C350,8 400,18 400,18" fill="none" stroke="rgba(57,245,208,0.12)" stroke-width="1"/>
    </svg>`;
  }
}

/* ============================================================
   ALERT BANNER
   ============================================================ */
function updateAlertBanner(summary, rows) {
  const banner = document.getElementById('alertBanner');
  if (summary.overload_hours > 0) {
    const firstOverload = rows.find(r => r.overload);
    const time = firstOverload
      ? new Date(firstOverload.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      : '';
    banner.className = 'alert-banner critical';
    banner.innerHTML = `🚨 Critical Overload: ${summary.overload_hours} hour(s) ≥ 200 kW${time ? ` (first at ${time})` : ''}`;
    banner.hidden = false;
  } else {
    banner.hidden = true;
  }
}

/* ============================================================
   SPARKLINES
   ============================================================ */
function drawSparklines(rows) {
  drawSparkline('sparkDemand', rows.map(r => r.predicted_kw), C.teal);
  drawSparkline('sparkPeak', rows.map(r => r.predicted_kw), C.amber);
  drawSparkline('sparkTemp', rows.map(r => r.ambient_temp_c), C.aqua);
  drawSparkline('sparkOverload', rows.map(r => r.overload ? 1 : 0), C.coral);
}

function drawSparkline(canvasId, data, color) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !data || data.length < 2) return;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const w = 130;
  const h = 48;
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, w, h);

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const step = w / (data.length - 1);

  const points = data.map((v, i) => ({
    x: i * step,
    y: h - ((v - min) / range) * (h - 14) - 7
  }));

  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 0; i < points.length - 1; i++) {
    const xc = (points[i].x + points[i + 1].x) / 2;
    const yc = (points[i].y + points[i + 1].y) / 2;
    ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
  }
  ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);

  ctx.shadowColor = color;
  ctx.shadowBlur = 10;
  ctx.strokeStyle = color;
  ctx.lineWidth = 2.5;
  ctx.lineCap = 'round';
  ctx.stroke();
}

/* ============================================================
   DATA TABLE
   ============================================================ */
function updateTable(rows) {
  const tbody = document.querySelector('#forecastTable tbody');
  const empty = document.getElementById('tableEmpty');
  tbody.innerHTML = '';

  if (!rows || rows.length === 0) {
    empty.style.display = '';
    return;
  }
  empty.style.display = 'none';

  rows.forEach(r => {
    const tr = document.createElement('tr');
    const hour = new Date(r.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const modeClass = r.mode === 'RENEWABLE_STORAGE' ? 'mode-battery' : 'mode-grid';
    const modeLabel = r.mode === 'RENEWABLE_STORAGE' ? 'Battery' : 'Grid';

    tr.innerHTML = `
      <td style="color: var(--text-primary); font-weight: 550;">${hour}</td>
      <td>${r.ambient_temp_c.toFixed(1)}</td>
      <td>${r.humidity_pct.toFixed(1)}</td>
      <td>${r.solar_irradiance_wm2.toFixed(0)}</td>
      <td style="color: var(--text-primary); font-weight: 600;">${r.predicted_kw.toFixed(2)}</td>
      <td><span class="mode-badge ${modeClass}">${modeLabel}</span></td>
      <td style="font-size: 0.78rem;">${r.reason}</td>
      <td class="${r.overload ? 'overload-yes' : 'overload-no'}">${r.overload ? '⚠️ YES' : 'No'}</td>
      <td>${r.soc_pct.toFixed(1)}%</td>
    `;
    tbody.appendChild(tr);
  });
}

function filterTable(query) {
  const rows = document.querySelectorAll('#forecastTable tbody tr');
  const q = query.toLowerCase();
  rows.forEach(tr => {
    tr.style.display = tr.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}

/* ============================================================
   SIGNALS
   ============================================================ */
function updateSignals(signals) {
  const container = document.getElementById('signalsList');
  const count = document.getElementById('signalCount');
  container.innerHTML = '';
  count.textContent = `${signals.length} signal${signals.length !== 1 ? 's' : ''}`;

  if (signals.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>No control signals</p></div>';
    return;
  }

  signals.forEach(s => {
    const div = document.createElement('div');
    div.className = 'signal-item' + (s.command.includes('OVERLOAD') ? ' critical' : '');
    div.innerHTML = `
      <span class="signal-time">${new Date(s.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
      <span class="signal-cmd">${s.command}</span>
      <span class="signal-detail">${s.detail}</span>
    `;
    container.appendChild(div);
  });
}

/* ============================================================
   QUALITY
   ============================================================ */
function updateQuality(quality) {
  if (!quality) return;
  const grid = document.getElementById('qualityGrid');
  grid.innerHTML = `
    <div class="quality-item"><span>Rows Processed</span><strong>${quality.rows || 0}</strong></div>
    <div class="quality-item"><span>Bad Timestamps</span><strong>${quality.bad_timestamps || 0}</strong></div>
    <div class="quality-item"><span>Missing Filled</span><strong>${quality.missing_filled || 0}</strong></div>
    <div class="quality-item"><span>Values Clipped</span><strong>${quality.clipped || 0}</strong></div>
    <div class="quality-item"><span>Duplicates</span><strong>${quality.duplicates || 0}</strong></div>
  `;

  const warnContainer = document.getElementById('qualityWarnings');
  if (quality.warnings && quality.warnings.length > 0) {
    warnContainer.hidden = false;
    warnContainer.innerHTML = '<strong>Warnings:</strong><ul>' +
      quality.warnings.map(w => `<li>${w}</li>`).join('') + '</ul>';
  } else {
    warnContainer.hidden = true;
  }
}

/* ============================================================
   LOGS
   ============================================================ */
async function fetchLogs() {
  try {
    const res = await fetch('/api/logs');
    const data = await res.json();
    const container = document.getElementById('logsList');
    container.innerHTML = '';

    if (data.logs && data.logs.length > 0) {
      data.logs.slice(0, 20).forEach(log => {
        const div = document.createElement('div');
        div.className = 'log-entry ' + (log.level || 'info');
        div.innerHTML = `
          <span class="log-time">${new Date(log.created_at).toLocaleTimeString()}</span>
          <span class="log-msg">${log.message}</span>
        `;
        container.appendChild(div);
      });
    } else {
      container.innerHTML = '<div class="empty-state"><p>No system events yet. Run a forecast to create a log.</p></div>';
    }
  } catch (e) {
    const container = document.getElementById('logsList');
    if (container) {
      container.innerHTML = '<div class="empty-state"><p>System logs are temporarily unavailable.</p></div>';
    }
  }
}

/* ============================================================
   CSV DOWNLOAD
   ============================================================ */
function downloadCSV() {
  if (!currentForecast) return;

  let csv = 'timestamp,target_demand_kw\n';
  currentForecast.rows.forEach(r => {
    csv += `${r.timestamp},${r.predicted_kw.toFixed(4)}\n`;
  });

  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'predictions_' + currentForecast.run_id + '.csv';
  a.click();
  URL.revokeObjectURL(url);
}

/* ============================================================
   UI HELPERS
   ============================================================ */
function showLoading(msg) {
  const overlay = document.getElementById('loadingOverlay');
  const text = document.getElementById('loadingText');
  text.textContent = msg || 'Processing…';
  overlay.hidden = false;
}

function hideLoading() {
  document.getElementById('loadingOverlay').hidden = true;
}

function showError(msg) {
  hideLoading();
  const banner = document.getElementById('alertBanner');
  banner.className = 'alert-banner critical';
  banner.innerHTML = `❌ ${msg}`;
  banner.hidden = false;
}

function showToast(msg) {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 300ms ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}
