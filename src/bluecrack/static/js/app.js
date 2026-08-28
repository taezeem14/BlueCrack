/* ═══════════════════════════════════════════════════════════════════
   BlueCrack — Modern Frontend Application Logic (ES6+)
   Ultra-Lightweight & GPU Optimized (128MB iGPU Ready)
   ═══════════════════════════════════════════════════════════════════ */

'use strict';

// ─── Socket.IO Connection ──────────────────────────────────────────
const socket = io({
  transports: ['websocket', 'polling'],
  reconnection: true,
  reconnectionDelay: 1000,
});

// ─── Safe HTML Escaping Helper ─────────────────────────────────────
function escapeHTML(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ─── Toast Notification System ─────────────────────────────────────
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const iconMap = {
    success: 'fa-solid fa-circle-check text-emerald',
    error:   'fa-solid fa-circle-exclamation text-rose',
    info:    'fa-solid fa-circle-info text-cyan',
  };

  toast.innerHTML = `
    <i class="${iconMap[type] || iconMap.info}"></i>
    <span>${escapeHTML(message)}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'all 0.2s ease';
    setTimeout(() => toast.remove(), 200);
  }, 3500);
}

// ─── DOM References ────────────────────────────────────────────────
const DOM = {
  // Header Actions
  btnLaunchDemo:   document.getElementById('btnLaunchDemo'),
  btnDoctor:       document.getElementById('btnDoctor'),
  btnInfo:         document.getElementById('btnInfo'),

  // Connection status
  connectionDot:   document.getElementById('connectionDot'),
  connectionLabel: document.getElementById('connectionLabel'),
  connectionPill:  document.getElementById('connectionPill'),

  // Floating Info & Welcome Modal
  tutorialModal:             document.getElementById('tutorialModal'),
  btnCloseModal:             document.getElementById('btnCloseModal'),
  btnAgreeDisclaimer:        document.getElementById('btnAgreeDisclaimer'),
  btnShowTutorialFromStart:  document.getElementById('btnShowTutorialFromStart'),
  btnBackToDisclaimer:       document.getElementById('btnBackToDisclaimer'),
  btnFinishTutorial:         document.getElementById('btnFinishTutorial'),
  panelDisclaimer:           document.getElementById('panelDisclaimer'),
  panelTutorial:             document.getElementById('panelTutorial'),
  tutTabButtons:             document.querySelectorAll('.tut-tab-btn'),
  tutContents:               document.querySelectorAll('.tut-content'),

  // Tab system
  tabButtons: document.querySelectorAll('.tab-btn'),
  tabPanels:  document.querySelectorAll('.tab-content'),

  // Target Config
  targetUrl:       document.getElementById('targetUrl'),
  btnScanTarget:   document.getElementById('btnScanTarget'),
  targetTechBadge: document.getElementById('targetTechBadge'),
  username:        document.getElementById('username'),
  password:        document.getElementById('password'),
  errorString:     document.getElementById('errorString'),
  successString:   document.getElementById('successString'),

  // Engine Settings
  attackMode:           document.getElementById('attackMode'),
  httpModeOptions:      document.getElementById('httpModeOptions'),
  headlessGroup:        document.getElementById('headlessGroup'),
  threads:              document.getElementById('threads'),
  delay:                document.getElementById('delay'),
  jitter:               document.getElementById('jitter'),
  rateLimit:            document.getElementById('rateLimit'),
  cooldown:             document.getElementById('cooldown'),
  maxAttempts:          document.getElementById('maxAttempts'),
  headless:             document.getElementById('headless'),
  continueAfterSuccess: document.getElementById('continueAfterSuccess'),
  sprayMode:            document.getElementById('sprayMode'),

  // HTTP Mode Options
  formAction:         document.getElementById('formAction'),
  usernameField:      document.getElementById('usernameField'),
  passwordField:      document.getElementById('passwordField'),
  csrfField:          document.getElementById('csrfField'),
  followRedirects:    document.getElementById('followRedirects'),
  jsonMode:           document.getElementById('jsonMode'),
  customHeaders:      document.getElementById('customHeaders'),
  customCookies:      document.getElementById('customCookies'),
  successStatusCodes: document.getElementById('successStatusCodes'),

  // Tor & Proxy
  enableTor:      document.getElementById('enableTor'),
  torControlPort: document.getElementById('torControlPort'),
  torShiftEvery:  document.getElementById('torShiftEvery'),
  proxy:          document.getElementById('proxy'),

  // CUPP Generator
  cuppFirstName:        document.getElementById('cuppFirstName'),
  cuppLastName:         document.getElementById('cuppLastName'),
  cuppNickname:         document.getElementById('cuppNickname'),
  cuppBirthdate:        document.getElementById('cuppBirthdate'),
  cuppPartnerName:      document.getElementById('cuppPartnerName'),
  cuppPartnerNickname:  document.getElementById('cuppPartnerNickname'),
  cuppPartnerBirthdate: document.getElementById('cuppPartnerBirthdate'),
  cuppChildName:        document.getElementById('cuppChildName'),
  cuppChildBirthdate:   document.getElementById('cuppChildBirthdate'),
  cuppPetName:          document.getElementById('cuppPetName'),
  cuppCompany:          document.getElementById('cuppCompany'),
  cuppKeywords:         document.getElementById('cuppKeywords'),
  cuppSpecialChars:     document.getElementById('cuppSpecialChars'),
  cuppRandomNumbers:    document.getElementById('cuppRandomNumbers'),
  cuppLeet:             document.getElementById('cuppLeet'),
  btnGenerateCupp:      document.getElementById('btnGenerateCupp'),
  btnUseCupp:           document.getElementById('btnUseCupp'),
  cuppStatus:           document.getElementById('cuppStatus'),

  // Sequence Generator
  seqStart:       document.getElementById('seqStart'),
  seqEnd:         document.getElementById('seqEnd'),
  seqPadding:     document.getElementById('seqPadding'),
  seqPrefix:      document.getElementById('seqPrefix'),
  seqSuffix:      document.getElementById('seqSuffix'),
  btnGenerateSeq: document.getElementById('btnGenerateSeq'),
  btnUseSeq:      document.getElementById('btnUseSeq'),
  seqStatus:      document.getElementById('seqStatus'),

  // Control bar
  btnStart:        document.getElementById('btnStart'),
  btnStop:         document.getElementById('btnStop'),
  btnExport:       document.getElementById('btnExport'),
  btnClear:        document.getElementById('btnClear'),
  btnReport:       document.getElementById('btnReport'),
  btnDownloadJson: document.getElementById('btnDownloadJson'),
  btnResetConfig:  document.getElementById('btnResetConfig'),

  // Doctor modal
  doctorModal:           document.getElementById('doctorModal'),
  btnCloseDoctor:        document.getElementById('btnCloseDoctor'),
  btnCloseDoctorBtn:     document.getElementById('btnCloseDoctorBtn'),
  btnRerunDoctor:        document.getElementById('btnRerunDoctor'),
  doctorChecksContainer: document.getElementById('doctorChecksContainer'),

  // Stats
  statElapsed:   document.getElementById('statElapsed'),
  statSpeed:     document.getElementById('statSpeed'),
  statEta:       document.getElementById('statEta'),
  statHits:      document.getElementById('statHits'),
  statAttempted: document.getElementById('statAttempted'),
  statErrors:    document.getElementById('statErrors'),

  // Progress
  progressFill: document.getElementById('progressFill'),
  progressText: document.getElementById('progressText'),

  // Terminal & Tools
  terminal:          document.getElementById('terminal'),
  terminalFilter:    document.getElementById('terminalFilter'),
  btnCopyTerminal:   document.getElementById('btnCopyTerminal'),
  btnAutoScroll:     document.getElementById('btnAutoScroll'),

  // Session resume
  resumeBanner:      document.getElementById('resumeBanner'),
  btnResume:         document.getElementById('btnResume'),
  btnDismissResume:  document.getElementById('btnDismissResume'),

  // Multi-target queue
  btnAddTarget:       document.getElementById('btnAddTarget'),
  btnStartAllTargets: document.getElementById('btnStartAllTargets'),
  targetList:         document.getElementById('targetList'),

  // Scheduler
  scheduleTime:      document.getElementById('scheduleTime'),
  btnScheduleAttack: document.getElementById('btnScheduleAttack'),
  scheduleList:      document.getElementById('scheduleList'),

  // Alerts
  discordWebhook:       document.getElementById('discordWebhook'),
  btnTestDiscord:       document.getElementById('btnTestDiscord'),
  telegramToken:        document.getElementById('telegramToken'),
  telegramChatId:       document.getElementById('telegramChatId'),
  btnTestTelegram:      document.getElementById('btnTestTelegram'),
  btnSaveNotifications: document.getElementById('btnSaveNotifications'),
  notifStatus:          document.getElementById('notifStatus'),
};

// Cached generator paths
let cuppResultPath = null;
let sequenceResultPath = null;
let autoScrollEnabled = true;

// ─── Tab Switching & Mode Changes ──────────────────────────────────
function switchTab(targetId) {
  if (!targetId) return;
  DOM.tabButtons.forEach(btn => {
    const isTarget = btn.dataset.tab === targetId;
    btn.classList.toggle('active', isTarget);
    btn.setAttribute('aria-selected', isTarget);
  });

  DOM.tabPanels.forEach(panel => {
    panel.classList.toggle('active', panel.id === `tab-${targetId}`);
  });

  try {
    localStorage.setItem('bluecrack_active_tab', targetId);
  } catch (e) {}
}

function onModeChange() {
  if (!DOM.attackMode) return;
  const isHttp = DOM.attackMode.value === 'http';
  if (DOM.httpModeOptions) DOM.httpModeOptions.style.display = isHttp ? 'flex' : 'none';
  if (DOM.headlessGroup) DOM.headlessGroup.style.display = isHttp ? 'none' : 'inline-flex';
  if (isHttp && parseInt(DOM.threads?.value || '1', 10) <= 1 && DOM.threads) {
    DOM.threads.value = '4';
  }
}

// ─── Form State Serialization & Persistence ────────────────────────
function getFormState() {
  return {
    target_url: DOM.targetUrl?.value || '',
    username: DOM.username?.value || '',
    password: DOM.password?.value || '',
    error_msg: DOM.errorString?.value || '',
    success_msg: DOM.successString?.value || '',

    attack_mode: DOM.attackMode?.value || 'browser',
    threads: DOM.threads?.value || '1',
    delay: DOM.delay?.value || '0',
    jitter: DOM.jitter?.value || '0',
    rate_limit: DOM.rateLimit?.value || '',
    cooldown: DOM.cooldown?.value || '12',
    max_attempts: DOM.maxAttempts?.value || '0',
    headless: DOM.headless ? DOM.headless.checked : true,
    continue_after_success: DOM.continueAfterSuccess ? DOM.continueAfterSuccess.checked : false,
    spray_mode: DOM.sprayMode ? DOM.sprayMode.checked : false,

    form_action: DOM.formAction?.value || '',
    username_field: DOM.usernameField?.value || '',
    password_field: DOM.passwordField?.value || '',
    csrf_field: DOM.csrfField?.value || '',
    follow_redirects: DOM.followRedirects ? DOM.followRedirects.checked : false,
    json_mode: DOM.jsonMode ? DOM.jsonMode.checked : false,
    custom_headers: DOM.customHeaders?.value || '',
    custom_cookies: DOM.customCookies?.value || '',
    success_status_codes: DOM.successStatusCodes?.value || '',

    enable_tor: DOM.enableTor ? DOM.enableTor.checked : false,
    tor_control_port: DOM.torControlPort?.value || '9051',
    tor_shift_every: DOM.torShiftEvery?.value || '10',
    proxy: DOM.proxy?.value || '',

    discord_webhook: DOM.discordWebhook?.value || '',
    telegram_token: DOM.telegramToken?.value || '',
    telegram_chat_id: DOM.telegramChatId?.value || '',

    cupp_first_name: DOM.cuppFirstName?.value || '',
    cupp_last_name: DOM.cuppLastName?.value || '',
    cupp_nickname: DOM.cuppNickname?.value || '',
    cupp_birthdate: DOM.cuppBirthdate?.value || '',
    cupp_partner_name: DOM.cuppPartnerName?.value || '',
    cupp_partner_nickname: DOM.cuppPartnerNickname?.value || '',
    cupp_partner_birthdate: DOM.cuppPartnerBirthdate?.value || '',
    cupp_child_name: DOM.cuppChildName?.value || '',
    cupp_child_birthdate: DOM.cuppChildBirthdate?.value || '',
    cupp_pet_name: DOM.cuppPetName?.value || '',
    cupp_company: DOM.cuppCompany?.value || '',
    cupp_keywords: DOM.cuppKeywords?.value || '',
    cupp_special_chars: DOM.cuppSpecialChars ? DOM.cuppSpecialChars.checked : false,
    cupp_random_numbers: DOM.cuppRandomNumbers ? DOM.cuppRandomNumbers.checked : false,
    cupp_leet: DOM.cuppLeet ? DOM.cuppLeet.checked : false,

    seq_start: DOM.seqStart?.value || '0',
    seq_end: DOM.seqEnd?.value || '9999',
    seq_padding: DOM.seqPadding?.value || '4',
    seq_prefix: DOM.seqPrefix?.value || '',
    seq_suffix: DOM.seqSuffix?.value || '',
  };
}

let saveTimer = null;
function saveFormState() {
  const state = getFormState();
  try {
    localStorage.setItem('bluecrack_config', JSON.stringify(state));
  } catch (e) {}

  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    postJSON('/api/config/save', state).catch(() => {});
  }, 400);
}

async function restoreFormState() {
  let state = null;
  try {
    const raw = localStorage.getItem('bluecrack_config');
    if (raw) state = JSON.parse(raw);
  } catch (e) {}

  if (!state) {
    try {
      const res = await fetch('/api/config/load');
      const data = await res.json();
      if (data.status === 'ok' && data.config && Object.keys(data.config).length > 0) {
        state = data.config;
      }
    } catch (e) {}
  }

  if (!state) return;

  if (state.target_url !== undefined && DOM.targetUrl) DOM.targetUrl.value = state.target_url;
  if (state.username !== undefined && DOM.username) DOM.username.value = state.username;
  if (state.password !== undefined && DOM.password) DOM.password.value = state.password;
  if (state.error_msg !== undefined && DOM.errorString) DOM.errorString.value = state.error_msg;
  if (state.success_msg !== undefined && DOM.successString) DOM.successString.value = state.success_msg;

  if (state.attack_mode !== undefined && DOM.attackMode) DOM.attackMode.value = state.attack_mode;
  if (state.threads !== undefined && DOM.threads) DOM.threads.value = state.threads;
  if (state.delay !== undefined && DOM.delay) DOM.delay.value = state.delay;
  if (state.jitter !== undefined && DOM.jitter) DOM.jitter.value = state.jitter;
  if (state.rate_limit !== undefined && DOM.rateLimit) DOM.rateLimit.value = state.rate_limit;
  if (state.cooldown !== undefined && DOM.cooldown) DOM.cooldown.value = state.cooldown;
  if (state.max_attempts !== undefined && DOM.maxAttempts) DOM.maxAttempts.value = state.max_attempts;
  if (state.headless !== undefined && DOM.headless) DOM.headless.checked = Boolean(state.headless);
  if (state.continue_after_success !== undefined && DOM.continueAfterSuccess) DOM.continueAfterSuccess.checked = Boolean(state.continue_after_success);
  if (state.spray_mode !== undefined && DOM.sprayMode) DOM.sprayMode.checked = Boolean(state.spray_mode);

  if (state.form_action !== undefined && DOM.formAction) DOM.formAction.value = state.form_action;
  if (state.username_field !== undefined && DOM.usernameField) DOM.usernameField.value = state.username_field;
  if (state.password_field !== undefined && DOM.passwordField) DOM.passwordField.value = state.password_field;
  if (state.csrf_field !== undefined && DOM.csrfField) DOM.csrfField.value = state.csrf_field;
  if (state.follow_redirects !== undefined && DOM.followRedirects) DOM.followRedirects.checked = Boolean(state.follow_redirects);
  if (state.json_mode !== undefined && DOM.jsonMode) DOM.jsonMode.checked = Boolean(state.json_mode);
  if (state.custom_headers !== undefined && DOM.customHeaders) DOM.customHeaders.value = state.custom_headers;
  if (state.custom_cookies !== undefined && DOM.customCookies) DOM.customCookies.value = state.custom_cookies;
  if (state.success_status_codes !== undefined && DOM.successStatusCodes) DOM.successStatusCodes.value = state.success_status_codes;

  if (state.enable_tor !== undefined && DOM.enableTor) DOM.enableTor.checked = Boolean(state.enable_tor);
  if (state.tor_control_port !== undefined && DOM.torControlPort) DOM.torControlPort.value = state.tor_control_port;
  if (state.tor_shift_every !== undefined && DOM.torShiftEvery) DOM.torShiftEvery.value = state.tor_shift_every;
  if (state.proxy !== undefined && DOM.proxy) DOM.proxy.value = state.proxy;

  if (state.discord_webhook !== undefined && DOM.discordWebhook) DOM.discordWebhook.value = state.discord_webhook;
  if (state.telegram_token !== undefined && DOM.telegramToken) DOM.telegramToken.value = state.telegram_token;
  if (state.telegram_chat_id !== undefined && DOM.telegramChatId) DOM.telegramChatId.value = state.telegram_chat_id;

  if (state.cupp_first_name !== undefined && DOM.cuppFirstName) DOM.cuppFirstName.value = state.cupp_first_name;
  if (state.cupp_last_name !== undefined && DOM.cuppLastName) DOM.cuppLastName.value = state.cupp_last_name;
  if (state.cupp_nickname !== undefined && DOM.cuppNickname) DOM.cuppNickname.value = state.cupp_nickname;
  if (state.cupp_birthdate !== undefined && DOM.cuppBirthdate) DOM.cuppBirthdate.value = state.cupp_birthdate;
  if (state.cupp_partner_name !== undefined && DOM.cuppPartnerName) DOM.cuppPartnerName.value = state.cupp_partner_name;
  if (state.cupp_partner_nickname !== undefined && DOM.cuppPartnerNickname) DOM.cuppPartnerNickname.value = state.cupp_partner_nickname;
  if (state.cupp_partner_birthdate !== undefined && DOM.cuppPartnerBirthdate) DOM.cuppPartnerBirthdate.value = state.cupp_partner_birthdate;
  if (state.cupp_child_name !== undefined && DOM.cuppChildName) DOM.cuppChildName.value = state.cupp_child_name;
  if (state.cupp_child_birthdate !== undefined && DOM.cuppChildBirthdate) DOM.cuppChildBirthdate.value = state.cupp_child_birthdate;
  if (state.cupp_pet_name !== undefined && DOM.cuppPetName) DOM.cuppPetName.value = state.cupp_pet_name;
  if (state.cupp_company !== undefined && DOM.cuppCompany) DOM.cuppCompany.value = state.cupp_company;
  if (state.cupp_keywords !== undefined && DOM.cuppKeywords) DOM.cuppKeywords.value = state.cupp_keywords;
  if (state.cupp_special_chars !== undefined && DOM.cuppSpecialChars) DOM.cuppSpecialChars.checked = Boolean(state.cupp_special_chars);
  if (state.cupp_random_numbers !== undefined && DOM.cuppRandomNumbers) DOM.cuppRandomNumbers.checked = Boolean(state.cupp_random_numbers);
  if (state.cupp_leet !== undefined && DOM.cuppLeet) DOM.cuppLeet.checked = Boolean(state.cupp_leet);

  if (state.seq_start !== undefined && DOM.seqStart) DOM.seqStart.value = state.seq_start;
  if (state.seq_end !== undefined && DOM.seqEnd) DOM.seqEnd.value = state.seq_end;
  if (state.seq_padding !== undefined && DOM.seqPadding) DOM.seqPadding.value = state.seq_padding;
  if (state.seq_prefix !== undefined && DOM.seqPrefix) DOM.seqPrefix.value = state.seq_prefix;
  if (state.seq_suffix !== undefined && DOM.seqSuffix) DOM.seqSuffix.value = state.seq_suffix;

  onModeChange();

  if (state.discord_webhook || (state.telegram_token && state.telegram_chat_id)) {
    postJSON('/api/notifications/configure', {
      discord_url: state.discord_webhook || '',
      telegram_token: state.telegram_token || '',
      telegram_chat_id: state.telegram_chat_id || '',
    }).catch(() => {});
  }
}

async function resetFormState() {
  try {
    localStorage.removeItem('bluecrack_config');
    await postJSON('/api/config/reset', {});
    await postJSON('/api/attack/reset', {});
  } catch (e) {}

  resetStats();
  setProgress(0);
  if (DOM.terminal) DOM.terminal.innerHTML = '';

  if (DOM.targetUrl) DOM.targetUrl.value = '';
  if (DOM.username) DOM.username.value = '';
  if (DOM.password) DOM.password.value = '';
  if (DOM.errorString) DOM.errorString.value = '';
  if (DOM.successString) DOM.successString.value = '';

  if (DOM.attackMode) DOM.attackMode.value = 'browser';
  if (DOM.threads) DOM.threads.value = '1';
  if (DOM.delay) DOM.delay.value = '0';
  if (DOM.jitter) DOM.jitter.value = '0';
  if (DOM.rateLimit) DOM.rateLimit.value = 'too many requests';
  if (DOM.cooldown) DOM.cooldown.value = '12';
  if (DOM.maxAttempts) DOM.maxAttempts.value = '0';
  if (DOM.headless) DOM.headless.checked = true;
  if (DOM.continueAfterSuccess) DOM.continueAfterSuccess.checked = false;
  if (DOM.sprayMode) DOM.sprayMode.checked = false;

  if (DOM.formAction) DOM.formAction.value = '';
  if (DOM.usernameField) DOM.usernameField.value = '';
  if (DOM.passwordField) DOM.passwordField.value = '';
  if (DOM.csrfField) DOM.csrfField.value = '';
  if (DOM.followRedirects) DOM.followRedirects.checked = false;
  if (DOM.jsonMode) DOM.jsonMode.checked = false;
  if (DOM.customHeaders) DOM.customHeaders.value = '';
  if (DOM.customCookies) DOM.customCookies.value = '';
  if (DOM.successStatusCodes) DOM.successStatusCodes.value = '';

  if (DOM.enableTor) DOM.enableTor.checked = false;
  if (DOM.torControlPort) DOM.torControlPort.value = '9051';
  if (DOM.torShiftEvery) DOM.torShiftEvery.value = '10';
  if (DOM.proxy) DOM.proxy.value = '';

  if (DOM.discordWebhook) DOM.discordWebhook.value = '';
  if (DOM.telegramToken) DOM.telegramToken.value = '';
  if (DOM.telegramChatId) DOM.telegramChatId.value = '';

  onModeChange();
  appendLog('[~] Form parameters and metrics reset to factory defaults.');
  showToast('Configuration and stats reset to defaults', 'info');
}

function bindAutoSave() {
  const inputs = document.querySelectorAll('input:not(#terminalFilter), select, textarea');
  inputs.forEach(el => {
    el.addEventListener('input', saveFormState);
    el.addEventListener('change', saveFormState);
  });
}

// ─── Timing & Formatting Helpers ───────────────────────────────────
function formatTime(totalSeconds) {
  if (totalSeconds == null || totalSeconds < 0 || !isFinite(totalSeconds)) {
    return '--:--:--';
  }
  const s = Math.floor(totalSeconds);
  const hh = String(Math.floor(s / 3600)).padStart(2, '0');
  const mm = String(Math.floor((s % 3600) / 60)).padStart(2, '0');
  const ss = String(s % 60).padStart(2, '0');
  return `${hh}:${mm}:${ss}`;
}

function getLogClass(message) {
  if (message.includes('VALID CREDENTIALS') || message.includes('HIT')) return 'log-hit';
  if (message.startsWith('[+]')) return 'log-success';
  if (message.startsWith('[-]')) return 'log-error';
  if (message.startsWith('[!]')) return 'log-warn';
  if (message.startsWith('[*]')) return 'log-info';
  if (message.startsWith('[~]')) return 'log-system';
  return '';
}

// ─── High-Performance Terminal Streaming Buffer ────────────────────
const logBuffer = [];
let isLoggingScheduled = false;
const MAX_LOG_LINES = 600;

function flushLogs() {
  if (logBuffer.length === 0) {
    isLoggingScheduled = false;
    return;
  }

  const fragment = document.createDocumentFragment();
  const filterQuery = DOM.terminalFilter?.value.toLowerCase().trim() || '';
  const linesToRender = logBuffer.splice(0, 100);

  linesToRender.forEach(message => {
    const line = document.createElement('div');
    line.className = `log-entry ${getLogClass(message)}`;
    line.textContent = message;
    if (filterQuery && !message.toLowerCase().includes(filterQuery)) {
      line.style.display = 'none';
    }
    fragment.appendChild(line);
  });

  DOM.terminal.appendChild(fragment);

  // Prune old DOM elements
  while (DOM.terminal.childNodes.length > MAX_LOG_LINES) {
    DOM.terminal.removeChild(DOM.terminal.firstChild);
  }

  if (autoScrollEnabled) {
    DOM.terminal.scrollTop = DOM.terminal.scrollHeight;
  }

  if (logBuffer.length > 0) {
    requestAnimationFrame(flushLogs);
  } else {
    isLoggingScheduled = false;
  }
}

function appendLog(message) {
  logBuffer.push(message);
  if (!isLoggingScheduled) {
    isLoggingScheduled = true;
    requestAnimationFrame(flushLogs);
  }
}

// ─── Chart.js Real-Time Visualizations ─────────────────────────────
let speedChart = null;
let resultsChart = null;

function initCharts() {
  const ctxSpeed = document.getElementById('speedChart')?.getContext('2d');
  const ctxResults = document.getElementById('resultsChart')?.getContext('2d');

  if (ctxSpeed) {
    speedChart = new Chart(ctxSpeed, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label: 'Speed (att/s)',
          data: [],
          borderColor: '#06b6d4',
          backgroundColor: 'rgba(6, 182, 212, 0.1)',
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.25,
          fill: true,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false, // Zero animation overhead for 128MB GPU
        plugins: {
          legend: { display: false },
          tooltip: { enabled: true },
        },
        scales: {
          x: {
            display: false,
            grid: { display: false },
          },
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#64748b', font: { size: 10 } },
          },
        },
      },
    });
  }

  if (ctxResults) {
    resultsChart = new Chart(ctxResults, {
      type: 'doughnut',
      data: {
        labels: ['Hits', 'Failures', 'Errors'],
        datasets: [{
          data: [0, 0, 0],
          backgroundColor: ['#10b981', '#3b82f6', '#f43f5e'],
          borderWidth: 0,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 300 },
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#94a3b8', font: { size: 10 }, boxWidth: 10 },
          },
        },
        cutout: '72%',
      },
    });
  }
}

function updateCharts(metrics) {
  if (speedChart && metrics.speed !== undefined) {
    const isRunning = DOM.btnStop && !DOM.btnStop.disabled;
    const speedVal = parseFloat(metrics.speed) || 0;
    if (isRunning || speedVal > 0) {
      const now = new Date().toLocaleTimeString();
      speedChart.data.labels.push(now);
      speedChart.data.datasets[0].data.push(speedVal);

      if (speedChart.data.labels.length > 30) {
        speedChart.data.labels.shift();
        speedChart.data.datasets[0].data.shift();
      }
      speedChart.update('none');
    }
  }

  if (resultsChart && (metrics.hits !== undefined || metrics.attempted !== undefined)) {
    const hits = metrics.hits || 0;
    const errors = metrics.errors || 0;
    const failures = Math.max(0, (metrics.attempted || 0) - hits - errors);

    resultsChart.data.datasets[0].data = [hits, failures, errors];
    resultsChart.update();
  }
}

// ─── Stats & Progress Updates ──────────────────────────────────────
let attackStartTime = null;
let elapsedTicker = null;

function startElapsedTicker() {
  stopElapsedTicker();
  attackStartTime = Date.now();
  elapsedTicker = setInterval(() => {
    if (attackStartTime && DOM.statElapsed) {
      const elapsedSec = (Date.now() - attackStartTime) / 1000;
      DOM.statElapsed.textContent = formatTime(elapsedSec);
    }
  }, 1000);
}

function stopElapsedTicker() {
  if (elapsedTicker) {
    clearInterval(elapsedTicker);
    elapsedTicker = null;
  }
}

function updateStats(metrics) {
  if (!metrics) return;
  if (metrics.elapsed != null && DOM.statElapsed) {
    DOM.statElapsed.textContent = formatTime(metrics.elapsed);
  }
  if (DOM.statSpeed) {
    const sp = parseFloat(metrics.speed) || 0;
    DOM.statSpeed.textContent = `${sp.toFixed(1)} att/s`;
  }
  if (DOM.statEta) {
    if (metrics.eta == null || metrics.eta <= 0 || !isFinite(metrics.eta)) {
      DOM.statEta.textContent = '--:--:--';
    } else {
      DOM.statEta.textContent = formatTime(metrics.eta);
    }
  }

  const hits = metrics.hits != null ? metrics.hits : (metrics.successes != null ? metrics.successes : 0);
  if (DOM.statHits) DOM.statHits.textContent = String(hits);

  if (metrics.attempted != null && DOM.statAttempted) {
    DOM.statAttempted.textContent = String(metrics.attempted);
  }

  const errors = metrics.errors != null ? metrics.errors : (metrics.rate_limits != null ? metrics.rate_limits : 0);
  if (DOM.statErrors) DOM.statErrors.textContent = String(errors);

  if (metrics.progress !== undefined) {
    setProgress(metrics.progress);
  }

  updateCharts(metrics);
}

function resetStats() {
  if (DOM.statElapsed) DOM.statElapsed.textContent = '00:00:00';
  if (DOM.statSpeed) DOM.statSpeed.textContent = '0.0 att/s';
  if (DOM.statEta) DOM.statEta.textContent = '--:--:--';
  if (DOM.statHits) DOM.statHits.textContent = '0';
  if (DOM.statAttempted) DOM.statAttempted.textContent = '0';
  if (DOM.statErrors) DOM.statErrors.textContent = '0';

  if (speedChart) {
    speedChart.data.labels = [];
    speedChart.data.datasets[0].data = [];
    speedChart.update('none');
  }
  if (resultsChart) {
    resultsChart.data.datasets[0].data = [0, 0, 0];
    resultsChart.update();
  }
}

function setProgress(percent) {
  if (!DOM.progressFill || !DOM.progressText) return;
  const clamped = Math.max(0, Math.min(100, parseFloat(percent) || 0));
  DOM.progressFill.style.width = `${clamped}%`;
  DOM.progressText.textContent = `${Math.round(clamped)}%`;
}

async function postJSON(url, data) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  try {
    const json = await response.json();
    if (!response.ok && !json.status) json.status = 'error';
    return json;
  } catch (e) {
    return { status: 'error', message: `Server error (HTTP ${response.status})` };
  }
}

// ─── API Operations ────────────────────────────────────────────────
async function startAttack() {
  const config = {
    target_url: DOM.targetUrl?.value.trim() || '',
    username: DOM.username?.value.trim() || '',
    password: DOM.password?.value.trim() || '',
    error_msg: DOM.errorString?.value.trim() || '',
    success_msg: DOM.successString?.value.trim() || '',

    mode: DOM.attackMode?.value || 'browser',
    threads: parseInt(DOM.threads?.value || '1', 10) || 1,
    delay: parseFloat(DOM.delay?.value || '0') || 0,
    jitter: parseFloat(DOM.jitter?.value || '0') || 0,
    limit_text: DOM.rateLimit?.value.trim() || '',
    cooldown: parseInt(DOM.cooldown?.value || '12', 10) || 12,
    max_attempts: parseInt(DOM.maxAttempts?.value || '0', 10) || 0,
    headless: DOM.headless ? DOM.headless.checked : true,
    continue_after_success: DOM.continueAfterSuccess ? DOM.continueAfterSuccess.checked : false,

    use_tor: DOM.enableTor ? DOM.enableTor.checked : false,
    tor_port: parseInt(DOM.torControlPort?.value || '9051', 10) || 9051,
    tor_shift_every: parseInt(DOM.torShiftEvery?.value || '10', 10) || 10,
    proxy: DOM.proxy?.value.trim() || '',
    spray_mode: DOM.sprayMode ? DOM.sprayMode.checked : false,

    discord_url: DOM.discordWebhook ? DOM.discordWebhook.value.trim() : '',
    telegram_token: DOM.telegramToken ? DOM.telegramToken.value.trim() : '',
    telegram_chat_id: DOM.telegramChatId ? DOM.telegramChatId.value.trim() : '',
  };

  if (config.mode === 'http') {
    config.form_action = DOM.formAction?.value.trim() || '';
    config.username_field = DOM.usernameField?.value.trim() || '';
    config.password_field = DOM.passwordField?.value.trim() || '';
    config.csrf_field = DOM.csrfField?.value.trim() || '';
    config.follow_redirects = DOM.followRedirects ? DOM.followRedirects.checked : false;
    config.json_mode = DOM.jsonMode ? DOM.jsonMode.checked : false;
    config.custom_headers = DOM.customHeaders?.value.trim() || '';
    config.cookies = DOM.customCookies?.value.trim() || '';
    config.success_status_codes = DOM.successStatusCodes?.value.trim() || '';
  }

  if (!config.target_url) {
    appendLog('[-] Target URL is required.');
    DOM.targetUrl?.focus();
    showToast('Target URL is required', 'error');
    return;
  }
  if (!config.username) {
    appendLog('[-] Username / userlist is required.');
    DOM.username?.focus();
    showToast('Username is required', 'error');
    return;
  }
  if (!config.password) {
    appendLog('[-] Password / wordlist is required.');
    DOM.password?.focus();
    showToast('Password is required', 'error');
    return;
  }

  DOM.btnStart.disabled = true;
  DOM.btnStop.disabled = false;

  DOM.terminal.innerHTML = '';
  resetStats();
  setProgress(0);
  startElapsedTicker();

  appendLog('[*] Initializing attack routine…');
  showToast('Starting attack…', 'info');

  try {
    const result = await postJSON('/api/attack/start', config);
    if (result.status === 'error' || result.error) {
      const errMsg = result.message || result.error || 'Unknown error';
      appendLog(`[-] ${errMsg}`);
      DOM.btnStart.disabled = false;
      DOM.btnStop.disabled = true;
      stopElapsedTicker();
      showToast(errMsg, 'error');
    } else {
      appendLog(`[+] ${result.message || 'Attack launched successfully.'}`);
    }
  } catch (err) {
    appendLog(`[-] Connection error: ${err.message}`);
    DOM.btnStart.disabled = false;
    DOM.btnStop.disabled = true;
    stopElapsedTicker();
    showToast(`Network error: ${err.message}`, 'error');
  }
}

async function stopAttack() {
  DOM.btnStop.disabled = true;
  stopElapsedTicker();
  appendLog('[!] Terminating active attack…');
  showToast('Stopping attack…', 'info');

  try {
    const result = await postJSON('/api/attack/stop', {});
    appendLog(`[*] ${result.message || 'Stop signal acknowledged.'}`);
  } catch (err) {
    appendLog(`[-] Error stopping attack: ${err.message}`);
  }

  DOM.btnStart.disabled = false;
  syncAttackStatus();
}

// ─── Target Fingerprint Scanner ────────────────────────────────────
async function scanTargetTechnology() {
  const url = DOM.targetUrl?.value.trim();
  if (!url) {
    showToast('Please enter a target URL to scan', 'error');
    DOM.targetUrl?.focus();
    return;
  }

  DOM.btnScanTarget.disabled = true;
  DOM.btnScanTarget.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Scanning…';
  appendLog(`[*] Fingerprinting technology stack for: ${url}`);

  try {
    const res = await postJSON('/api/target/fingerprint', { target_url: url });
    if (res.status === 'error' || res.error) {
      const errMsg = res.message || res.error || 'Fingerprint failed';
      appendLog(`[-] Fingerprint failed: ${errMsg}`);
      showToast(errMsg, 'error');
    } else {
      renderTechBadges(res);
      showToast('Technology stack identified', 'success');
    }
  } catch (err) {
    appendLog(`[-] Fingerprint scan error: ${err.message}`);
  } finally {
    DOM.btnScanTarget.disabled = false;
    DOM.btnScanTarget.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Scan Tech';
  }
}

function renderTechBadges(data) {
  if (!DOM.targetTechBadge) return;
  DOM.targetTechBadge.innerHTML = '';

  const fp = (data && data.fingerprint) ? data.fingerprint : (data || {});
  const frameworks = fp.frameworks || [];
  const servers = fp.servers || [];
  const protections = fp.protections || [];

  if (frameworks.length === 0 && servers.length === 0 && protections.length === 0) {
    DOM.targetTechBadge.style.display = 'none';
  } else {
    DOM.targetTechBadge.style.display = 'flex';
  }

  frameworks.forEach(f => {
    const tag = document.createElement('span');
    tag.className = 'tech-tag framework';
    tag.innerHTML = `<i class="fa-solid fa-code"></i> ${escapeHTML(f)}`;
    DOM.targetTechBadge.appendChild(tag);
  });

  servers.forEach(s => {
    const tag = document.createElement('span');
    tag.className = 'tech-tag server';
    tag.innerHTML = `<i class="fa-solid fa-server"></i> ${escapeHTML(s)}`;
    DOM.targetTechBadge.appendChild(tag);
  });

  protections.forEach(p => {
    const tag = document.createElement('span');
    tag.className = 'tech-tag protection';
    tag.innerHTML = `<i class="fa-solid fa-shield"></i> ${escapeHTML(p)}`;
    DOM.targetTechBadge.appendChild(tag);
  });

  if (fp.form && fp.form.has_login_form) {
    if (fp.form.action && DOM.formAction && !DOM.formAction.value) {
      DOM.formAction.value = fp.form.action;
    }
    if (fp.form.username_field && DOM.usernameField && !DOM.usernameField.value) {
      DOM.usernameField.value = fp.form.username_field;
    }
    if (fp.form.password_field && DOM.passwordField && !DOM.passwordField.value) {
      DOM.passwordField.value = fp.form.password_field;
    }
    if (fp.form.csrf_field && DOM.csrfField && !DOM.csrfField.value) {
      DOM.csrfField.value = fp.form.csrf_field;
    }
    appendLog(`[+] Auto-filled form parameters for action: ${fp.form.action}`);
  }
}

// ─── Generators: CUPP & Sequence ───────────────────────────────────
async function generateCupp() {
  const profile = {
    first_name: DOM.cuppFirstName?.value.trim() || '',
    last_name: DOM.cuppLastName?.value.trim() || '',
    nickname: DOM.cuppNickname?.value.trim() || '',
    birthdate: DOM.cuppBirthdate?.value.trim() || '',
    partner_name: DOM.cuppPartnerName?.value.trim() || '',
    partner_nickname: DOM.cuppPartnerNickname?.value.trim() || '',
    partner_birthdate: DOM.cuppPartnerBirthdate?.value.trim() || '',
    child_name: DOM.cuppChildName?.value.trim() || '',
    child_birthdate: DOM.cuppChildBirthdate?.value.trim() || '',
    pet_name: DOM.cuppPetName?.value.trim() || '',
    company: DOM.cuppCompany?.value.trim() || '',
    keywords: DOM.cuppKeywords?.value.trim() || '',
    special_chars: DOM.cuppSpecialChars ? DOM.cuppSpecialChars.checked : false,
    random_numbers: DOM.cuppRandomNumbers ? DOM.cuppRandomNumbers.checked : false,
    leet: DOM.cuppLeet ? DOM.cuppLeet.checked : false,
  };

  DOM.btnGenerateCupp.disabled = true;
  DOM.btnUseCupp.disabled = true;
  DOM.cuppStatus.textContent = 'Generating…';
  appendLog('[*] Compiling CUPP profile wordlist…');

  try {
    const result = await postJSON('/api/cupp/generate', profile);
    if (result.status === 'error' || result.error) {
      const errMsg = result.message || result.error || 'CUPP error';
      appendLog(`[-] CUPP error: ${errMsg}`);
      DOM.cuppStatus.textContent = 'Failed';
      showToast(errMsg, 'error');
      DOM.btnGenerateCupp.disabled = false;
    } else {
      appendLog(`[*] CUPP generation started, waiting for completion…`);
      DOM.cuppStatus.textContent = 'Generating…';
    }
  } catch (err) {
    appendLog(`[-] CUPP request failed: ${err.message}`);
    DOM.cuppStatus.textContent = 'Error';
    DOM.btnGenerateCupp.disabled = false;
  }
}

function useCuppResult() {
  if (cuppResultPath && DOM.password) {
    DOM.password.value = cuppResultPath;
    saveFormState();
    switchTab('target');
    showToast('Loaded CUPP wordlist into Password input', 'success');
  }
}

async function generateSequence() {
  const payload = {
    start: parseInt(DOM.seqStart?.value || '0', 10),
    end: parseInt(DOM.seqEnd?.value || '9999', 10),
    pad_width: parseInt(DOM.seqPadding?.value || '4', 10),
    prefix: DOM.seqPrefix?.value || '',
    suffix: DOM.seqSuffix?.value || '',
  };

  DOM.btnGenerateSeq.disabled = true;
  DOM.btnUseSeq.disabled = true;
  DOM.seqStatus.textContent = 'Generating…';
  appendLog('[*] Generating numeric sequence wordlist…');

  try {
    const result = await postJSON('/api/sequence/generate', payload);
    if (result.status === 'error' || result.error) {
      const errMsg = result.message || result.error || 'Sequence error';
      appendLog(`[-] Sequence error: ${errMsg}`);
      DOM.seqStatus.textContent = 'Failed';
      showToast(errMsg, 'error');
      DOM.btnGenerateSeq.disabled = false;
    } else {
      appendLog(`[*] Sequence generation started, waiting for completion…`);
      DOM.seqStatus.textContent = 'Generating…';
    }
  } catch (err) {
    appendLog(`[-] Sequence failed: ${err.message}`);
    DOM.seqStatus.textContent = 'Error';
    DOM.btnGenerateSeq.disabled = false;
  }
}

function useSequenceResult() {
  if (sequenceResultPath && DOM.password) {
    DOM.password.value = sequenceResultPath;
    saveFormState();
    switchTab('target');
    showToast('Loaded sequence wordlist into Target input', 'success');
  }
}

// ─── Environment Diagnostics (Doctor) ──────────────────────────────
async function runDoctorDiagnostics() {
  if (!DOM.doctorChecksContainer) return;
  DOM.doctorChecksContainer.innerHTML = `
    <div class="loading-state">
      <i class="fa-solid fa-spinner fa-spin"></i> Running diagnostic health checks…
    </div>
  `;

  try {
    const res = await fetch('/api/doctor');
    const data = await res.json();
    DOM.doctorChecksContainer.innerHTML = '';

    const checks = data.checks || (data.report && data.report.checks) || [];
    if (checks.length === 0) {
      DOM.doctorChecksContainer.innerHTML = '<div class="empty-state"><p>No diagnostics data returned.</p></div>';
      return;
    }

    checks.forEach(chk => {
      const item = document.createElement('div');
      item.className = 'doctor-item';
      const isPass = chk.status === 'ok' || chk.passed === true;
      const isWarn = chk.status === 'warn';
      const badgeClass = isPass ? 'pass' : (isWarn ? 'warn' : 'fail');
      const badgeText = isPass ? 'PASS' : (isWarn ? 'WARN' : 'FAIL');

      item.innerHTML = `
        <div>
          <div class="doctor-item-name">${escapeHTML(chk.name)}</div>
          <div class="doctor-item-desc">${escapeHTML(chk.detail || '')}</div>
        </div>
        <span class="doctor-badge ${badgeClass}">
          ${badgeText}
        </span>
      `;
      DOM.doctorChecksContainer.appendChild(item);
    });
  } catch (err) {
    DOM.doctorChecksContainer.innerHTML = `<div class="log-error">Doctor check failed: ${escapeHTML(err.message)}</div>`;
  }
}

// ─── Demo Sandbox ──────────────────────────────────────────────────
async function launchDemoMode() {
  appendLog('[*] Initializing local Demo Sandbox…');
  showToast('Spinning up Demo Sandbox…', 'info');

  try {
    const res = await postJSON('/api/demo/start', { port: 5001 });
    if (res.status === 'ok' || res.status === 'running') {
      const demoUrl = `http://127.0.0.1:${res.port || 5001}/login`;
      if (DOM.targetUrl) DOM.targetUrl.value = demoUrl;
      if (DOM.username) DOM.username.value = 'demo';
      if (DOM.password) DOM.password.value = 'pass.txt';
      if (DOM.errorString) DOM.errorString.value = 'Invalid';
      if (DOM.successString) DOM.successString.value = 'Successful';

      saveFormState();
      switchTab('target');
      appendLog(`[+] Demo sandbox ready at: ${demoUrl} (Target configured)`);
      showToast('Demo Sandbox active and loaded into Target Config!', 'success');
    } else {
      appendLog(`[-] Demo launch issue: ${res.message || 'Unknown'}`);
    }
  } catch (err) {
    appendLog(`[-] Demo error: ${err.message}`);
  }
}

// ─── Notifications Configuration ───────────────────────────────────
async function saveNotifications() {
  const payload = {
    discord_url: DOM.discordWebhook?.value.trim() || '',
    telegram_token: DOM.telegramToken?.value.trim() || '',
    telegram_chat_id: DOM.telegramChatId?.value.trim() || '',
  };

  DOM.btnSaveNotifications.disabled = true;
  DOM.notifStatus.textContent = 'Saving…';

  try {
    const res = await postJSON('/api/notifications/configure', payload);
    DOM.notifStatus.textContent = res.message || 'Saved';
    showToast('Notification settings saved', 'success');
    saveFormState();
  } catch (err) {
    DOM.notifStatus.textContent = 'Save failed';
    showToast(err.message, 'error');
  } finally {
    DOM.btnSaveNotifications.disabled = false;
  }
}

async function testDiscord() {
  const url = DOM.discordWebhook?.value.trim();
  if (!url) {
    showToast('Please enter a Discord Webhook URL', 'error');
    return;
  }

  DOM.btnTestDiscord.disabled = true;
  appendLog('[*] Testing Discord webhook alert…');

  try {
    const res = await postJSON('/api/notifications/test', { discord_url: url });
    if (res.results?.discord) {
      appendLog('[+] Discord test webhook sent successfully!');
      showToast('Discord test notification dispatched!', 'success');
    } else {
      appendLog(`[-] Discord test failed: ${res.results?.discord_error || 'Check URL'}`);
      showToast('Discord test failed', 'error');
    }
  } catch (err) {
    appendLog(`[-] Discord test error: ${err.message}`);
  } finally {
    DOM.btnTestDiscord.disabled = false;
  }
}

async function testTelegram() {
  const token = DOM.telegramToken?.value.trim();
  const chatId = DOM.telegramChatId?.value.trim();
  if (!token || !chatId) {
    showToast('Please enter both Bot Token and Chat ID', 'error');
    return;
  }

  DOM.btnTestTelegram.disabled = true;
  appendLog('[*] Testing Telegram bot notification…');

  try {
    const res = await postJSON('/api/notifications/test', { telegram_token: token, telegram_chat_id: chatId });
    if (res.results?.telegram) {
      appendLog('[+] Telegram test message sent successfully!');
      showToast('Telegram test notification dispatched!', 'success');
    } else {
      appendLog(`[-] Telegram test failed: ${res.results?.telegram_error || 'Check Token/Chat ID'}`);
      showToast('Telegram test failed', 'error');
    }
  } catch (err) {
    appendLog(`[-] Telegram test error: ${err.message}`);
  } finally {
    DOM.btnTestTelegram.disabled = false;
  }
}

// ─── Targets Queue & Scheduler ─────────────────────────────────────
async function addCurrentTargetToQueue() {
  const config = getFormState();
  if (!config.target_url) {
    showToast('Configure a Target URL first', 'error');
    return;
  }

  try {
    const res = await postJSON('/api/targets/add', { config, name: config.target_url });
    if (res.status === 'ok') {
      showToast('Target added to queue', 'success');
      loadTargetsQueue();
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadTargetsQueue() {
  if (!DOM.targetList) return;
  try {
    const res = await fetch('/api/targets');
    const data = await res.json();
    const targets = data.targets || [];

    if (targets.length === 0) {
      DOM.targetList.innerHTML = `
        <div class="empty-state">
          <i class="fa-solid fa-folder-open empty-state-icon"></i>
          <p>No targets queued yet. Configure a target and click "Queue Current Configuration".</p>
        </div>
      `;
      if (DOM.btnStartAllTargets) DOM.btnStartAllTargets.disabled = true;
    } else {
      DOM.targetList.innerHTML = '';
      targets.forEach((t, idx) => {
        const item = document.createElement('div');
        item.className = 'queue-target-item';
        item.innerHTML = `
          <div class="queue-target-url">${idx + 1}. ${escapeHTML(t.config?.target_url || t.name)}</div>
          <button class="btn btn-ghost btn-sm" onclick="removeQueueTarget(${idx})">
            <i class="fa-solid fa-trash text-rose"></i>
          </button>
        `;
        DOM.targetList.appendChild(item);
      });
      if (DOM.btnStartAllTargets) DOM.btnStartAllTargets.disabled = false;
    }
  } catch (e) {}
}

window.removeQueueTarget = async function(idx) {
  try {
    await postJSON('/api/targets/remove', { index: idx });
    loadTargetsQueue();
  } catch (e) {}
};

async function scheduleAttack() {
  const time = DOM.scheduleTime?.value;
  if (!time) {
    showToast('Please select a scheduled date and time', 'error');
    return;
  }

  const config = getFormState();
  try {
    const res = await postJSON('/api/schedule/create', { run_at: time, config });
    if (res.status === 'ok') {
      showToast('Attack scheduled successfully', 'success');
      loadScheduleList();
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadScheduleList() {
  if (!DOM.scheduleList) return;
  try {
    const res = await fetch('/api/schedule');
    const data = await res.json();
    const tasks = data.tasks || [];

    if (tasks.length === 0) {
      DOM.scheduleList.innerHTML = `
        <div class="empty-state">
          <i class="fa-solid fa-calendar-xmark empty-state-icon"></i>
          <p>No scheduled tasks currently active.</p>
        </div>
      `;
    } else {
      DOM.scheduleList.innerHTML = '';
      tasks.forEach((task, idx) => {
        const item = document.createElement('div');
        item.className = 'queue-target-item';

        const parsedDate = new Date(task.run_at);
        const dateDisplay = isNaN(parsedDate.getTime()) ? escapeHTML(String(task.run_at || '')) : parsedDate.toLocaleString();

        const infoDiv = document.createElement('div');
        infoDiv.innerHTML = `
          <div class="queue-target-url">${escapeHTML(task.target_url || 'Target')}</div>
          <div style="font-size: 0.72rem; color: var(--text-muted);">Runs: ${dateDisplay}</div>
        `;

        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'btn btn-ghost btn-sm';
        cancelBtn.innerHTML = '<i class="fa-solid fa-xmark text-rose"></i> Cancel';
        cancelBtn.addEventListener('click', () => {
          window.cancelScheduledTask(task.id || String(idx));
        });

        item.appendChild(infoDiv);
        item.appendChild(cancelBtn);
        DOM.scheduleList.appendChild(item);
      });
    }
  } catch (e) {}
}

window.cancelScheduledTask = async function(taskId) {
  try {
    await postJSON('/api/schedule/cancel', { task_id: taskId });
    loadScheduleList();
    showToast('Scheduled task cancelled', 'info');
  } catch (e) {}
};

// ─── Socket.IO Real-Time Sync & Dynamic Reconnection ──────────────
socket.on('connect', () => {
  if (DOM.connectionDot) DOM.connectionDot.className = 'status-dot connected';
  if (DOM.connectionLabel) DOM.connectionLabel.textContent = 'Live';
  syncAttackStatus();
});

socket.on('disconnect', () => {
  if (DOM.connectionDot) DOM.connectionDot.className = 'status-dot disconnected';
  if (DOM.connectionLabel) DOM.connectionLabel.textContent = 'Disconnected';
});

socket.on('connect_error', () => {
  if (DOM.connectionDot) DOM.connectionDot.className = 'status-dot disconnected';
  if (DOM.connectionLabel) DOM.connectionLabel.textContent = 'Offline';
});

// Metrics updates directly from engine
socket.on('metrics', data => {
  if (data) updateStats(data);
});

// Progress updates directly from engine
socket.on('progress', data => {
  if (!data) return;
  if (data.percent !== undefined) {
    setProgress(data.percent);
  } else if (data.total > 0) {
    setProgress((data.current / data.total) * 100);
  } else if (data.progress !== undefined) {
    setProgress(data.progress);
  }
});

// General status updates
socket.on('status', data => {
  if (!data) return;
  if (data.metrics) updateStats(data.metrics);
  if (data.progress !== undefined) setProgress(data.progress);
  if (data.running !== undefined) {
    if (DOM.btnStart) DOM.btnStart.disabled = data.running;
    if (DOM.btnStop) DOM.btnStop.disabled = !data.running;
    if (data.running) {
      if (!elapsedTicker) startElapsedTicker();
    } else {
      stopElapsedTicker();
    }
  }
});

socket.on('log', data => {
  if (data && data.message) appendLog(data.message);
});

socket.on('credential_found', data => {
  if (!data) return;
  appendLog(`[+] 🔥 FOUND CREDENTIALS → User: ${data.username} | Pass: ${data.password}`);
  showToast(`Found Credentials: ${data.username} / ${data.password}`, 'success');
  const currentHits = parseInt(DOM.statHits?.textContent || '0', 10) || 0;
  if (DOM.statHits) DOM.statHits.textContent = String(currentHits + 1);
});

// 'found' is a legacy alias for 'credential_found' — handled above to avoid double counting

socket.on('finished', data => {
  if (DOM.btnStart) DOM.btnStart.disabled = false;
  if (DOM.btnStop) DOM.btnStop.disabled = true;
  stopElapsedTicker();
  appendLog(`[*] Attack finished: ${data?.message || 'Complete'}`);
  showToast('Attack cycle completed', 'info');
  syncAttackStatus();
});

socket.on('tor_identity', data => {
  if (data) appendLog(`[*] Tor identity shifted. New egress IP: ${data.ip || 'Rotated'}`);
});

socket.on('cupp_done', data => {
  if (data && data.success && data.path) {
    cuppResultPath = data.path;
    const countText = data.count ? ` (${data.count} passwords)` : '';
    if (DOM.cuppStatus) DOM.cuppStatus.textContent = `Ready${countText}`;
    if (DOM.btnUseCupp) DOM.btnUseCupp.disabled = false;
    showToast(`CUPP wordlist ready${countText}`, 'success');
  }
});

socket.on('sequence_done', data => {
  if (data && data.success && data.path) {
    sequenceResultPath = data.path;
    const countText = data.count ? ` (${data.count} passwords)` : '';
    if (DOM.seqStatus) DOM.seqStatus.textContent = `Ready${countText}`;
    if (DOM.btnUseSeq) DOM.btnUseSeq.disabled = false;
    showToast(`Sequence wordlist ready${countText}`, 'success');
  }
});

socket.on('targets_queue_finished', data => {
  showToast(data?.message || 'Multi-target queue finished', 'success');
  loadTargetsQueue();
});

async function syncAttackStatus() {
  try {
    const res = await fetch('/api/attack/status');
    const data = await res.json();

    if (data.running) {
      if (DOM.btnStart) DOM.btnStart.disabled = true;
      if (DOM.btnStop) DOM.btnStop.disabled = false;
      if (!elapsedTicker) startElapsedTicker();
      if (data.metrics) updateStats(data.metrics);
      if (data.progress !== undefined) setProgress(data.progress);
    } else {
      if (DOM.btnStart) DOM.btnStart.disabled = false;
      if (DOM.btnStop) DOM.btnStop.disabled = true;
      stopElapsedTicker();
      if (data.metrics && data.metrics.attempted > 0) {
        updateStats({
          ...data.metrics,
          speed: 0,
          eta: 0,
        });
      } else {
        resetStats();
      }
      if (data.progress !== undefined) setProgress(data.progress);
    }

    if (data.logs && Array.isArray(data.logs) && DOM.terminal && DOM.terminal.childNodes.length <= 1) {
      data.logs.forEach(msg => appendLog(msg));
    }
  } catch (e) {}
}

async function resumeAttack() {
  if (DOM.resumeBanner) DOM.resumeBanner.classList.remove('visible');
  appendLog('[*] Resuming attack from saved checkpoint session…');
  showToast('Resuming attack session…', 'info');
  try {
    const res = await postJSON('/api/attack/resume', {});
    if (res.status === 'ok') {
      if (DOM.btnStart) DOM.btnStart.disabled = true;
      if (DOM.btnStop) DOM.btnStop.disabled = false;
      startElapsedTicker();
      showToast(res.message || 'Attack resumed successfully', 'success');
    } else {
      appendLog(`[-] Resume failed: ${res.message}`);
      showToast(res.message || 'Resume failed', 'error');
    }
  } catch (err) {
    appendLog(`[-] Resume error: ${err.message}`);
    showToast(`Resume error: ${err.message}`, 'error');
  }
}

async function startAllTargets() {
  if (DOM.btnStartAllTargets) DOM.btnStartAllTargets.disabled = true;
  appendLog('[*] Initiating sequential attack for all queued targets…');
  showToast('Starting multi-target attack queue…', 'info');
  try {
    const res = await postJSON('/api/targets/start', {});
    if (res.status === 'ok') {
      showToast(res.message || 'Targets queue started', 'success');
      loadTargetsQueue();
    } else {
      showToast(res.message || 'Could not start targets', 'error');
      if (DOM.btnStartAllTargets) DOM.btnStartAllTargets.disabled = false;
    }
  } catch (err) {
    showToast(`Queue error: ${err.message}`, 'error');
    if (DOM.btnStartAllTargets) DOM.btnStartAllTargets.disabled = false;
  }
}

async function clearTargetsQueue() {
  try {
    const res = await postJSON('/api/targets/clear', {});
    if (res.status === 'ok') {
      showToast('Targets queue cleared', 'info');
      loadTargetsQueue();
    }
  } catch (e) {}
}

// ─── Event Listeners Initialization ────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  // Initialize lightweight charts
  initCharts();

  // Restore active tab
  const savedTab = localStorage.getItem('bluecrack_active_tab') || 'target';
  switchTab(savedTab);

  // Tab buttons click
  DOM.tabButtons.forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  // Mode change
  if (DOM.attackMode) {
    DOM.attackMode.addEventListener('change', onModeChange);
  }

  // Restore form state
  await restoreFormState();
  bindAutoSave();

  // Attack Control Bar
  DOM.btnStart?.addEventListener('click', startAttack);
  DOM.btnStop?.addEventListener('click', stopAttack);
  DOM.btnResetConfig?.addEventListener('click', resetFormState);

  // Scan tech
  DOM.btnScanTarget?.addEventListener('click', scanTargetTechnology);

  // CUPP & Sequence
  DOM.btnGenerateCupp?.addEventListener('click', generateCupp);
  DOM.btnUseCupp?.addEventListener('click', useCuppResult);
  DOM.btnGenerateSeq?.addEventListener('click', generateSequence);
  DOM.btnUseSeq?.addEventListener('click', useSequenceResult);

  // Targets Queue & Scheduler
  DOM.btnAddTarget?.addEventListener('click', addCurrentTargetToQueue);
  DOM.btnStartAllTargets?.addEventListener('click', startAllTargets);
  DOM.btnScheduleAttack?.addEventListener('click', scheduleAttack);

  // Session Resume Bar
  DOM.btnResume?.addEventListener('click', resumeAttack);
  DOM.btnDismissResume?.addEventListener('click', () => {
    DOM.resumeBanner?.classList.remove('visible');
  });

  // Notifications
  DOM.btnSaveNotifications?.addEventListener('click', saveNotifications);
  DOM.btnTestDiscord?.addEventListener('click', testDiscord);
  DOM.btnTestTelegram?.addEventListener('click', testTelegram);

  // Header quick pills
  DOM.btnDoctor?.addEventListener('click', () => {
    DOM.doctorModal?.classList.add('open');
    runDoctorDiagnostics();
  });
  DOM.btnLaunchDemo?.addEventListener('click', launchDemoMode);
  DOM.btnInfo?.addEventListener('click', () => {
    DOM.tutorialModal?.classList.add('open');
    DOM.panelDisclaimer?.classList.remove('active');
    DOM.panelTutorial?.classList.add('active');
  });

  // Modal Closers
  DOM.btnCloseDoctor?.addEventListener('click', () => DOM.doctorModal?.classList.remove('open'));
  DOM.btnCloseModal?.addEventListener('click', () => DOM.tutorialModal?.classList.remove('open'));
  DOM.btnAgreeDisclaimer?.addEventListener('click', () => {
    DOM.tutorialModal?.classList.remove('open');
    try { localStorage.setItem('bluecrack_disclaimer_agreed', 'true'); } catch (e) {}
  });

  // Doctor modal actions
  DOM.btnCloseDoctorBtn?.addEventListener('click', () => DOM.doctorModal?.classList.remove('open'));
  DOM.btnRerunDoctor?.addEventListener('click', runDoctorDiagnostics);

  // Tutorial / Disclaimer navigation
  DOM.btnShowTutorialFromStart?.addEventListener('click', () => {
    DOM.panelDisclaimer?.classList.remove('active');
    DOM.panelTutorial?.classList.add('active');
  });
  DOM.btnBackToDisclaimer?.addEventListener('click', () => {
    DOM.panelTutorial?.classList.remove('active');
    DOM.panelDisclaimer?.classList.add('active');
  });
  DOM.btnFinishTutorial?.addEventListener('click', () => {
    DOM.tutorialModal?.classList.remove('open');
    try { localStorage.setItem('bluecrack_disclaimer_agreed', 'true'); } catch (e) {}
  });

  // Tutorial sub-tab navigation
  DOM.tutTabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      DOM.tutTabButtons.forEach(b => b.classList.toggle('active', b === btn));
      DOM.tutContents.forEach(c => c.classList.toggle('active', c.id === btn.dataset.tut));
    });
  });


  // Terminal actions
  DOM.btnClear?.addEventListener('click', async () => {
    if (DOM.terminal) DOM.terminal.innerHTML = '';
    try {
      await postJSON('/api/logs/clear', {});
      await postJSON('/api/attack/reset', {});
    } catch (e) {}
    resetStats();
    setProgress(0);
    showToast('Terminal and stats cleared', 'info');
  });

  DOM.btnCopyTerminal?.addEventListener('click', () => {
    if (!DOM.terminal) return;
    const text = DOM.terminal.innerText;
    navigator.clipboard.writeText(text).then(() => {
      showToast('Logs copied to clipboard', 'success');
    }).catch(() => {
      showToast('Failed to copy logs', 'error');
    });
  });

  DOM.btnAutoScroll?.addEventListener('click', () => {
    autoScrollEnabled = !autoScrollEnabled;
    DOM.btnAutoScroll.classList.toggle('active', autoScrollEnabled);
    showToast(autoScrollEnabled ? 'Auto-scroll enabled' : 'Auto-scroll paused', 'info');
  });

  DOM.terminalFilter?.addEventListener('input', () => {
    const q = DOM.terminalFilter.value.toLowerCase().trim();
    const entries = DOM.terminal.querySelectorAll('.log-entry');
    entries.forEach(el => {
      el.style.display = (!q || el.textContent.toLowerCase().includes(q)) ? '' : 'none';
    });
  });

  DOM.btnExport?.addEventListener('click', () => {
    const text = DOM.terminal.innerText;
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bluecrack_logs_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Logs exported', 'success');
  });

  DOM.btnReport?.addEventListener('click', () => {
    window.open('/api/report/html', '_blank');
  });

  DOM.btnDownloadJson?.addEventListener('click', () => {
    window.location.href = '/api/report/json';
  });

  // Check initial disclaimer acceptance
  const disclaimerAgreed = localStorage.getItem('bluecrack_disclaimer_agreed') === 'true';
  if (!disclaimerAgreed && DOM.tutorialModal) {
    DOM.tutorialModal.classList.add('open');
    DOM.panelDisclaimer?.classList.add('active');
    DOM.panelTutorial?.classList.remove('active');
  }

  // Check session status on page load for resume banner
  try {
    const sessRes = await fetch('/api/session/status');
    const sessData = await sessRes.json();
    if (sessData && sessData.has_session && DOM.resumeBanner) {
      DOM.resumeBanner.classList.add('visible');
    }
  } catch (e) {}

  // Load targets & schedules
  loadTargetsQueue();
  loadScheduleList();
});
