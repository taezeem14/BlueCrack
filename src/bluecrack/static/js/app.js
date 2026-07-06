/* ═══════════════════════════════════════════════════════════════
   BlueCrack — Frontend Application Logic
   ═══════════════════════════════════════════════════════════════ */

'use strict';

// ─── Socket.IO Connection ──────────────────────────────────────
const socket = io();

// ─── DOM References ────────────────────────────────────────────
const DOM = {
  // New Header Actions
  btnLaunchDemo:   document.getElementById('btnLaunchDemo'),
  btnToggleEco:    document.getElementById('btnToggleEco'),

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

    // Show/hide HTTP-specific options
    DOM.httpModeOptions.style.display = isHttp ? 'block' : 'none';

    // Hide headless toggle in HTTP mode (irrelevant)
    DOM.headlessGroup.style.display = isHttp ? 'none' : '';

    // Default higher threads for HTTP mode
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

  // ── Control buttons ──
  DOM.btnStart.addEventListener('click', startAttack);
  DOM.btnStop.addEventListener('click', stopAttack);
  DOM.btnExport.addEventListener('click', exportLogs);
  DOM.btnClear.addEventListener('click', clearLogs);

  // ── CUPP buttons ──
  DOM.btnGenerateCupp.addEventListener('click', generateCupp);
  DOM.btnUseCupp.addEventListener('click', useCuppResult);

  // ── Sequence buttons ──
  DOM.btnGenerateSeq.addEventListener('click', generateSequence);
  DOM.btnUseSeq.addEventListener('click', useSequenceResult);

  // ── Browse button (password file picker via hidden input) ──
  DOM.btnBrowsePasswords = document.getElementById('btnBrowsePasswords');
  if (DOM.btnBrowsePasswords) {
    const fileInput = document.createElement('input');
    fileInput.type  = 'file';
    fileInput.style.display = 'none';
    fileInput.accept = '.txt,.lst,.csv,.dic';
    document.body.appendChild(fileInput);

    DOM.btnBrowsePasswords.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
        // In a web context, we display the filename;
        // the actual file upload would be handled by the backend.
        DOM.password.value = fileInput.files[0].name;
        appendLog(`[*] Selected file: ${fileInput.files[0].name}`);
      }
    });
  }

  appendLog('[~] All systems nominal. Ready.');
});
