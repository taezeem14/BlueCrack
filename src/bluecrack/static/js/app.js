/* ═══════════════════════════════════════════════════════════════
   BlueCrack — Frontend Application Logic
   ═══════════════════════════════════════════════════════════════ */

'use strict';

// ─── Socket.IO Connection ──────────────────────────────────────
const socket = io();

// ─── Utility: Safe HTML Escaping ───────────────────────────────
function escapeHTML(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ─── DOM References ────────────────────────────────────────────
const DOM = {
  // Header Actions
  btnLaunchDemo:   document.getElementById('btnLaunchDemo'),
  btnToggleEco:    document.getElementById('btnToggleEco'),
  btnDoctor:       document.getElementById('btnDoctor'),

  // Connection status
  connectionDot:   document.getElementById('connectionDot'),
  connectionLabel: document.getElementById('connectionLabel'),

  // Floating Info & Welcome Modal
  btnInfo:                   document.getElementById('btnInfo'),
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

  // Terminal
  terminal: document.getElementById('terminal'),

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

// Cached result paths for generators
let cuppResultPath    = null;
let sequenceResultPath = null;


// ═══════════════════════════════════════════════════════════════
//  TAB SWITCHING & CONFIG PERSISTENCE
// ═══════════════════════════════════════════════════════════════

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
  const mode = DOM.attackMode.value;
  const isHttp = mode === 'http';
  if (DOM.httpModeOptions) DOM.httpModeOptions.style.display = isHttp ? 'block' : 'none';
  if (DOM.headlessGroup) DOM.headlessGroup.style.display = isHttp ? 'none' : '';
  if (isHttp && parseInt(DOM.threads?.value || '1', 10) <= 1 && DOM.threads) {
    DOM.threads.value = '4';
  }
}

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
    if (raw) {
      state = JSON.parse(raw);
    }
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
      telegram_chat_id: state.telegram_chat_id || ''
    }).catch(() => {});
  }
}

async function resetFormState() {
  try {
    localStorage.removeItem('bluecrack_config');
    await postJSON('/api/config/reset', {});
  } catch (e) {}

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
  appendLog('[~] Form configuration reset to default settings.');
}

function bindAutoSave() {
  const inputs = document.querySelectorAll('input, select, textarea');
  inputs.forEach(el => {
    el.addEventListener('input', saveFormState);
    el.addEventListener('change', saveFormState);
  });
}


// ═══════════════════════════════════════════════════════════════
//  HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════

/**
 * Format seconds into HH:MM:SS display string.
 */
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

/**
 * Determine CSS class for a log line based on its prefix.
 */
function getLogClass(message) {
  if (message.startsWith('[+]')) return 'log-success';
  if (message.startsWith('[-]')) return 'log-error';
  if (message.startsWith('[!]')) return 'log-warning';
  if (message.startsWith('[*]')) return 'log-info';
  if (message.startsWith('[~]')) return 'log-system';
  return '';
}

// Log buffering to prevent lag on rapid emissions
let logQueue = [];
let isLoggingScheduled = false;
const MAX_LOG_LINES = 500;

function flushLogs() {
  if (logQueue.length === 0) {
    isLoggingScheduled = false;
    return;
  }

  const fragment = document.createDocumentFragment();
  const linesToRender = logQueue.splice(0, 100);

  linesToRender.forEach(message => {
    const line = document.createElement('div');
    line.className = `log-line ${getLogClass(message)}`;
    line.textContent = message;
    fragment.appendChild(line);
  });

  DOM.terminal.appendChild(fragment);

  // Keep DOM clean by pruning old lines
  while (DOM.terminal.childNodes.length > MAX_LOG_LINES) {
    DOM.terminal.removeChild(DOM.terminal.firstChild);
  }

  // Scroll to bottom once per batch
  DOM.terminal.scrollTop = DOM.terminal.scrollHeight;

  if (logQueue.length > 0) {
    requestAnimationFrame(flushLogs);
  } else {
    isLoggingScheduled = false;
  }
}

/**
 * Append a log line to the terminal and auto-scroll.
 */
function appendLog(message) {
  logQueue.push(message);
  if (!isLoggingScheduled) {
    isLoggingScheduled = true;
    requestAnimationFrame(flushLogs);
  }
}

/**
 * Update all stat card values with optional pulse animation.
 */
function updateStats(metrics) {
  const updates = {
    statElapsed:   metrics.elapsed   != null ? formatTime(metrics.elapsed)                 : null,
    statSpeed:     metrics.speed     != null ? `${parseFloat(metrics.speed).toFixed(1)} att/s` : null,
    statEta:       metrics.eta       != null ? formatTime(metrics.eta)                     : null,
    statHits:      metrics.hits      != null ? String(metrics.hits)                        : null,
    statAttempted: metrics.attempted != null ? String(metrics.attempted)                   : null,
    statErrors:    metrics.errors    != null ? String(metrics.errors)                      : null,
  };

  for (const [id, value] of Object.entries(updates)) {
    if (value === null) continue;
    const el = DOM[id];
    if (!el) continue;

    // Only update and pulse if value actually changed
    if (el.textContent !== value) {
      el.textContent = value;
      // Only pulse Hits and Errors to avoid excessive layout calculations
      if (id === 'statHits' || id === 'statErrors') {
        el.classList.remove('pulse');
        void el.offsetWidth; // Force reflow only for high priority highlights
        el.classList.add('pulse');
      }
    }
  }

  // Update Chart.js live charts
  updateCharts(metrics);
}

/**
 * Reset all stats to their default display values.
 */
function resetStats() {
  DOM.statElapsed.textContent   = '00:00:00';
  DOM.statSpeed.textContent     = '0.0 att/s';
  DOM.statEta.textContent       = '--:--:--';
  DOM.statHits.textContent      = '0';
  DOM.statAttempted.textContent = '0';
  DOM.statErrors.textContent    = '0';
}

/**
 * Set progress bar width and label.
 */
function setProgress(percent) {
  const clamped = Math.max(0, Math.min(100, percent));
  DOM.progressFill.style.width = `${clamped}%`;
  DOM.progressText.textContent = `${Math.round(clamped)}%`;
}

/**
 * Helper to POST JSON to an API endpoint.
 */
async function postJSON(url, data) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return response.json();
}


// ═══════════════════════════════════════════════════════════════
//  API FUNCTIONS
// ═══════════════════════════════════════════════════════════════

/**
 * Collect all form values and start the attack.
 */
async function startAttack() {
  const config = {
    // Target
    target_url:     DOM.targetUrl.value.trim(),
    username:       DOM.username.value.trim(),
    password:       DOM.password.value.trim(),
    error_msg:      DOM.errorString.value.trim(),
    success_msg:    DOM.successString.value.trim(),

    // Attack mode
    mode:           DOM.attackMode.value,

    // Engine
    threads:                parseInt(DOM.threads.value, 10)   || 1,
    delay:                  parseFloat(DOM.delay.value)       || 0,
    jitter:                 parseFloat(DOM.jitter.value)      || 0,
    limit_text:             DOM.rateLimit.value.trim(),
    cooldown:               parseInt(DOM.cooldown.value, 10)  || 12,
    max_attempts:           parseInt(DOM.maxAttempts.value, 10) || 0,
    headless:               DOM.headless.checked,
    continue_after_success: DOM.continueAfterSuccess.checked,

    // Tor & Proxy
    use_tor:          DOM.enableTor.checked,
    tor_port:         parseInt(DOM.torControlPort.value, 10) || 9051,
    tor_shift_every:  parseInt(DOM.torShiftEvery.value, 10)  || 10,
    proxy:            DOM.proxy.value.trim(),

    // Spray mode
    spray_mode:       DOM.sprayMode.checked,
  };

  // Add HTTP-mode-specific fields
  if (config.mode === 'http') {
    config.form_action          = DOM.formAction?.value.trim() || '';
    config.username_field       = DOM.usernameField?.value.trim() || '';
    config.password_field       = DOM.passwordField?.value.trim() || '';
    config.csrf_field           = DOM.csrfField?.value.trim() || '';
    config.follow_redirects     = DOM.followRedirects ? DOM.followRedirects.checked : false;
    config.json_mode            = DOM.jsonMode ? DOM.jsonMode.checked : false;
    config.custom_headers       = DOM.customHeaders?.value.trim() || '';
    config.cookies              = DOM.customCookies?.value.trim() || '';
    config.success_status_codes = DOM.successStatusCodes?.value.trim() || '';
  }

  // Validate minimum fields
  if (!config.target_url) {
    appendLog('[-] Target URL is required.');
    DOM.targetUrl.focus();
    return;
  }
  if (!config.username) {
    appendLog('[-] Username is required.');
    DOM.username.focus();
    return;
  }
  if (!config.password) {
    appendLog('[-] Password / wordlist is required.');
    DOM.password.focus();
    return;
  }

  // Update UI state
  DOM.btnStart.disabled = true;
  DOM.btnStop.disabled  = false;

  // Clear terminal and reset stats
  DOM.terminal.innerHTML = '';
  resetStats();
  setProgress(0);

  appendLog('[*] Initialising attack…');

  try {
    const result = await postJSON('/api/attack/start', config);
    if (result.error) {
      appendLog(`[-] ${result.error}`);
      DOM.btnStart.disabled = false;
      DOM.btnStop.disabled  = true;
    } else {
      appendLog(`[+] ${result.message || 'Attack started.'}`);
    }
  } catch (err) {
    appendLog(`[-] Connection error: ${err.message}`);
    DOM.btnStart.disabled = false;
    DOM.btnStop.disabled  = true;
  }
}

/**
 * Stop the current attack.
 */
async function stopAttack() {
  DOM.btnStop.disabled = true;
  appendLog('[!] Stopping attack…');

  try {
    const result = await postJSON('/api/attack/stop', {});
    appendLog(`[*] ${result.message || 'Stop signal sent.'}`);
  } catch (err) {
    appendLog(`[-] Error stopping attack: ${err.message}`);
  }

  DOM.btnStart.disabled = false;
}

/**
 * Generate a CUPP wordlist from profile fields.
 */
async function generateCupp() {
  const profile = {
    first_name:        DOM.cuppFirstName.value.trim(),
    last_name:         DOM.cuppLastName.value.trim(),
    nickname:          DOM.cuppNickname.value.trim(),
    birthdate:         DOM.cuppBirthdate.value.trim(),
    partner_name:      DOM.cuppPartnerName.value.trim(),
    partner_nickname:  DOM.cuppPartnerNickname.value.trim(),
    partner_birthdate: DOM.cuppPartnerBirthdate.value.trim(),
    child_name:        DOM.cuppChildName.value.trim(),
    child_birthdate:   DOM.cuppChildBirthdate.value.trim(),
    pet_name:          DOM.cuppPetName.value.trim(),
    company:           DOM.cuppCompany.value.trim(),
    keywords:          DOM.cuppKeywords.value.trim(),
    special_chars:     DOM.cuppSpecialChars.checked,
    random_numbers:    DOM.cuppRandomNumbers.checked,
    leet:              DOM.cuppLeet.checked,
  };

  DOM.btnGenerateCupp.disabled = true;
  DOM.btnUseCupp.disabled      = true;
  DOM.cuppStatus.textContent   = 'Generating…';
  appendLog('[*] Generating CUPP wordlist…');

  try {
    const result = await postJSON('/api/cupp/generate', profile);
    if (result.error) {
      appendLog(`[-] CUPP error: ${result.error}`);
      DOM.cuppStatus.textContent = 'Error';
    } else {
      cuppResultPath = result.path || '';
      const count = result.count || '?';
      appendLog(`[+] CUPP generated: ${count} passwords → ${cuppResultPath}`);
      DOM.cuppStatus.textContent = `${count} passwords generated`;
      DOM.btnUseCupp.disabled = false;
    }
  } catch (err) {
    appendLog(`[-] CUPP request failed: ${err.message}`);
    DOM.cuppStatus.textContent = 'Failed';
  }

  DOM.btnGenerateCupp.disabled = false;
}

/**
 * Load the CUPP result file path into the password field.
 */
function useCuppResult() {
  if (cuppResultPath) {
    DOM.password.value = cuppResultPath;
    saveFormState();
    appendLog(`[+] Password file set to CUPP result: ${cuppResultPath}`);
    // Switch to Target tab for visibility
    switchTab('target');
  }
}

/**
 * Generate a numeric sequence.
 */
async function generateSequence() {
  const params = {
    start:   parseInt(DOM.seqStart.value, 10)   || 0,
    end:     parseInt(DOM.seqEnd.value, 10)      || 9999,
    padding: parseInt(DOM.seqPadding.value, 10)  || 0,
    prefix:  DOM.seqPrefix.value,
    suffix:  DOM.seqSuffix.value,
  };

  DOM.btnGenerateSeq.disabled = true;
  DOM.btnUseSeq.disabled      = true;
  DOM.seqStatus.textContent   = 'Generating…';
  appendLog('[*] Generating numeric sequence…');

  try {
    const result = await postJSON('/api/sequence/generate', params);
    if (result.error) {
      appendLog(`[-] Sequence error: ${result.error}`);
      DOM.seqStatus.textContent = 'Error';
    } else {
      sequenceResultPath = result.path || '';
      const count = result.count || '?';
      appendLog(`[+] Sequence generated: ${count} entries → ${sequenceResultPath}`);
      DOM.seqStatus.textContent = `${count} entries generated`;
      DOM.btnUseSeq.disabled = false;
    }
  } catch (err) {
    appendLog(`[-] Sequence request failed: ${err.message}`);
    DOM.seqStatus.textContent = 'Failed';
  }

  DOM.btnGenerateSeq.disabled = false;
}

/**
 * Load the sequence result file path into the password field.
 */
function useSequenceResult() {
  if (sequenceResultPath) {
    DOM.password.value = sequenceResultPath;
    saveFormState();
    appendLog(`[+] Password file set to sequence result: ${sequenceResultPath}`);
    switchTab('target');
  }
}

/**
 * Start the demo login server and auto-fill the target credentials settings.
 */
async function launchDemoMode() {
  if (!DOM.btnLaunchDemo) return;
  DOM.btnLaunchDemo.disabled = true;
  DOM.btnLaunchDemo.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Starting...';
  appendLog('[*] Contacting server to launch demo environment...');

  try {
    const result = await postJSON('/api/demo/start', {});
    if (result.status === 'ok') {
      appendLog(`[+] Demo server is running on port ${result.port}!`);
      
      // Auto-fill form inputs
      DOM.targetUrl.value = result.url;
      DOM.username.value = result.default_username;
      DOM.password.value = result.default_password_file;
      DOM.errorString.value = result.default_error_msg;
      DOM.successString.value = result.default_success_msg;
      saveFormState();
      
      appendLog(`[~] Credentials and target configured: ${result.default_username} / ${result.default_password_file}`);
      switchTab('target');
    } else {
      appendLog(`[-] Demo launch error: ${result.message || 'Unknown error'}`);
    }
  } catch (err) {
    appendLog(`[-] Demo server request failed: ${err.message}`);
  } finally {
    DOM.btnLaunchDemo.disabled = false;
    DOM.btnLaunchDemo.innerHTML = '<i class="fa-solid fa-rocket"></i> Demo Mode';
  }
}

// ─── Starfield Canvas Background Animation Loop ─────────────────
let starfieldCanvas = null;
let starfieldCtx = null;
let stars = [];
const numStars = 50;
let animationId = null;
let isCosmicMode = false;

function initStarfield() {
  starfieldCanvas = document.getElementById('starfield');
  if (!starfieldCanvas) return;
  starfieldCtx = starfieldCanvas.getContext('2d');
  resizeStarfield();
  
  // Debounced resize to avoid GPU thrashing during window drag
  let resizeTimer = null;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(resizeStarfield, 150);
  });
  
  // Initialize stars
  stars = [];
  for (let i = 0; i < numStars; i++) {
    stars.push({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      z: Math.random() * window.innerWidth,
      color: Math.random() > 0.5 ? '#c084fc' : '#34d399'
    });
  }
  
  if (isCosmicMode) {
    startStarfieldAnimation();
  }
}

function resizeStarfield() {
  if (!starfieldCanvas) return;
  starfieldCanvas.width = window.innerWidth;
  starfieldCanvas.height = window.innerHeight;
}

function startStarfieldAnimation() {
  if (animationId) cancelAnimationFrame(animationId);
  
  function draw() {
    if (!isCosmicMode) return;
    
    starfieldCtx.clearRect(0, 0, starfieldCanvas.width, starfieldCanvas.height);
    
    // Draw and update stars
    for (let i = 0; i < stars.length; i++) {
      let star = stars[i];
      star.z -= 1.2;
      
      if (star.z <= 0) {
        star.z = window.innerWidth;
        star.x = Math.random() * window.innerWidth;
        star.y = Math.random() * window.innerHeight;
      }
      
      // 3D Projection
      let k = 128.0 / star.z;
      let px = (star.x - window.innerWidth / 2) * k + window.innerWidth / 2;
      let py = (star.y - window.innerHeight / 2) * k + window.innerHeight / 2;
      
      if (px >= 0 && px <= window.innerWidth && py >= 0 && py <= window.innerHeight) {
        let size = (1 - star.z / window.innerWidth) * 3;
        starfieldCtx.beginPath();
        starfieldCtx.fillStyle = star.color;
        starfieldCtx.globalAlpha = 1 - star.z / window.innerWidth;
        starfieldCtx.arc(px, py, size, 0, Math.PI * 2);
        starfieldCtx.fill();
      }
    }
    
    animationId = requestAnimationFrame(draw);
  }
  
  animationId = requestAnimationFrame(draw);
}

function stopStarfieldAnimation() {
  if (animationId) {
    cancelAnimationFrame(animationId);
    animationId = null;
  }
  if (starfieldCanvas && starfieldCtx) {
    starfieldCtx.clearRect(0, 0, starfieldCanvas.width, starfieldCanvas.height);
  }
}

/**
 * Toggle Cosmic Mode (opt-in glassmorphism + starfield).
 * Default = lightweight for low-end GPUs.
 */
function toggleCosmicMode() {
  isCosmicMode = document.body.classList.toggle('cosmic-mode');
  if (isCosmicMode) {
    localStorage.setItem('cosmic_mode', 'true');
    startStarfieldAnimation();
    if (DOM.btnToggleEco) {
      DOM.btnToggleEco.classList.add('active');
      DOM.btnToggleEco.innerHTML = '<i class="fa-solid fa-star"></i> Cosmic Active';
    }
    appendLog('[~] Cosmic Mode: ON. Starfield and glassmorphism enabled.');
  } else {
    localStorage.setItem('cosmic_mode', 'false');
    stopStarfieldAnimation();
    if (DOM.btnToggleEco) {
      DOM.btnToggleEco.classList.remove('active');
      DOM.btnToggleEco.innerHTML = '<i class="fa-solid fa-star"></i> Cosmic Mode';
    }
    appendLog('[~] Cosmic Mode: OFF. Lightweight mode for performance.');
  }
}

/**
 * Export logs by opening the export endpoint in a new tab.
 */
function exportLogs() {
  window.open('/api/logs/export', '_blank');
}

/**
 * Synchronize live UI state (running state, metrics, progress, logs) on dynamic reload / reconnection.
 */
function syncAttackStatus(statusData) {
  if (!statusData) return;
  const isRunning = Boolean(statusData.running);
  if (DOM.btnStart) DOM.btnStart.disabled = isRunning;
  if (DOM.btnStop) DOM.btnStop.disabled = !isRunning;

  if (statusData.metrics && Object.keys(statusData.metrics).length > 0) {
    updateStats(statusData.metrics);
    const attempted = statusData.metrics.attempted || 0;
    const total = statusData.metrics.total || 0;
    if (total > 0) {
      setProgress((attempted / total) * 100);
    }
  }

  if (Array.isArray(statusData.recent_logs) && statusData.recent_logs.length > 0) {
    if (DOM.terminal && !DOM.terminal.dataset.replayed) {
      DOM.terminal.innerHTML = '';
      DOM.terminal.dataset.replayed = 'true';
      statusData.recent_logs.forEach(msg => appendLog(msg));
    }
  }
}

/**
 * Clear all lines from the terminal and clear server buffer.
 */
function clearLogs() {
  logQueue.length = 0;
  if (DOM.terminal) {
    DOM.terminal.innerHTML = '';
    DOM.terminal.dataset.replayed = 'true';
  }
  postJSON('/api/logs/clear', {}).catch(() => {});
  appendLog('[~] Console cleared.');
}


// ═══════════════════════════════════════════════════════════════
//  SOCKET.IO EVENT HANDLERS
// ═══════════════════════════════════════════════════════════════

socket.on('connect', () => {
  DOM.connectionDot.className   = 'status-dot connected';
  DOM.connectionLabel.textContent = 'Connected';
  appendLog('[+] Socket connected to server.');
});

socket.on('disconnect', () => {
  DOM.connectionDot.className   = 'status-dot disconnected';
  DOM.connectionLabel.textContent = 'Disconnected';
  appendLog('[-] Socket disconnected from server.');
});

socket.on('status', (data) => {
  syncAttackStatus(data);
});

socket.on('log', (data) => {
  const message = typeof data === 'string' ? data : data.message || '';
  if (message) {
    appendLog(message);
  }
});

socket.on('progress', (data) => {
  const percent = data.total ? (data.current / data.total) * 100 : 0;
  setProgress(percent);
});

socket.on('metrics', (data) => {
  updateStats(data);
});

socket.on('finished', (data) => {
  const message = data?.message || 'Attack finished.';
  appendLog(`[+] ${message}`);
  DOM.btnStart.disabled = false;
  DOM.btnStop.disabled  = true;
  setProgress(100);
});

socket.on('cupp_done', (data) => {
  cuppResultPath = data?.path || '';
  const count = data?.count || '?';
  DOM.cuppStatus.textContent = `${count} passwords generated`;
  DOM.btnUseCupp.disabled    = false;
  DOM.btnGenerateCupp.disabled = false;
  appendLog(`[+] CUPP wordlist ready: ${cuppResultPath}`);
});

socket.on('sequence_done', (data) => {
  sequenceResultPath = data?.path || '';
  DOM.seqStatus.textContent = 'Sequence ready';
  DOM.btnUseSeq.disabled = false;
  DOM.btnGenerateSeq.disabled = false;
  appendLog(`[+] Sequence wordlist ready: ${sequenceResultPath}`);
});


// ═══════════════════════════════════════════════════════════════
//  EVENT LISTENERS — Wire Everything Up
// ═══════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {

  // Initialize Cosmic Mode from storage (default = OFF = lightweight)
  isCosmicMode = localStorage.getItem('cosmic_mode') === 'true';
  if (isCosmicMode) {
    document.body.classList.add('cosmic-mode');
    if (DOM.btnToggleEco) {
      DOM.btnToggleEco.classList.add('active');
      DOM.btnToggleEco.innerHTML = '<i class="fa-solid fa-star"></i> Cosmic Active';
    }
  }

  // Initialize background starfield animation
  initStarfield();

  // ── Tab buttons ──
  DOM.tabButtons.forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  // ── Attack Mode Toggle ──
  if (DOM.attackMode) {
    DOM.attackMode.addEventListener('change', onModeChange);
  }

  // ── Header Actions ──
  if (DOM.btnLaunchDemo) {
    DOM.btnLaunchDemo.addEventListener('click', launchDemoMode);
  }
  if (DOM.btnToggleEco) {
    DOM.btnToggleEco.addEventListener('click', toggleCosmicMode);
  }

  // ── Control Buttons ──
  if (DOM.btnStart) {
    DOM.btnStart.addEventListener('click', startAttack);
  }
  if (DOM.btnStop) {
    DOM.btnStop.addEventListener('click', stopAttack);
  }
  if (DOM.btnExport) {
    DOM.btnExport.addEventListener('click', exportLogs);
  }
  if (DOM.btnClear) {
    DOM.btnClear.addEventListener('click', clearLogs);
  }
  if (DOM.btnResetConfig) {
    DOM.btnResetConfig.addEventListener('click', resetFormState);
  }

  // ── CUPP Buttons ──
  if (DOM.btnGenerateCupp) {
    DOM.btnGenerateCupp.addEventListener('click', generateCupp);
  }
  if (DOM.btnUseCupp) {
    DOM.btnUseCupp.addEventListener('click', useCuppResult);
  }

  // ── Sequence Buttons ──
  if (DOM.btnGenerateSeq) {
    DOM.btnGenerateSeq.addEventListener('click', generateSequence);
  }
  if (DOM.btnUseSeq) {
    DOM.btnUseSeq.addEventListener('click', useSequenceResult);
  }



  // ── Session resume ──
  if (DOM.btnResume) {
    DOM.btnResume.addEventListener('click', resumeAttack);
  }
  if (DOM.btnDismissResume) {
    DOM.btnDismissResume.addEventListener('click', () => {
      DOM.resumeBanner.classList.remove('visible');
    });
  }

  // ── Multi-target queue ──
  if (DOM.btnAddTarget) {
    DOM.btnAddTarget.addEventListener('click', addTarget);
  }
  if (DOM.btnStartAllTargets) {
    DOM.btnStartAllTargets.addEventListener('click', startAllTargets);
  }

  // ── Scheduler ──
  if (DOM.btnScheduleAttack) {
    DOM.btnScheduleAttack.addEventListener('click', scheduleAttack);
  }

  // ── Alerts ──
  if (DOM.btnSaveNotifications) {
    DOM.btnSaveNotifications.addEventListener('click', saveNotificationConfig);
  }
  if (DOM.btnTestDiscord) {
    DOM.btnTestDiscord.addEventListener('click', testDiscordNotif);
  }
  if (DOM.btnTestTelegram) {
    DOM.btnTestTelegram.addEventListener('click', testTelegramNotif);
  }

  // ── Report & JSON Downloads ──
  if (DOM.btnReport) {
    DOM.btnReport.addEventListener('click', downloadReport);
  }
  if (DOM.btnDownloadJson) {
    DOM.btnDownloadJson.addEventListener('click', () => {
      window.open('/api/report/json', '_blank');
    });
  }

  // ── Target Tech Scanner ──
  if (DOM.btnScanTarget) {
    DOM.btnScanTarget.addEventListener('click', scanTargetTech);
  }

  // ── Doctor Modal ──
  if (DOM.btnDoctor) {
    DOM.btnDoctor.addEventListener('click', openDoctorModal);
  }
  if (DOM.btnCloseDoctor) {
    DOM.btnCloseDoctor.addEventListener('click', () => DOM.doctorModal?.classList.remove('active'));
  }
  if (DOM.btnCloseDoctorBtn) {
    DOM.btnCloseDoctorBtn.addEventListener('click', () => DOM.doctorModal?.classList.remove('active'));
  }
  if (DOM.btnRerunDoctor) {
    DOM.btnRerunDoctor.addEventListener('click', runDoctorChecks);
  }

  // ── Welcome & Tutorial Modal ──
  if (DOM.tutorialModal) {
    // Show warning on start
    DOM.tutorialModal.classList.add('active');

    // Agree & Proceed close button
    if (DOM.btnAgreeDisclaimer) {
      DOM.btnAgreeDisclaimer.addEventListener('click', () => {
        DOM.tutorialModal.classList.remove('active');
      });
    }

    // Close buttons (&times;)
    if (DOM.btnCloseModal) {
      DOM.btnCloseModal.addEventListener('click', () => {
        DOM.tutorialModal.classList.remove('active');
      });
    }

    // Finish guide close button
    if (DOM.btnFinishTutorial) {
      DOM.btnFinishTutorial.addEventListener('click', () => {
        DOM.tutorialModal.classList.remove('active');
      });
    }

    // Stepper from disclaimer to guide
    if (DOM.btnShowTutorialFromStart) {
      DOM.btnShowTutorialFromStart.addEventListener('click', () => {
        DOM.panelDisclaimer.classList.remove('active');
        DOM.panelTutorial.classList.add('active');
      });
    }

    // Go back to disclaimer
    if (DOM.btnBackToDisclaimer) {
      DOM.btnBackToDisclaimer.addEventListener('click', () => {
        DOM.panelTutorial.classList.remove('active');
        DOM.panelDisclaimer.classList.add('active');
      });
    }

    // Floating Info Button triggers guide directly
    if (DOM.btnInfo) {
      DOM.btnInfo.addEventListener('click', () => {
        DOM.panelDisclaimer.classList.remove('active');
        DOM.panelTutorial.classList.add('active');
        DOM.tutorialModal.classList.add('active');
      });
    }

    // Tutorial tab buttons wiring
    DOM.tutTabButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        DOM.tutTabButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        const targetTut = btn.dataset.tut;
        DOM.tutContents.forEach(content => {
          if (content.id === targetTut) {
            content.classList.add('active');
          } else {
            content.classList.remove('active');
          }
        });
      });
    });
  }

  // Initialize features
  initCharts();
  checkSessionStatus();
  refreshTargets();
  refreshScheduled();

  // Restore persistent configuration from localStorage / disk and bind auto-save
  restoreFormState().then(() => {
    bindAutoSave();
    const activeTab = localStorage.getItem('bluecrack_active_tab') || 'target';
    switchTab(activeTab);
  });

  // Fetch live attack status & logs immediately to handle dynamic reload
  fetch('/api/attack/status')
    .then(res => res.json())
    .then(data => {
      if (data && data.status === 'ok') {
        syncAttackStatus(data);
      }
    })
    .catch(() => {});

  appendLog('[~] All systems nominal. Ready.');
});

// ── Chart.js Setup ──
let speedChart = null;
let resultsChart = null;
const speedHistory = [];

function initCharts() {
  const speedCtx = document.getElementById('speedChart')?.getContext('2d');
  if (speedCtx) {
    speedChart = new Chart(speedCtx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label: 'Attempts/sec',
          data: [],
          borderColor: '#6c5ce7',
          backgroundColor: 'rgba(108, 92, 231, 0.1)',
          fill: true,
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { beginAtZero: true } },
        plugins: { legend: { display: false } },
        animation: { duration: 300 }
      }
    });
  }
  
  const resultsCtx = document.getElementById('resultsChart')?.getContext('2d');
  if (resultsCtx) {
    resultsChart = new Chart(resultsCtx, {
      type: 'doughnut',
      data: {
        labels: ['Success', 'Failed', 'Errors', 'Skipped'],
        datasets: [{
          data: [0, 0, 0, 0],
          backgroundColor: ['#10b981', '#ef4444', '#eab308', '#6b7280']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom', labels: { color: '#9ca3af' } } }
      }
    });
  }
}

function updateCharts(metrics) {
  if (!speedChart || !resultsChart) return;
  const now = new Date().toLocaleTimeString();
  speedHistory.push({ time: now, speed: metrics.speed || 0 });
  if (speedHistory.length > 30) speedHistory.shift();
  speedChart.data.labels = speedHistory.map(s => s.time);
  speedChart.data.datasets[0].data = speedHistory.map(s => s.speed);
  speedChart.update('none');
  
  resultsChart.data.datasets[0].data = [
    metrics.successes || metrics.hits || 0,
    metrics.failures || 0,
    metrics.errors || 0,
    (metrics.skipped_empty || 0) + (metrics.skipped_solved_user || 0)
  ];
  resultsChart.update('none');
}

// ── Session Resume ──
async function checkSessionStatus() {
  try {
    const res = await fetch('/api/session/status');
    const status = await res.json();
    if (status.has_session) {
      DOM.resumeBanner.classList.add('visible');
    }
  } catch (e) {}
}

async function resumeAttack() {
  DOM.resumeBanner.classList.remove('visible');
  appendLog('[*] Resuming attack...');
  try {
    const res = await fetch('/api/attack/resume', { method: 'POST' });
    const data = await res.json();
    if (data.status === 'ok') {
      appendLog(`[+] ${data.message}`);
      DOM.btnStart.disabled = true;
      DOM.btnStop.disabled = false;
    } else {
      appendLog(`[-] Resume failed: ${data.message}`);
    }
  } catch (err) {
    appendLog(`[-] Resume error: ${err.message}`);
  }
}

// ── Target Queue ──
let targetList = [];

function getTargetConfig() {
  return {
    target_url: DOM.targetUrl.value.trim(),
    username: DOM.username.value.trim(),
    password: DOM.password.value.trim(),
    error_msg: DOM.errorString.value.trim(),
    success_msg: DOM.successString.value.trim(),
    mode: DOM.attackMode.value,
    threads: parseInt(DOM.threads.value, 10) || 1,
    delay: parseFloat(DOM.delay.value) || 0,
    jitter: parseFloat(DOM.jitter.value) || 0,
    limit_text: DOM.rateLimit.value.trim(),
    cooldown: parseInt(DOM.cooldown.value, 10) || 12,
    max_attempts: parseInt(DOM.maxAttempts.value, 10) || 0,
    headless: DOM.headless.checked,
    continue_after_success: DOM.continueAfterSuccess.checked,
    spray_mode: DOM.sprayMode.checked
  };
}

async function addTarget() {
  const config = getTargetConfig();
  if (!config.target_url) {
    appendLog('[-] Target URL is required.');
    return;
  }
  try {
    const res = await postJSON('/api/targets/add', config);
    if (res.status === 'ok') {
      appendLog(`[+] Target added to queue: ${config.target_url}`);
      await refreshTargets();
    }
  } catch (e) {
    appendLog(`[-] Failed to add target: ${e.message}`);
  }
}

async function refreshTargets() {
  try {
    const res = await fetch('/api/targets/list');
    const data = await res.json();
    targetList = data.targets || [];
    renderTargets();
    
    if (targetList.length > 0) {
      DOM.btnStartAllTargets.disabled = false;
    } else {
      DOM.btnStartAllTargets.disabled = true;
    }
  } catch (e) {}
}

function renderTargets() {
  if (targetList.length === 0) {
    DOM.targetList.innerHTML = `<p style="color: var(--text-muted); font-size: 0.8rem; text-align: center; padding: 20px;">No targets added yet.</p>`;
    return;
  }
  DOM.targetList.innerHTML = targetList.map((t, idx) => `
    <div class="target-item" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
      <span class="target-url">${escapeHTML(t.config?.target_url || '')}</span>
      <span class="target-status ${escapeHTML(t.status)}">${escapeHTML(t.status)}</span>
      <button class="btn btn-ghost btn-sm" onclick="removeTargetAt(${parseInt(t.index, 10)})">Remove</button>
    </div>
  `).join('');
}

window.removeTargetAt = async function(index) {
  try {
    const res = await postJSON('/api/targets/remove', { index: parseInt(index, 10) });
    if (res.status === 'ok') {
      appendLog('[+] Target removed from queue.');
      await refreshTargets();
    }
  } catch (e) {}
}

async function startAllTargets() {
  appendLog('[*] Starting sequential multi-target attack...');
  const snapshot = [...targetList];
  for (let t of snapshot) {
    if (t.status === 'pending') {
      const c = t.config || {};
      DOM.targetUrl.value = c.target_url || '';
      DOM.username.value = c.username || '';
      DOM.password.value = c.password || '';
      DOM.errorString.value = c.error_msg || '';
      DOM.successString.value = c.success_msg || '';
      DOM.attackMode.value = c.mode || 'browser';
      DOM.threads.value = c.threads || 4;
      DOM.delay.value = c.delay || 0;
      DOM.jitter.value = c.jitter || 0;
      DOM.rateLimit.value = c.limit_text || '';
      DOM.cooldown.value = c.cooldown || 0;
      DOM.maxAttempts.value = c.max_attempts || 0;
      DOM.headless.checked = Boolean(c.headless);
      DOM.continueAfterSuccess.checked = Boolean(c.continue_after_success);
      DOM.sprayMode.checked = Boolean(c.spray_mode);
      
      await startAttack();
      
      let waitLimit = 300; // 5 minute max wait per target
      while (DOM.btnStart.disabled && waitLimit > 0) {
        await new Promise(r => setTimeout(r, 1000));
        waitLimit--;
      }
      await refreshTargets();
    }
  }
  appendLog('[+] Sequential multi-target attack complete!');
}

// ── Scheduler ──
async function scheduleAttack() {
  const timeVal = DOM.scheduleTime.value;
  if (!timeVal) {
    appendLog('[-] Schedule time is required.');
    return;
  }
  const config = getTargetConfig();
  try {
    const res = await postJSON('/api/schedule/add', { target_url: config.target_url, run_at: timeVal, ...config });
    if (res.status === 'ok') {
      appendLog(`[+] Attack scheduled successfully for ${timeVal}`);
      await refreshScheduled();
    } else {
      appendLog(`[-] Failed to schedule: ${res.message || 'Error'}`);
    }
  } catch (e) {
    appendLog(`[-] Schedule error: ${e.message}`);
  }
}

async function refreshScheduled() {
  try {
    const res = await fetch('/api/schedule/list');
    const data = await res.json();
    renderScheduled(data.scheduled || []);
  } catch (e) {}
}

function renderScheduled(list) {
  if (list.length === 0) {
    DOM.scheduleList.innerHTML = `<p style="color: var(--text-muted); font-size: 0.8rem; text-align: center; padding: 20px;">No scheduled attacks.</p>`;
    return;
  }
  DOM.scheduleList.innerHTML = list.map(s => `
    <div class="schedule-card" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
      <span class="schedule-time">${escapeHTML(new Date(s.run_at).toLocaleString())}</span>
      <span class="schedule-target">${escapeHTML(s.target_url)}</span>
      <span class="target-status ${escapeHTML(s.status)}">${escapeHTML(s.status)}</span>
      <button class="btn btn-ghost btn-sm" data-cancel-id="${escapeHTML(s.id)}">Cancel</button>
    </div>
  `).join('');

  // Event delegation for cancel buttons
  DOM.scheduleList.querySelectorAll('[data-cancel-id]').forEach(btn => {
    btn.addEventListener('click', () => cancelScheduled(btn.dataset.cancelId));
  });
}

window.cancelScheduled = async function(id) {
  try {
    const res = await postJSON('/api/schedule/cancel', { id });
    if (res.status === 'ok') {
      appendLog('[+] Scheduled attack cancelled.');
      await refreshScheduled();
    }
  } catch (e) {}
}

// ── Alerts ──
async function saveNotificationConfig() {
  const payload = {
    discord_url: DOM.discordWebhook ? DOM.discordWebhook.value.trim() : '',
    telegram_token: DOM.telegramToken ? DOM.telegramToken.value.trim() : '',
    telegram_chat_id: DOM.telegramChatId ? DOM.telegramChatId.value.trim() : ''
  };
  saveFormState();
  try {
    const res = await postJSON('/api/notifications/configure', payload);
    if (res.status === 'ok') {
      DOM.notifStatus.textContent = 'Configuration saved!';
      setTimeout(() => { if (DOM.notifStatus) DOM.notifStatus.textContent = ''; }, 3000);
      appendLog('[+] Notification configuration saved & synchronized.');
    }
  } catch (e) {}
}

async function testDiscordNotif() {
  await saveNotificationConfig();
  try {
    const res = await postJSON('/api/notifications/test', {});
    if (res.results && res.results.discord) {
      appendLog('[+] Discord test notification sent successfully!');
    } else {
      appendLog('[-] Discord test notification failed.');
    }
  } catch (e) {}
}

async function testTelegramNotif() {
  await saveNotificationConfig();
  try {
    const res = await postJSON('/api/notifications/test', {});
    if (res.results && res.results.telegram) {
      appendLog('[+] Telegram test notification sent successfully!');
    } else {
      appendLog('[-] Telegram test notification failed.');
    }
  } catch (e) {}
}

// ── Report ──
function downloadReport() {
  window.open('/api/report/html', '_blank');
}

// ── Target Tech Scanner ──
async function scanTargetTech() {
  const url = DOM.targetUrl?.value.trim();
  if (!url) {
    appendLog('[-] Enter a Target URL first to scan.');
    DOM.targetUrl?.focus();
    return;
  }
  appendLog(`[*] Fingerprinting technology stack for ${url}…`);
  if (DOM.btnScanTarget) {
    DOM.btnScanTarget.disabled = true;
    DOM.btnScanTarget.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Scanning…';
  }

  try {
    const res = await postJSON('/api/target/fingerprint', { target_url: url });
    if (res.status === 'ok' && res.fingerprint) {
      const fp = res.fingerprint;
      appendLog(`[+] Tech scan complete for ${url}`);
      if (DOM.targetTechBadge) {
        let pills = '';
        (fp.frameworks || []).forEach(fw => {
          pills += `<span class="tech-pill tech-pill-fw"><i class="fa-solid fa-code"></i> ${escapeHTML(fw)}</span>`;
        });
        (fp.servers || []).forEach(srv => {
          pills += `<span class="tech-pill tech-pill-server"><i class="fa-solid fa-server"></i> ${escapeHTML(srv)}</span>`;
        });
        (fp.protections || []).forEach(prot => {
          pills += `<span class="tech-pill tech-pill-waf"><i class="fa-solid fa-shield"></i> ${escapeHTML(prot)}</span>`;
        });
        if (fp.form && fp.form.csrf_field) {
          pills += `<span class="tech-pill tech-pill-csrf"><i class="fa-solid fa-key"></i> CSRF: ${escapeHTML(fp.form.csrf_field)}</span>`;
        }
        if (!pills) {
          pills = '<span class="tech-pill">No specific framework headers found</span>';
        }
        DOM.targetTechBadge.innerHTML = pills;
        DOM.targetTechBadge.style.display = 'flex';
      }

      // Auto-fill form fields if in HTTP mode or if empty
      if (fp.form) {
        if (DOM.formAction && !DOM.formAction.value && fp.form.action) {
          DOM.formAction.value = fp.form.action;
        }
        if (DOM.usernameField && !DOM.usernameField.value && fp.form.username_field) {
          DOM.usernameField.value = fp.form.username_field;
        }
        if (DOM.passwordField && !DOM.passwordField.value && fp.form.password_field) {
          DOM.passwordField.value = fp.form.password_field;
        }
        if (DOM.csrfField && !DOM.csrfField.value && fp.form.csrf_field) {
          DOM.csrfField.value = fp.form.csrf_field;
        }
        saveFormState();
      }
    } else {
      appendLog(`[-] Fingerprint scan failed: ${res.message || 'Target unreachable'}`);
    }
  } catch (err) {
    appendLog(`[-] Fingerprint scan error: ${err.message}`);
  } finally {
    if (DOM.btnScanTarget) {
      DOM.btnScanTarget.disabled = false;
      DOM.btnScanTarget.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Scan Tech';
    }
  }
}

// ── Doctor Environment Diagnostics ──
function openDoctorModal() {
  if (DOM.doctorModal) {
    DOM.doctorModal.classList.add('active');
    runDoctorChecks();
  }
}

async function runDoctorChecks() {
  if (!DOM.doctorChecksContainer) return;
  DOM.doctorChecksContainer.innerHTML = '<div style="text-align:center; padding: 20px; color: var(--text-muted);"><i class="fa-solid fa-spinner fa-spin"></i> Running diagnostics…</div>';

  try {
    const res = await fetch('/api/doctor');
    const data = await res.json();
    if (data.status === 'ok' && data.report) {
      const checks = data.report.checks || [];
      DOM.doctorChecksContainer.innerHTML = checks.map(c => {
        let badgeIcon = 'fa-check';
        let badgeText = 'PASS';
        let statusClass = 'ok';
        if (c.status === 'warn') {
          badgeIcon = 'fa-triangle-exclamation';
          badgeText = 'WARN';
          statusClass = 'warn';
        } else if (c.status === 'fail') {
          badgeIcon = 'fa-xmark';
          badgeText = 'FAIL';
          statusClass = 'fail';
        }

        return `
          <div class="doctor-check-item">
            <div class="doctor-check-info">
              <span class="doctor-check-title">${escapeHTML(c.name)}</span>
              <span class="doctor-check-detail">${escapeHTML(c.detail)}</span>
            </div>
            <span class="doctor-check-badge ${statusClass}">
              <i class="fa-solid ${badgeIcon}"></i> ${badgeText}
            </span>
          </div>
        `;
      }).join('');
    } else {
      DOM.doctorChecksContainer.innerHTML = `<div style="color: var(--danger); padding: 10px;">Failed to fetch diagnostics: ${escapeHTML(data.message)}</div>`;
    }
  } catch (e) {
    DOM.doctorChecksContainer.innerHTML = `<div style="color: var(--danger); padding: 10px;">Diagnostic error: ${escapeHTML(e.message)}</div>`;
  }
}

