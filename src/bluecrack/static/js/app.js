/* ═══════════════════════════════════════════════════════════════
   BlueCrack — Frontend Application Logic
   ═══════════════════════════════════════════════════════════════ */

'use strict';

// ─── Socket.IO Connection ──────────────────────────────────────
const socket = io();

// ─── DOM References ────────────────────────────────────────────
// ─── DOM References ────────────────────────────────────────────
const DOM = {
  // New Header Actions
  btnLaunchDemo:   document.getElementById('btnLaunchDemo'),
  btnToggleEco:    document.getElementById('btnToggleEco'),
  btnThemeToggle:  document.getElementById('btnThemeToggle'),

  // Connection status
  connectionDot:   document.getElementById('connectionDot'),
  connectionLabel: document.getElementById('connectionLabel'),

  // Tab system
  tabButtons: document.querySelectorAll('.tab-btn'),
  tabPanels:  document.querySelectorAll('.tab-content'),

  // Target Config
  targetUrl:     document.getElementById('targetUrl'),
  username:      document.getElementById('username'),
  password:      document.getElementById('password'),
  errorString:   document.getElementById('errorString'),
  successString: document.getElementById('successString'),

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
  formAction:      document.getElementById('formAction'),
  usernameField:   document.getElementById('usernameField'),
  passwordField:   document.getElementById('passwordField'),
  csrfField:       document.getElementById('csrfField'),
  followRedirects: document.getElementById('followRedirects'),

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
  btnStart:  document.getElementById('btnStart'),
  btnStop:   document.getElementById('btnStop'),
  btnExport: document.getElementById('btnExport'),
  btnClear:  document.getElementById('btnClear'),
  btnReport: document.getElementById('btnReport'),

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
//  TAB SWITCHING
// ═══════════════════════════════════════════════════════════════

function switchTab(targetId) {
  DOM.tabButtons.forEach(btn => {
    const isTarget = btn.dataset.tab === targetId;
    btn.classList.toggle('active', isTarget);
    btn.setAttribute('aria-selected', isTarget);
  });

  DOM.tabPanels.forEach(panel => {
    panel.classList.toggle('active', panel.id === `tab-${targetId}`);
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
    config.form_action     = DOM.formAction.value.trim();
    config.username_field  = DOM.usernameField.value.trim();
    config.password_field  = DOM.passwordField.value.trim();
    config.csrf_field      = DOM.csrfField.value.trim();
    config.follow_redirects = DOM.followRedirects.checked;
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
  DOM.btnLaunchDemo.textContent = '⏳ Starting...';
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
      
      appendLog(`[~] Credentials and target configured: ${result.default_username} / ${result.default_password_file}`);
      switchTab('target');
    } else {
      appendLog(`[-] Demo launch error: ${result.message || 'Unknown error'}`);
    }
  } catch (err) {
    appendLog(`[-] Demo server request failed: ${err.message}`);
  } finally {
    DOM.btnLaunchDemo.disabled = false;
    DOM.btnLaunchDemo.textContent = '🚀 Demo Mode';
  }
}

// ─── Starfield Canvas Background Animation Loop ─────────────────
let starfieldCanvas = null;
let starfieldCtx = null;
let stars = [];
const numStars = 100;
let animationId = null;
let isEcoMode = false;

function initStarfield() {
  starfieldCanvas = document.getElementById('starfield');
  if (!starfieldCanvas) return;
  starfieldCtx = starfieldCanvas.getContext('2d');
  resizeStarfield();
  
  window.addEventListener('resize', resizeStarfield);
  
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
  
  if (!isEcoMode) {
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
    if (isEcoMode) return;
    
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
 * Toggle the Performance Eco-Astral Mode (Lag Fix).
 */
function toggleEcoMode() {
  isEcoMode = document.body.classList.toggle('eco-mode');
  if (isEcoMode) {
    localStorage.setItem('eco_mode', 'true');
    stopStarfieldAnimation();
    if (DOM.btnToggleEco) {
      DOM.btnToggleEco.classList.add('active');
      DOM.btnToggleEco.innerHTML = '⚡ Eco Active';
    }
    appendLog('[~] Eco-Astral Mode: ON. Starfield stopped, blurs disabled. Performance optimized.');
  } else {
    localStorage.setItem('eco_mode', 'false');
    startStarfieldAnimation();
    if (DOM.btnToggleEco) {
      DOM.btnToggleEco.classList.remove('active');
      DOM.btnToggleEco.innerHTML = '🍃 Eco Mode';
    }
    appendLog('[~] Eco-Astral Mode: OFF. Cosmic vibes and blurs enabled.');
  }
}

/**
 * Export logs by opening the export endpoint in a new tab.
 */
function exportLogs() {
  window.open('/api/logs/export', '_blank');
}

/**
 * Clear all lines from the terminal.
 */
function clearLogs() {
  logQueue.length = 0;
  DOM.terminal.innerHTML = '';
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
//  V4.0 — THEME SWITCHER (must be defined before DOMContentLoaded)
// ═══════════════════════════════════════════════════════════════

const ThemeManager = {
  init() {
    const saved = localStorage.getItem('bluecrack-theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = saved || (prefersDark ? 'dark' : 'light');
    this.set(theme);
  },
  toggle() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    this.set(current === 'dark' ? 'light' : 'dark');
  },
  set(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('bluecrack-theme', theme);
    const btn = DOM.btnThemeToggle;
    if (btn) btn.textContent = theme === 'dark' ? '☀️' : '🌙';
  }
};


// ═══════════════════════════════════════════════════════════════
//  EVENT LISTENERS — Wire Everything Up
// ═══════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {

  // Initialize Eco Mode from storage
  isEcoMode = localStorage.getItem('eco_mode') === 'true';
  if (isEcoMode) {
    document.body.classList.add('eco-mode');
    if (DOM.btnToggleEco) {
      DOM.btnToggleEco.classList.add('active');
      DOM.btnToggleEco.innerHTML = '⚡ Eco Active';
    }
  }

  // Initialize background starfield animation
  initStarfield();

  // ── Tab buttons ──
  DOM.tabButtons.forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  // ── Attack Mode Toggle ──
  function onModeChange() {
    const mode = DOM.attackMode.value;
    const isHttp = mode === 'http';
    DOM.httpModeOptions.style.display = isHttp ? 'block' : 'none';
    DOM.headlessGroup.style.display = isHttp ? 'none' : '';
    if (isHttp && parseInt(DOM.threads.value, 10) <= 1) {
      DOM.threads.value = '4';
    }
  }
  DOM.attackMode.addEventListener('change', onModeChange);

  // ── Header Actions ──
  if (DOM.btnLaunchDemo) {
    DOM.btnLaunchDemo.addEventListener('click', launchDemoMode);
  }
  if (DOM.btnToggleEco) {
    DOM.btnToggleEco.addEventListener('click', toggleEcoMode);
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

  // ── Theme toggle ──
  if (DOM.btnThemeToggle) {
    DOM.btnThemeToggle.addEventListener('click', () => ThemeManager.toggle());
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

  // ── Report ──
  if (DOM.btnReport) {
    DOM.btnReport.addEventListener('click', downloadReport);
  }

  // Initialize features
  ThemeManager.init();
  initCharts();
  checkSessionStatus();
  refreshTargets();
  refreshScheduled();

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
      <span class="target-url">${t.config.target_url}</span>
      <span class="target-status ${t.status}">${t.status}</span>
      <button class="btn btn-ghost btn-sm" onclick="removeTargetAt(${t.index})">Remove</button>
    </div>
  `).join('');
}

window.removeTargetAt = async function(index) {
  try {
    const res = await postJSON('/api/targets/remove', { index });
    if (res.status === 'ok') {
      appendLog('[+] Target removed from queue.');
      await refreshTargets();
    }
  } catch (e) {}
}

async function startAllTargets() {
  appendLog('[*] Starting sequential multi-target attack...');
  for (let t of targetList) {
    if (t.status === 'pending') {
      DOM.targetUrl.value = t.config.target_url;
      DOM.username.value = t.config.username;
      DOM.password.value = t.config.password;
      DOM.errorString.value = t.config.error_msg;
      DOM.successString.value = t.config.success_msg;
      DOM.attackMode.value = t.config.mode;
      DOM.threads.value = t.config.threads;
      DOM.delay.value = t.config.delay;
      DOM.jitter.value = t.config.jitter;
      DOM.rateLimit.value = t.config.limit_text;
      DOM.cooldown.value = t.config.cooldown;
      DOM.maxAttempts.value = t.config.max_attempts;
      DOM.headless.checked = t.config.headless;
      DOM.continueAfterSuccess.checked = t.config.continue_after_success;
      DOM.sprayMode.checked = t.config.spray_mode;
      
      await startAttack();
      
      while (DOM.btnStart.disabled) {
        await new Promise(r => setTimeout(r, 1000));
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
    const res = await postJSON('/api/schedule/create', { config, run_at: timeVal });
    if (res.status === 'ok') {
      appendLog(`[+] Attack scheduled successfully for ${timeVal}`);
      await refreshScheduled();
    } else {
      appendLog(`[-] Failed to schedule: ${res.message}`);
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
      <span class="schedule-time">${new Date(s.run_at).toLocaleString()}</span>
      <span class="schedule-target">${s.target_url}</span>
      <span class="target-status ${s.status}">${s.status}</span>
      <button class="btn btn-ghost btn-sm" onclick="cancelScheduled('${s.id}')">Cancel</button>
    </div>
  `).join('');
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
    discord_url: DOM.discordWebhook.value.trim(),
    telegram_token: DOM.telegramToken.value.trim(),
    telegram_chat_id: DOM.telegramChatId.value.trim()
  };
  try {
    const res = await postJSON('/api/notifications/configure', payload);
    if (res.status === 'ok') {
      DOM.notifStatus.textContent = 'Configuration saved!';
      setTimeout(() => DOM.notifStatus.textContent = '', 3000);
      appendLog('[+] Notification configuration updated.');
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
