/* ═══════════════════════════════════════════
   JARVIS DESKTOP v4 — renderer.js
   Architecture : Module pattern + Event-driven
═══════════════════════════════════════════ */

// ── STATE ─────────────────────────────────
const S = {
  listening: false,
  speaking: false,
  cameraActive: false,
  networkActive: false,
  recognition: null,
  recognitionLock: false,
  currentMode: 'normal',
  latencyStart: 0,
  reconnectTimer: null,
  apiOnline: false,
  lastMessages: [],
};

// ── BOOT SEQUENCE ─────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  bootSequence();
});

async function bootSequence() {
  const fill = document.getElementById('boot-fill');
  const screen = document.getElementById('boot-screen');

  // Animate progress bar
  let pct = 0;
  const interval = setInterval(() => {
    pct = Math.min(pct + Math.random() * 8 + 2, 95);
    if (fill) fill.style.width = pct + '%';
  }, 80);

  // Init everything
  initClock();
  initWaveform();
  initNetworkMap();
  initSpeechRecognition();
  initKeyboard();
  initTools();
  await checkApiHealth();

  // Move orb to corner after 1.8s
  setTimeout(() => {
    const orb = document.getElementById('jarvis-orb');
    if (orb) orb.classList.remove('mode-center');
  }, 1800);

  // Finish boot
  setTimeout(() => {
    clearInterval(interval);
    if (fill) fill.style.width = '100%';
    setTimeout(() => {
      screen.classList.add('hidden');
      setTimeout(() => screen.remove(), 900);
    }, 300);
  }, 2200);

  // Periodic health check
  setInterval(checkApiHealth, 12000);
}

// ── CLOCK ─────────────────────────────────
function initClock() {
  function tick() {
    const now = new Date();
    const t = now.toLocaleTimeString('fr-FR', { hour12: false });
    const t2 = now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    const el = document.getElementById('sys-time');
    if (el) el.textContent = t;
    document.getElementById('status-time').textContent = t2;
  }
  tick();
  setInterval(tick, 1000);
}

// ── WAVEFORM ──────────────────────────────
function initWaveform() {
  const canvas = document.getElementById('waveform-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  canvas.width = 460;
  canvas.height = 52;
  let analyser = null;
  let idle = 0;

  navigator.mediaDevices.getUserMedia({ audio: true, video: false })
    .then(stream => {
      const ac = new AudioContext();
      const src = ac.createMediaStreamSource(stream);
      analyser = ac.createAnalyser();
      analyser.fftSize = 128;
      src.connect(analyser);
    })
    .catch(() => {});

  function draw() {
    requestAnimationFrame(draw);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const bars = 58;
    const bw = canvas.width / bars - 1;
    const cy = canvas.height / 2;

    for (let i = 0; i < bars; i++) {
      let amp;
      if (analyser && S.listening) {
        const d = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(d);
        amp = d[i] / 255;
      } else {
        amp = (Math.sin(idle + i * 0.25) * 0.5 + 0.5) * 0.12 + 0.02;
      }
      const h = Math.max(2, amp * canvas.height * 0.85);
      const alpha = 0.25 + amp * 0.75;
      ctx.fillStyle = `rgba(${Math.floor(amp*120)},${180+Math.floor(amp*75)},255,${alpha})`;
      ctx.fillRect(i * (bw + 1), cy - h / 2, bw, h);
    }
    idle += 0.025;
  }
  draw();
}

// ── NETWORK MAP ───────────────────────────
let networkMap = null;

function initNetworkMap() {
  const canvas = document.getElementById('network-canvas');
  if (!canvas) return;
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    if (networkMap) { networkMap.nodes = []; networkMap.connections = [];
      networkMap.generateNodes(80); networkMap.generateConnections(); }
  });
  networkMap = new NetworkMap(canvas);
}

function showNetworkMap() {
  if (!networkMap) return;
  document.getElementById('network-canvas').style.opacity = '0.55';
  networkMap.start();
  S.networkActive = true;
}

function hideNetworkMap() {
  document.getElementById('network-canvas').style.opacity = '0';
  if (networkMap) networkMap.stop();
  S.networkActive = false;
}

class NetworkMap {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.nodes = [];
    this.connections = [];
    this.raf = null;
    this.lastT = 0;
    this.generateNodes(80);
    this.generateConnections();
  }
  generateNodes(n) {
    for (let i = 0; i < n; i++) {
      this.nodes.push({
        x: Math.random() * this.canvas.width,
        y: Math.random() * this.canvas.height,
        r: Math.random() * 2.2 + 0.5,
        phase: Math.random() * Math.PI * 2,
        hub: Math.random() < 0.1,
      });
    }
  }
  generateConnections() {
    this.nodes.forEach((n, i) => {
      this.nodes.map((o, j) => ({ j, d: Math.hypot(o.x - n.x, o.y - n.y) }))
        .filter(x => x.j !== i && x.d < 170).sort((a, b) => a.d - b.d).slice(0, 3)
        .forEach(x => {
          if (!this.connections.find(c =>
            (c.a === i && c.b === x.j) || (c.a === x.j && c.b === i)))
            this.connections.push({ a: i, b: x.j, op: Math.random() * 0.28 + 0.04 });
        });
    });
  }
  draw(ts) {
    this.raf = requestAnimationFrame(t => this.draw(t));
    if (ts - this.lastT < 34) return;
    this.lastT = ts;
    const { ctx, canvas, nodes, connections } = this;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    connections.forEach(c => {
      const a = nodes[c.a], b = nodes[c.b];
      const g = ctx.createLinearGradient(a.x, a.y, b.x, b.y);
      g.addColorStop(0,   `rgba(0,80,120,${c.op})`);
      g.addColorStop(0.5, `rgba(0,140,190,${c.op*1.6})`);
      g.addColorStop(1,   `rgba(0,80,120,${c.op})`);
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
      ctx.strokeStyle = g; ctx.lineWidth = 0.5; ctx.stroke();
    });
    nodes.forEach(n => {
      const p = Math.sin(ts * 0.002 + n.phase) * 0.5 + 0.5;
      const r = n.hub ? n.r * 2.8 : n.r;
      const alpha = n.hub ? 0.65 + p * 0.35 : 0.28 + p * 0.28;
      const col = n.hub ? `rgba(0,255,136,${alpha})` : `rgba(0,212,255,${alpha})`;
      if (n.hub) {
        ctx.beginPath(); ctx.arc(n.x, n.y, r * 4, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0,255,136,${0.025 * p})`; ctx.fill();
      }
      ctx.beginPath(); ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
      ctx.fillStyle = col; ctx.fill();
    });
  }
  start() { requestAnimationFrame(t => this.draw(t)); }
  stop()  { cancelAnimationFrame(this.raf); }
}

// ── SPEECH RECOGNITION ───────────────────
function initSpeechRecognition() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    console.warn('[JARVIS] SpeechRecognition non disponible sur ce navigateur');
    return;
  }
  S.recognition = new SR();
  S.recognition.continuous = true;
  S.recognition.interimResults = true;
  S.recognition.lang = 'fr-FR';

  S.recognition.onstart = () => { S.recognitionLock = true; };
  S.recognition.onend = () => {
    S.recognitionLock = false;
    if (S.listening) {
      setTimeout(() => {
        if (S.listening && !S.recognitionLock) safeStart();
      }, 300);
    }
  };
  S.recognition.onerror = (e) => {
    S.recognitionLock = false;
    if (['no-speech', 'audio-capture'].includes(e.error)) return; // silencieux
    if (e.error === 'not-allowed') {
      addSystemMsg(' Microphone non autorisé — Paramètres → Confidentialité → Microphone');
      stopListening();
    }
  };
  S.recognition.onresult = (e) => {
    const last = e.results[e.results.length - 1];
    if (last.isFinal) {
      const text = last[0].transcript.trim();
      if (text.length > 1) sendToJarvis(text);
    }
  };
}

function safeStart() {
  if (!S.recognition || S.recognitionLock) return;
  try { S.recognition.start(); } catch(e) {}
}

function startListening() {
  S.listening = true;
  safeStart();
  setMicStatus(true);
}

function stopListening() {
  S.listening = false;
  if (S.recognition && S.recognitionLock) {
    try { S.recognition.stop(); } catch(e) {}
  }
  setMicStatus(false);
}

function toggleListening() {
  if (S.listening) stopListening(); else startListening();
}

function setMicStatus(on) {
  const el = document.getElementById('mic-status');
  const dot = document.getElementById('status-dot');
  if (!el) return;
  if (on) {
    el.textContent = 'ÉCOUTE';
    el.style.color = 'var(--green)';
    el.style.textShadow = '0 0 8px rgba(0,255,136,0.6)';
    document.getElementById('jarvis-orb').classList.add('state-listening');
    if (dot) dot.className = 'dot dot-online';
    document.getElementById('status-text').textContent = 'EN ÉCOUTE';
  } else {
    el.textContent = 'VEILLE';
    el.style.color = '';
    el.style.textShadow = '';
    document.getElementById('jarvis-orb').classList.remove('state-listening');
    if (dot) dot.className = S.apiOnline ? 'dot dot-online' : 'dot dot-offline';
    document.getElementById('status-text').textContent = 'EN ATTENTE';
  }
}

// ── SEND TO JARVIS ────────────────────────
async function sendToJarvis(message) {
  if (!message.trim()) return;
  S.lastMessages.push(message);
  if (S.lastMessages.length > 20) S.lastMessages.shift();

  addUserMsg(message);
  setThinkingState(true);
  S.latencyStart = Date.now();

  try {
    const res = await fetchWithTimeout('/api/tool-chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    }, 18000);

    const data = await res.json();
    const latency = Date.now() - S.latencyStart;
    document.getElementById('latency-display').textContent = latency + 'ms';

    setThinkingState(false);
    addJarvisMsg(data.reply || 'Pas de réponse.', data.mode_used || 'normal');

    if (data.action) handleAction(data.action);
    if (data.mode_used) updateModeDisplay(data.mode_used);

  } catch (err) {
    setThinkingState(false);
    addJarvisMsg('Serveur non disponible. Lance START_JARVIS.bat et vérifie que server.py tourne.', 'error');
    checkApiHealth();
  }
}

function fetchWithTimeout(url, opts, timeout) {
  return Promise.race([
    fetch(url, opts),
    new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), timeout))
  ]);
}

// ── MESSAGES ─────────────────────────────
function addUserMsg(text) {
  const zone = document.getElementById('chat-zone');
  const div = document.createElement('div');
  div.className = 'msg msg-user';
  div.innerHTML = `<div class="msg-label">VOUS</div><div class="msg-bubble">${escHtml(text)}</div>`;
  zone.appendChild(div);
  scrollChat();
  scheduleAutoRemove(div, 45000);
}

function addJarvisMsg(text, mode = 'normal') {
  const zone = document.getElementById('chat-zone');
  const div = document.createElement('div');
  div.className = 'msg msg-jarvis';

  const modeBadge = getModeHtml(mode);
  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble typing-cursor';

  div.innerHTML = `<div class="msg-label">JARVIS</div>${modeBadge}`;
  div.appendChild(bubble);
  zone.appendChild(div);
  scrollChat();

  // Typing effect
  let i = 0;
  const clean = text.replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const tid = setInterval(() => {
    bubble.innerHTML = clean.slice(0, ++i);
    scrollChat();
    if (i >= clean.length) {
      bubble.classList.remove('typing-cursor');
      clearInterval(tid);
    }
  }, 14);

  scheduleAutoRemove(div, 60000);
}

function addSystemMsg(text) {
  const zone = document.getElementById('chat-zone');
  const div = document.createElement('div');
  div.className = 'msg-system';
  div.textContent = text;
  zone.appendChild(div);
  scrollChat();
  setTimeout(() => { div.style.opacity = '0'; div.style.transition = 'opacity 1s'; setTimeout(() => div.remove(), 1000); }, 6000);
}

function addThinkingIndicator() {
  removeThinkingIndicator();
  const zone = document.getElementById('chat-zone');
  const div = document.createElement('div');
  div.id = 'thinking-indicator';
  div.className = 'msg msg-jarvis';
  div.innerHTML = `<div class="msg-label">JARVIS</div>
    <div class="msg-bubble">
      <div class="thinking-dots">
        <span></span><span></span><span></span>
      </div>
    </div>`;
  zone.appendChild(div);
  scrollChat();
}

function removeThinkingIndicator() {
  const el = document.getElementById('thinking-indicator');
  if (el) el.remove();
}

function setThinkingState(on) {
  const orb = document.getElementById('jarvis-orb');
  if (on) {
    orb.classList.add('state-thinking');
    orb.classList.remove('state-speaking');
    addThinkingIndicator();
    document.getElementById('status-text').textContent = 'TRAITEMENT...';
    document.getElementById('status-dot').className = 'dot dot-pending';
  } else {
    orb.classList.remove('state-thinking');
    orb.classList.add('state-speaking');
    removeThinkingIndicator();
    setTimeout(() => {
      orb.classList.remove('state-speaking');
      document.getElementById('status-text').textContent = S.listening ? 'EN ÉCOUTE' : 'EN ATTENTE';
      document.getElementById('status-dot').className = S.apiOnline ? 'dot dot-online' : 'dot dot-offline';
    }, 3000);
  }
}

function getModeHtml(mode) {
  const map = {
    web_search: [' RECHERCHE WEB', 'mode-web'],
    deep_think:  [' RÉFLEXION', 'mode-deep'],
    vision:      [' VISION', 'mode-vision'],
    browser:     [' NAVIGATION', 'mode-browser'],
    quick:       [' RAPIDE', 'mode-quick'],
  };
  if (!map[mode]) return '';
  const [label, cls] = map[mode];
  return `<span class="msg-mode ${cls}">${label}</span>`;
}

function updateModeDisplay(mode) {
  S.currentMode = mode;
  const labels = {
    web_search: ' WEB', deep_think: ' DEEP',
    vision: ' VISION', browser: ' BROWSER', quick: ' QUICK', normal: '—',
  };
  document.getElementById('mode-display').textContent = labels[mode] || '—';
}

function scrollChat() {
  const z = document.getElementById('chat-zone');
  z.scrollTop = z.scrollHeight;
}

function scheduleAutoRemove(el, delay) {
  setTimeout(() => {
    el.style.transition = 'opacity 1.2s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 1200);
  }, delay);
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── ACTIONS ───────────────────────────────
function handleAction(action) {
  if (!action) return;
  const type = action.type || action.action;
  if (type === 'open_url' && action.url) {
    window.open(action.url, '_blank');
    showNetworkMap();
    setTimeout(hideNetworkMap, 7000);
  } else if (type === 'show_map') {
    showNetworkMap();
    setTimeout(hideNetworkMap, 10000);
  } else if (type === 'system') {
    if (action.command === 'camera') toggleCamera();
    if (action.command === 'screen') captureScreen();
  }
}

// ── API HEALTH ────────────────────────────
async function checkApiHealth() {
  const el = document.getElementById('api-status');
  const dot = document.getElementById('status-dot');
  try {
    const r = await fetchWithTimeout('/api/health', {}, 4000);
    const d = await r.json();
    S.apiOnline = true;
    if (el) {
      el.innerHTML = '<span class="dot dot-online"></span>CONNECTÉ';
      el.className = 'hud-val status-ok';
    }
    if (d.model) {
      const name = (d.model || '').toUpperCase().replace('(DÉFAUT)', '').trim().slice(0, 18);
      document.getElementById('model-name').textContent = name;
    }
    if (dot && !S.listening) dot.className = 'dot dot-online';
    document.getElementById('status-text').textContent = 'EN ATTENTE';
    loadProviders();
  } catch {
    S.apiOnline = false;
    if (el) {
      el.innerHTML = '<span class="dot dot-offline"></span>HORS LIGNE';
      el.className = 'hud-val status-err';
    }
    if (dot) dot.className = 'dot dot-offline';
    document.getElementById('status-text').textContent = 'FLASK NON DÉMARRÉ';
  }
}

// ── PROVIDERS ─────────────────────────────
async function loadProviders() {
  try {
    const r = await fetchWithTimeout('/api/providers', {}, 5000);
    const d = await r.json();
    renderProviders(d.providers || [], d.ollama_models || [], d.current);
  } catch {}
}

function renderProviders(providers, ollama, current) {
  const list = document.getElementById('provider-list');
  // Group by category
  const groups = {};
  providers.forEach(p => {
    const cat = p.category || 'Autre';
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(p);
  });
  list.innerHTML = '';
  Object.entries(groups).forEach(([cat, items]) => {
    const title = document.createElement('div');
    title.className = 'provider-section-title';
    title.textContent = cat;
    list.appendChild(title);
    items.forEach(p => {
      const el = document.createElement('div');
      el.className = 'provider-item' +
        (p.id === current ? ' active' : '') +
        (!p.available ? ' unavailable' : '');
      const badge = p.free
        ? '<span class="provider-badge badge-free">GRATUIT</span>'
        : '<span class="provider-badge badge-paid">PAYANT</span>';
      el.innerHTML = `<span>${p.name}</span>${p.available ? badge : '<span style="font-size:8px;color:var(--muted)">CLÉ MANQUANTE</span>'}`;
      if (p.available) {
        el.onclick = () => switchProvider(p.id);
      }
      list.appendChild(el);
    });
  });

  const ollamaList = document.getElementById('ollama-list');
  if (ollama.length === 0) {
    ollamaList.innerHTML = '<span class="provider-none">Ollama non détecté — installer sur ollama.com</span>';
  } else {
    ollamaList.innerHTML = '';
    ollama.forEach(m => {
      const el = document.createElement('div');
      el.className = 'provider-item';
      el.innerHTML = `<span>▸ ${m}</span><span class="provider-badge badge-local">LOCAL</span>`;
      el.onclick = () => {
        fetch('/api/set-provider', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ provider_id: 'ollama-auto' })
        });
        document.getElementById('model-name').textContent = m.toUpperCase().slice(0,16);
        toggleProviderSelector();
      };
      ollamaList.appendChild(el);
    });
  }
}

async function switchProvider(id) {
  try {
    const r = await fetch('/api/set-provider', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider_id: id })
    });
    const d = await r.json();
    document.getElementById('model-name').textContent = (d.provider || '').toUpperCase().slice(0,18);
    addSystemMsg(`✓ Modèle : ${d.provider}`);
    toggleProviderSelector();
    loadProviders();
  } catch {}
}

function toggleProviderSelector() {
  const sel = document.getElementById('provider-selector');
  const isOpen = sel.style.display === 'block';
  sel.style.display = isOpen ? 'none' : 'block';
  if (!isOpen) loadProviders();
}

// ── CAMERA ────────────────────────────────
async function toggleCamera() {
  const feed = document.getElementById('camera-feed');
  const video = document.getElementById('camera-video');
  const status = document.getElementById('cam-status');
  if (!S.cameraActive) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      video.srcObject = stream;
      feed.style.opacity = '1';
      S.cameraActive = true;
      status.textContent = 'ACTIF';
      status.style.color = 'var(--green)';
    } catch {
      addSystemMsg(' Accès caméra refusé — vérifie les permissions Windows');
    }
  } else {
    video.srcObject?.getTracks().forEach(t => t.stop());
    video.srcObject = null;
    feed.style.opacity = '0';
    S.cameraActive = false;
    status.textContent = 'OFF';
    status.style.color = '';
  }
}

// ── SCREEN CAPTURE ───────────────────────
async function captureScreen() {
  try {
    const stream = await navigator.mediaDevices.getDisplayMedia({
      video: { cursor: 'always' }, audio: false
    });
    const video = document.createElement('video');
    video.srcObject = stream;
    await video.play();
    const c = document.createElement('canvas');
    c.width = video.videoWidth; c.height = video.videoHeight;
    c.getContext('2d').drawImage(video, 0, 0);
    stream.getTracks().forEach(t => t.stop());
    const b64 = c.toDataURL('image/jpeg', 0.7).split(',')[1];
    const r = await fetch('/api/vision', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: "Décris précisément cet écran", frame_b64: b64 })
    });
    const d = await r.json();
    addJarvisMsg(d.reply || 'Analyse impossible.', 'vision');
  } catch (e) {
    addSystemMsg(' Capture écran annulée');
  }
}

// ── TOOLS PANEL ───────────────────────────
const TOOLS = [
  { icon: '', label: 'Recherche web',    cmd: 'JARVIS, cherche ' },
  { icon: '', label: 'Météo',            cmd: 'JARVIS, quel temps à Paris ?' },
  { icon: '', label: 'Infos système',    cmd: 'JARVIS, montre les infos système' },
  { icon: '', label: 'Vitesse internet', cmd: 'JARVIS, teste ma connexion' },
  { icon: '', label: 'Screenshot',       cmd: 'JARVIS, prends un screenshot' },
  { icon: '', label: 'Calculer',         cmd: 'JARVIS, calcule ' },
  { icon: '',  label: 'YouTube',          cmd: 'JARVIS, cherche sur YouTube ' },
  { icon: '', label: 'Wikipedia',        cmd: 'JARVIS, infos Wikipedia sur ' },
  { icon: '', label: 'Rappel',           cmd: 'JARVIS, rappelle-moi dans 5 min de ' },
  { icon: '', label: 'Voir caméra',      cmd: null, fn: () => { toggleToolsPanel(); sendToJarvis("JARVIS, qu'est-ce que tu vois ?"); } },
  { icon: '', label: 'Carte monde',     cmd: null, fn: () => { toggleToolsPanel(); showNetworkMap(); setTimeout(hideNetworkMap, 8000); } },
  { icon: '', label: 'Téléphone',        cmd: 'JARVIS, montre mon téléphone Android' },
];

function initTools() {
  const grid = document.getElementById('tools-grid');
  TOOLS.forEach(t => {
    const btn = document.createElement('button');
    btn.className = 'tool-btn';
    btn.innerHTML = `<span class="tool-icon">${t.icon}</span>${t.label}`;
    btn.onclick = () => {
      if (t.fn) { t.fn(); return; }
      if (t.cmd) {
        const input = document.getElementById('text-input');
        if (t.cmd.endsWith(' ')) {
          input.value = t.cmd;
          input.focus();
        } else {
          sendToJarvis(t.cmd);
        }
        toggleToolsPanel();
      }
    };
    grid.appendChild(btn);
  });
}

function toggleToolsPanel() {
  const p = document.getElementById('tools-panel');
  p.style.display = p.style.display === 'block' ? 'none' : 'block';
}

// ── KEYBOARD ──────────────────────────────
function initKeyboard() {
  window.addEventListener('keydown', (e) => {
    // Ne pas déclencher si on tape dans l'input
    if (document.activeElement === document.getElementById('text-input')) {
      if (e.key === 'Enter') handleInputSend();
      return;
    }
    switch (e.code) {
      case 'Space':
        e.preventDefault();
        toggleListening();
        break;
      case 'KeyC':
        toggleCamera();
        break;
      case 'KeyN':
        if (S.networkActive) hideNetworkMap(); else showNetworkMap();
        break;
      case 'Escape':
        fetch('/api/stop-tts', { method: 'POST' }).catch(() => {});
        stopListening();
        break;
      case 'ArrowUp':
        e.preventDefault();
        if (S.lastMessages.length > 0) {
          const input = document.getElementById('text-input');
          input.value = S.lastMessages[S.lastMessages.length - 1];
          input.focus();
        }
        break;
    }
  });

  // Input hover
  const row = document.getElementById('input-row');
  document.addEventListener('mousemove', (e) => {
    const bottom = window.innerHeight - 90;
    const inZone = e.clientY > bottom;
    row.style.opacity = inZone ? '1' : '0';
  });
}

function handleInputSend() {
  const input = document.getElementById('text-input');
  const val = input.value.trim();
  if (val) {
    input.value = '';
    sendToJarvis(val);
  }
}

// Exposition globale pour les boutons HTML onclick
window.toggleProviderSelector = toggleProviderSelector;
window.toggleToolsPanel = toggleToolsPanel;
window.toggleCamera = toggleCamera;
window.handleInputSend = handleInputSend;
window.sendToJarvis = sendToJarvis;
