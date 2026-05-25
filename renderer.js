/* ═══════════════════════════════════════════
   JARVIS DESKTOP v4 — renderer.js
   Architecture : Module Pattern + Event-driven HUD
   ═══════════════════════════════════════════ */

// ── ÉTAT CENTRALISÉ DE L'HUD ─────────────────────────────────
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
  browserVisible: false,
  voiceSynthesisActive: true,
  availableVoices: [],
  selectedVoice: null,
};

// ── SÉQUENCE D'ARMEMENT INITIAL (BOOT SEQUENCE) ─────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  bootSequence();
});

async function bootSequence() {
  const fill = document.getElementById('boot-fill');
  const screen = document.getElementById('boot-screen');

  // Animation de la jauge de chargement militaire
  let pct = 0;
  const interval = setInterval(() => {
    pct = Math.min(pct + Math.random() * 10 + 2, 95);
    if (fill) fill.style.width = pct + '%';
  }, 60);

  // Armement séquentiel
  initClock();
  initWaveform();
  initNetworkMap();
  initSpeechRecognition();
  initVoiceSynthesis();
  initKeyboard();
  initTools();
  await checkApiHealth();

  // Animation : déplacement de l'orbe central
  setTimeout(() => {
    const orb = document.getElementById('jarvis-orb');
    if (orb) orb.classList.remove('mode-center');
    addSystemLog('sys', 'Déplacement de l\'orbe vers sa coordonnée d\'ancrage');
  }, 1600);

  // Fin de la séquence de boot
  setTimeout(() => {
    clearInterval(interval);
    if (fill) fill.style.width = '100%';
    setTimeout(() => {
      screen.classList.add('hidden');
      addSystemLog('sys', 'HUD système entièrement armé');
      addSystemLog('int', 'Sandboxing d\'Open Interpreter prêt');
      
      // Rendre l'espace libre au démarrage
      hideTelemetryPanel();
      hideWorkspacePanel();
      
      setTimeout(() => screen.remove(), 900);
    }, 250);
  }, 2000);

  // Diagnostic périodique de connectivité
  setInterval(checkApiHealth, 10000);
}

// ── LOGGER D'ACTIVITÉ COGNITIVE (LEFT PANEL FEED) ───────────────────────
function addSystemLog(tag, msg) {
  const container = document.getElementById('hud-system-logs');
  if (!container) return;
  
  const timeStr = new Date().toLocaleTimeString('fr-FR', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  });
  
  const div = document.createElement('div');
  div.className = 'log-line';
  
  let tagClass = 'tag-sys';
  const normTag = tag.toLowerCase();
  
  if (normTag === 'vad' || normTag === 'mic') tagClass = 'tag-vad';
  if (normTag === 'exec' || normTag === 'int') tagClass = 'tag-int';

  div.innerHTML = `<span class="log-ts">[${timeStr}]</span> <span class="${tagClass}">${tag.toUpperCase()}</span> ${msg}`;
  
  // Insertion au début pour un défilement descendant naturel
  container.insertBefore(div, container.firstChild);
  
  // Pruning de débordement mémoire (max 20 lignes)
  while (container.children.length > 20) {
    container.lastChild.remove();
  }
}

// ── HORLOGE TACTIQUE ──
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

// ── ANALYSEUR ET SPECTROGRAMME WAVEFORM (AUDIO VISUALIZER) ──
function initWaveform() {
  const canvas = document.getElementById('waveform-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  canvas.width = 320;
  canvas.height = 48;
  let analyser = null;
  let idle = 0;

  navigator.mediaDevices.getUserMedia({ audio: true, video: false })
    .then(stream => {
      const ac = new AudioContext();
      const src = ac.createMediaStreamSource(stream);
      analyser = ac.createAnalyser();
      analyser.fftSize = 64; // Tailles compactes pour le design épuré
      src.connect(analyser);
      addSystemLog('vad', 'Harnachement audio périphérique OK');
    })
    .catch(() => {
      addSystemLog('vad', 'Impossible d\'accrocher le microphone en direct');
    });

  function draw() {
    requestAnimationFrame(draw);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const bars = 36;
    const bw = canvas.width / bars - 2;
    const cy = canvas.height / 2;

    for (let i = 0; i < bars; i++) {
      let amp;
      if (analyser && S.listening) {
        const d = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(d);
        amp = d[i % analyser.frequencyBinCount] / 255;
      } else {
        // Oscillation sinusoïdale passive en veille
        amp = (Math.sin(idle + i * 0.22) * 0.5 + 0.5) * 0.14 + 0.02;
      }
      const h = Math.max(3, amp * canvas.height * 0.82);
      const alpha = 0.3 + amp * 0.7;
      
      // Palette du bleu électrique au vert néon selon amplitude
      ctx.fillStyle = `rgba(${Math.floor(amp * 100)}, ${200 + Math.floor(amp * 55)}, 255, ${alpha})`;
      ctx.fillRect(i * (bw + 2), cy - h / 2, bw, h);
    }
    idle += 0.04;
  }
  draw();
}

// ── INTERPOLATION MAP SENSOR ART (COMPASS NETWORK) ───────────────────────────
let networkMap = null;

function initNetworkMap() {
  const canvas = document.getElementById('network-canvas');
  if (!canvas) return;
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    if (networkMap) { 
      networkMap.nodes = []; 
      networkMap.connections = [];
      networkMap.generateNodes(80); 
      networkMap.generateConnections(); 
    }
  });
  networkMap = new NetworkMap(canvas);
}

function showNetworkMap() {
  if (!networkMap) return;
  document.getElementById('network-canvas').style.opacity = '0.55';
  networkMap.start();
  S.networkActive = true;
  addSystemLog('sys', 'Projection HOLO_GRID de la topologie réseau');
}

function hideNetworkMap() {
  document.getElementById('network-canvas').style.opacity = '0';
  if (networkMap) networkMap.stop();
  S.networkActive = false;
  addSystemLog('sys', 'Désactivation de la projection HOLO_GRID');
}

class NetworkMap {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.nodes = [];
    this.connections = [];
    this.raf = null;
    this.lastT = 0;
    this.generateNodes(55);
    this.generateConnections();
  }
  generateNodes(n) {
    for (let i = 0; i < n; i++) {
      this.nodes.push({
        x: Math.random() * this.canvas.width,
        y: Math.random() * this.canvas.height,
        r: Math.random() * 2 + 0.5,
        phase: Math.random() * Math.PI * 2,
        hub: Math.random() < 0.08,
      });
    }
  }
  generateConnections() {
    this.nodes.forEach((n, i) => {
      this.nodes.map((o, j) => ({ j, d: Math.hypot(o.x - n.x, o.y - n.y) }))
        .filter(x => x.j !== i && x.d < 180).sort((a, b) => a.d - b.d).slice(0, 3)
        .forEach(x => {
          if (!this.connections.find(c =>
            (c.a === i && c.b === x.j) || (c.a === x.j && c.b === i)))
            this.connections.push({ a: i, b: x.j, op: Math.random() * 0.22 + 0.03 });
        });
    });
  }
  draw(ts) {
    this.raf = requestAnimationFrame(t => this.draw(t));
    if (ts - this.lastT < 30) return;
    this.lastT = ts;
    const { ctx, canvas, nodes, connections } = this;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    connections.forEach(c => {
      const a = nodes[c.a], b = nodes[c.b];
      const g = ctx.createLinearGradient(a.x, a.y, b.x, b.y);
      g.addColorStop(0, `rgba(0,100,150,${c.op})`);
      g.addColorStop(0.5, `rgba(0,243,255,${c.op*1.5})`);
      g.addColorStop(1, `rgba(0,100,150,${c.op})`);
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
      ctx.strokeStyle = g; ctx.lineWidth = 0.5; ctx.stroke();
    });
    nodes.forEach(n => {
      const p = Math.sin(ts * 0.0015 + n.phase) * 0.5 + 0.5;
      const r = n.hub ? n.r * 2.5 : n.r;
      const alpha = n.hub ? 0.6 + p * 0.4 : 0.2 + p * 0.3;
      const col = n.hub ? `rgba(0,250,154,${alpha})` : `rgba(0,243,255,${alpha})`;
      if (n.hub) {
        ctx.beginPath(); ctx.arc(n.x, n.y, r * 4, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0,250,154,${0.02 * p})`; ctx.fill();
      }
      ctx.beginPath(); ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
      ctx.fillStyle = col; ctx.fill();
    });
  }
  start() { requestAnimationFrame(t => this.draw(t)); }
  stop()  { cancelAnimationFrame(this.raf); }
}

// ── CAPTEUR DE RECONNAISSANCE VOCALE (SPEECH DECK) ───────────────────
function initSpeechRecognition() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    console.warn('[JARVIS] Web Speech API indisponible sur ce navigateur d\'exécution');
    addSystemLog('vad', 'Reconnaissance vocale API Web introuvable');
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
    if (['no-speech', 'audio-capture'].includes(e.error)) return;
    if (e.error === 'not-allowed') {
      addSystemMsg('Autorisation micro défaillante. Modifiez vos options de confidentialité.');
      addSystemLog('vad', 'Erreur d\'autorisation d\'accès micro');
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
    el.style.textShadow = '0 0 8px rgba(0,250,154,0.6)';
    document.getElementById('jarvis-orb').className = 'state-listening';
    if (dot) dot.className = 'dot dot-online';
    document.getElementById('status-text').textContent = 'AUDIO CAPTURE ACTIVE';
    addSystemLog('mic', 'Microphone ouvert; détection VAD engagée');
  } else {
    el.textContent = 'VEILLE';
    el.style.color = '';
    el.style.textShadow = '';
    document.getElementById('jarvis-orb').className = '';
    if (dot) dot.className = S.apiOnline ? 'dot dot-online' : 'dot dot-offline';
    document.getElementById('status-text').textContent = 'EN ATTENTE DE COMMANDE';
    addSystemLog('mic', 'Microphone fermé; mise en veille passive');
  }
}

// ── EXPEDITION DES COMMANDES VERS LE CERVEAU NATIVE (FLASK) ────────────────────────
async function sendToJarvis(message) {
  if (!message.trim()) return;
  S.lastMessages.push(message);
  if (S.lastMessages.length > 20) S.lastMessages.shift();

  addUserMsg(message);
  setThinkingState(true);
  S.latencyStart = Date.now();
  
  addSystemLog('sys', `Directive : "${message.length > 28 ? message.slice(0, 25) + '...' : message}"`);

  try {
    const res = await fetchWithTimeout('/api/tool-chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    }, 25000);

    const data = await res.json();
    const latency = Date.now() - S.latencyStart;
    document.getElementById('latency-display').textContent = latency + 'ms';

    setThinkingState(false);
    
    // Dispatch de réponse
    addJarvisMsg(data.reply || 'Execution complétée sans retour écrit.', data.mode_used || 'normal');
    addSystemLog('int', 'Calcul résolu par Open Interpreter');

    if (data.action) handleAction(data.action);
    if (data.mode_used) updateModeDisplay(data.mode_used);

  } catch (err) {
    setThinkingState(false);
    addJarvisMsg('Moteur d\'action injoignable. Démarre server.py via start_jarvis.', 'error');
    addSystemLog('exec', 'Erreur critique de routage vers le noyau Flask local');
    checkApiHealth();
  }
}

function fetchWithTimeout(url, opts, timeout) {
  return Promise.race([
    fetch(url, opts),
    new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), timeout))
  ]);
}

// ── RENDU GRAPHIQUE DES BULLES DE DISCUSSION ─────────────────────────────
function addUserMsg(text) {
  const zone = document.getElementById('chat-zone');
  const div = document.createElement('div');
  div.className = 'msg msg-user';
  div.innerHTML = `<div class="msg-label">VOUS</div><div class="msg-bubble">${escHtml(text)}</div>`;
  zone.appendChild(div);
  scrollChat();
  scheduleAutoRemove(div, 90000);
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

  // === VISUALIZATION DU CODE SOURCE DANS LE CONSOLE DROIT ===
  // Extraction regex des blocs de codes markdown générés par Open Interpreter
  const codeRegex = /```(\w*)\n([\s\S]*?)```/g;
  let match;
  let codeStr = '';
  let cleanedText = text;
  
  while ((match = codeRegex.exec(text)) !== null) {
    const lang = match[1] || 'python';
    const code = match[2];
    codeStr += `\n# --- AUTOMATED ${lang.toUpperCase()} EXECUTION ---\n${code}\n`;
  }

  // Si on décrypte du code sandbox en cours d'analyse
  const termBody = document.getElementById('code-terminal-body');
  if (termBody && codeStr) {
    // Déployer automatiquement le panneau de travail si du code est exécuté ou écrit par JARVIS
    showWorkspacePanel();
    
    termBody.innerHTML = '';
    
    // Coloration syntaxique de base par Regex
    let highlighted = codeStr
      .replace(/(#[^\n]*)/g, '<span class="term-comment">$1</span>')
      .replace(/\b(def|import|from|print|if|elif|else|return|for|while|try|except|as|with|class|in|not|and|or)\b/g, '<span class="term-keyword">$1</span>')
      .replace(/("[^"]*"|'[^']*')/g, '<span class="term-string">$1</span>');
      
    termBody.innerHTML = highlighted;
    termBody.scrollTop = termBody.scrollHeight;
    
    // Flash de l'indicateur d'état du terminal sandbox en orange
    const pin = document.querySelector('.term-pin');
    if (pin) {
      pin.className = 'term-pin processing';
      setTimeout(() => { pin.className = 'term-pin'; }, 5000);
    }
    
    addSystemLog('exec', 'Extraction de code : Script détecté et déporté au terminal');
    
    // Nettoyer l'affichage du chat principal pour éviter de dupliquer de longs codes illisibles
    cleanedText = text.split("```")[0].trim();
    if (!cleanedText) {
      cleanedText = "J'ai structuré et exécuté un script sur votre invite. En voici l'aperçu dynamique à l'écran de droite.";
    } else {
      cleanedText += "\n\n*(Script reporté sur le moniteur de droite)*";
    }
  }

  // Vocalisation du texte nettoyé en synthèse de parole client-side
  speakText(cleanedText);

  // Effet d'écriture machine pour une fluidité d'IA
  let i = 0;
  const clean = cleanedText.replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const tid = setInterval(() => {
    bubble.innerHTML = clean.slice(0, ++i);
    scrollChat();
    if (i >= clean.length) {
      bubble.classList.remove('typing-cursor');
      clearInterval(tid);
    }
  }, 10);

  scheduleAutoRemove(div, 120000);
}

function addSystemMsg(text) {
  const zone = document.getElementById('chat-zone');
  const div = document.createElement('div');
  div.className = 'msg-system';
  div.textContent = text;
  zone.appendChild(div);
  scrollChat();
  setTimeout(() => { 
    div.style.opacity = '0'; 
    div.style.transition = 'opacity 1s'; 
    setTimeout(() => div.remove(), 1000); 
  }, 10000);
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
  if (!orb) return;
  if (on) {
    orb.className = 'state-thinking';
    addThinkingIndicator();
    document.getElementById('status-text').textContent = 'ANALYSE DU PROMPT EN COURS...';
    document.getElementById('status-dot').className = 'dot dot-pending';
  } else {
    orb.className = 'state-speaking';
    removeThinkingIndicator();
    setTimeout(() => {
      orb.className = '';
      document.getElementById('status-text').textContent = S.listening ? 'AUDIO CAPTURE ACTIVE' : 'EN ATTENTE DE DIRECTIVES';
      document.getElementById('status-dot').className = S.apiOnline ? 'dot dot-online' : 'dot dot-offline';
    }, 2800);
  }
}

function getModeHtml(mode) {
  const map = {
    web_search: ['⌕ RECHERCHE WEB', 'mode-web'],
    deep_think:  ['⬡ DEEP THINK', 'mode-deep'],
    vision:      ['◎ TACTICAL VISION', 'mode-vision'],
    browser:     ['⊞ NATIVE RUNNER', 'mode-browser'],
    quick:       ['⇋ FILTRAGE IMMÉDIAT', 'mode-quick'],
  };
  if (!map[mode]) return '';
  const [label, cls] = map[mode];
  return `<span class="msg-mode ${cls}">${label}</span>`;
}

function updateModeDisplay(mode) {
  S.currentMode = mode;
  const labels = {
    web_search: '⌕ OSINT', deep_think: '⬡ COGNITIVE',
    vision: '◎ SENSOR', browser: '⊞ SHELL', quick: '⇋ BYPASS', normal: '—',
  };
  const disp = document.getElementById('mode-display');
  if (disp) disp.textContent = labels[mode] || '—';
}

function scrollChat() {
  const z = document.getElementById('chat-zone');
  if (z) z.scrollTop = z.scrollHeight;
}

function scheduleAutoRemove(el, delay) {
  setTimeout(() => {
    el.style.transition = 'opacity 1.5s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 1500);
  }, delay);
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── DISPATCHER D'ACTIONS MACHINE (FRONTEND/HOST ACTION TRACERS) ───────────────────────────
function handleAction(action) {
  if (!action) return;
  const type = action.type || action.action;
  addSystemLog('exec', `Action demandée par le noyau : "${type}"`);
  
  if (type === 'open_url' && action.url) {
    window.open(action.url, '_blank');
    showNetworkMap();
    setTimeout(hideNetworkMap, 6000);
  } else if (type === 'show_map') {
    showNetworkMap();
    setTimeout(hideNetworkMap, 10000);
  } else if (type === 'system') {
    if (action.command === 'camera') toggleCamera();
    if (action.command === 'screen') captureScreen();
  }
}

// ── DIAGNOSTIC ET ETAT TECHNIQUE DE L'API NOYAU ────────────────────────────
async function checkApiHealth() {
  const el = document.getElementById('api-status');
  const dot = document.getElementById('status-dot');
  try {
    const r = await fetchWithTimeout('/api/health', {}, 4000);
    const d = await r.json();
    
    if (!S.apiOnline) {
      addSystemLog('sys', 'Connexion établie avec le serveur d\'orchestration');
    }
    
    S.apiOnline = true;
    if (el) {
      el.innerHTML = '<span class="dot dot-online"></span>SUPPORT SÉCURISÉ';
      el.className = 'hud-val status-ok';
    }
    
    if (d.provider) {
      const name = d.provider.toUpperCase();
      document.getElementById('model-name').textContent = name;
    }
    if (dot && !S.listening) dot.className = 'dot dot-online';
    document.getElementById('status-text').textContent = 'RESTAURATION COMPLÈTE NOMINALE';
    loadProviders();
  } catch {
    if (S.apiOnline || S.apiOnline === false) {
      addSystemLog('sys', 'Erreur de connexion : Serveur d\'orchestration Flask injouable');
    }
    S.apiOnline = false;
    if (el) {
      el.innerHTML = '<span class="dot dot-offline"></span>HORS-LIGNE CORE';
      el.className = 'hud-val status-err';
    }
    if (dot) dot.className = 'dot dot-offline';
    document.getElementById('status-text').textContent = 'SERVEUR FLASK OFF';
  }
}

// ── DISPATCHS DES SERVICES D'IA COMPUTE ─────────────────────────────
async function loadProviders() {
  try {
    const r = await fetchWithTimeout('/api/providers', {}, 5000);
    const d = await r.json();
    renderProviders(d.providers || [], d.ollama_models || [], d.current);
  } catch {}
}

function renderProviders(providers, ollama, current) {
  const list = document.getElementById('provider-list');
  if (!list) return;
  
  const groups = {};
  providers.forEach(p => {
    const cat = p.category || 'Orchestration';
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
        ? '<span class="provider-badge badge-free">LIBRE</span>'
        : '<span class="provider-badge badge-paid">CLE SECURES</span>';
      el.innerHTML = `<span>${p.name}</span>${p.available ? badge : '<span style="font-size:8px;color:rgba(255,100,100,0.6)">CLÉ ABSENTE</span>'}`;
      if (p.available) {
        el.onclick = () => switchProvider(p.id);
      }
      list.appendChild(el);
    });
  });

  const ollamaList = document.getElementById('ollama-list');
  if (ollamaList) {
    if (ollama.length === 0) {
      ollamaList.innerHTML = '<span class="provider-none">Moteurs d\'exécutions natifs auto-détectés</span>';
    } else {
      ollamaList.innerHTML = '';
      ollama.forEach(m => {
        const el = document.createElement('div');
        el.className = 'provider-item';
        el.innerHTML = `<span>▸ ${m}</span><span class="provider-badge badge-local">NATIVE</span>`;
        el.onclick = () => {
          fetch('/api/set-provider', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider_id: 'local' })
          });
          document.getElementById('model-name').textContent = m.toUpperCase().slice(0,16);
          toggleProviderSelector();
        };
        ollamaList.appendChild(el);
      });
    }
  }
}

async function switchProvider(id) {
  try {
    const r = await fetch('/api/set-provider', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider_id: id })
    });
    const d = await r.json();
    document.getElementById('model-name').textContent = (id === 'gemini' ? 'GEMINI 2.5' : 'LOCAL SHELL');
    addSystemMsg(`✓ Nouveau mode de calcul assigné : ${id === 'gemini' ? 'Gemini 2.5 CLoud' : 'Local Interpreter Core'}`);
    addSystemLog('sys', `Mutation calcul : Modèle configuré vers [${id.toUpperCase()}]`);
    toggleProviderSelector();
    loadProviders();
  } catch {}
}

function toggleProviderSelector() {
  const sel = document.getElementById('provider-selector');
  if (!sel) return;
  const isOpen = sel.style.display === 'block';
  sel.style.display = isOpen ? 'none' : 'block';
  if (!isOpen) loadProviders();
}

// ── ENREGISTREMENT ET FLUX DES CAPTEURS OPTIQUES (WEBCAM) ────────────────────────────────
async function toggleCamera() {
  const feed = document.getElementById('camera-feed');
  const video = document.getElementById('camera-video');
  const status = document.getElementById('cam-status');
  
  if (!S.cameraActive) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (video) video.srcObject = stream;
      if (feed) feed.style.opacity = '1';
      S.cameraActive = true;
      if (status) {
        status.textContent = 'ACTIF';
        status.style.color = 'var(--green)';
        status.style.textShadow = '0 0 8px var(--green-glow)';
      }
      
      // Déployer automatiquement le panneau de droite pour voir la caméra
      showWorkspacePanel();
      
      addSystemLog('sys', 'Flux caméra démarré : Capteur d\'analyse physique actif');
    } catch {
      addSystemMsg('Permission optique refusée. Autorisez la caméra dans vos capteurs système.');
      addSystemLog('sys', 'Erreur d\'ouverture du capteur caméra');
    }
  } else {
    if (video && video.srcObject) {
      video.srcObject.getTracks().forEach(t => t.stop());
      video.srcObject = null;
    }
    if (feed) feed.style.opacity = '0';
    S.cameraActive = false;
    if (status) {
      status.textContent = 'OFF';
      status.style.color = '';
      status.style.textShadow = '';
    }
    
    // Fermer le panneau de droite si la caméra est désactivée
    hideWorkspacePanel();
    
    addSystemLog('sys', 'Caméra coupée par l\'opérateur');
  }
}

// ── CAPTURE D'ÉCRANS ANALYSE OPTIQUE ───────────────────────
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
    
    addSystemLog('sys', 'Aperçu d\'écran capturé; transfert au moteur vision...');

    const r = await fetch('/api/vision', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: "Décris précisément cet écran", frame_b64: b64 })
    });
    const d = await r.json();
    addJarvisMsg(d.reply || 'Analyse optique indéchiffrable.', 'vision');
  } catch (e) {
    addSystemMsg('Capture de flux vidéo annulée');
    addSystemLog('sys', 'Opération de capture d\'écran déclinée');
  }
}

// ── RACCOURCIS ET OUTILS TACTIQUES PREDEFINIS ───────────────────────────
const TOOLS = [
  { icon: '⌕', label: 'Recherche OSINT',    cmd: 'JARVIS, cherche sur internet ' },
  { icon: '☼', label: 'Méteo En Direct',   cmd: 'JARVIS, quel temps fait-il actuellement ?' },
  { icon: '⏣', label: 'Ressources System',  cmd: 'JARVIS, montre les statistiques système' },
  { icon: '⇋', label: 'Test Connexion',    cmd: 'JARVIS, fais un test de débit internet' },
  { icon: '⛶', label: 'Screenshot Capt',    cmd: 'JARVIS, prends un screenshot' },
  { icon: '∑', label: 'Calculatrice',       cmd: 'JARVIS, calcule ' },
  { icon: '▶', label: 'Oubli YouTube',      cmd: 'JARVIS, cherche sur YouTube ' },
  { icon: 'W', label: 'Recherche Wiki',     cmd: 'JARVIS, cherche des infos wikipedia sur ' },
  { icon: '⧖', label: 'Alarme / Rappel',    cmd: 'JARVIS, rappelle-moi dans 5 minutes de ' },
  { icon: '◎', label: 'Activer Optique',    cmd: null, fn: () => { toggleToolsPanel(); sendToJarvis("JARVIS, qu'est-ce que tu vois ?"); } },
  { icon: '▧', label: 'Scanner Cartes',     cmd: null, fn: () => { toggleToolsPanel(); showNetworkMap(); setTimeout(hideNetworkMap, 8000); } },
  { icon: '⌗', label: 'Statut Reseaux',    cmd: 'JARVIS, montre les infos de connexion locale' },
];

function initTools() {
  const grid = document.getElementById('tools-grid');
  if (!grid) return;
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
  if (p) p.style.display = p.style.display === 'block' ? 'none' : 'block';
}

// ── CLAVIER ET RACCOURCIS RACCORDS DU HUD ──────────────────────────────
function initKeyboard() {
  window.addEventListener('keydown', (e) => {
    // Ne pas court-circuiter l'écriture de l'utilisateur
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
      case 'KeyT':
        toggleTelemetryPanel();
	break;
      case 'KeyW':
        toggleWorkspacePanel();
	break;
      case 'KeyN':
        if (S.networkActive) hideNetworkMap(); else showNetworkMap();
        break;
      case 'Escape':
        fetch('/api/stop-tts', { method: 'POST' }).catch(() => {});
        stopListening();
        addSystemLog('sys', 'Coupure d\'urgence des sorties audio vocalisées');
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

  // Masquage intelligent de la barre de saisie pour epurer l'orbe central
  const row = document.getElementById('input-row');
  if (row) {
    document.addEventListener('mousemove', (e) => {
      const bottomLimit = window.innerHeight - 100;
      const hoverInputArea = e.clientY > bottomLimit;
      row.style.opacity = hoverInputArea ? '1' : '0.85';
    });
  }
}

function handleInputSend() {
  const input = document.getElementById('text-input');
  if (!input) return;
  const val = input.value.trim();
  if (val) {
    input.value = '';
    sendToJarvis(val);
  }
}

// ── EXPANSION DE COUPLAGE DU NAVIGATEUR EN DIRECT ──
async function toggleBrowserView() {
  S.browserVisible = !S.browserVisible;
  const btn = document.getElementById('browser-toggle');
  
  try {
    const r = await fetch('/api/browser/toggle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ visible: S.browserVisible })
    });
    const data = await r.json();
    if (data.success) {
      if (!data.headless) {
        if (btn) {
          btn.innerHTML = 'HIDE CHROME';
          btn.style.color = 'var(--amber)';
          btn.style.borderColor = 'rgba(255,175,0,0.5)';
        }
        addSystemLog('exec', 'Lancement navigateur Chrome en mode visible sur l\'écran');
      } else {
        if (btn) {
          btn.innerHTML = 'VIEW CHROME';
          btn.style.color = 'var(--cyan)';
          btn.style.borderColor = 'var(--cyan-border)';
        }
        addSystemLog('exec', 'Rétraction de Chrome en mode arrière-plan invisible');
      }
      addSystemMsg(`✓ Navigateur d'automatisation ${data.headless ? 'masqué' : 'affiché'}`);
    }
  } catch (err) {
    addSystemMsg('Échec de communication de l\'action bascule navigateur');
  }
}

// ── CONTRÔLE DES PANNEAUX LATÉRAUX DYNAMIQUES (DECLUTTER INTERFACES) ──
function showTelemetryPanel() {
  const panel = document.querySelector('.hud-left-panel');
  const btn = document.getElementById('btn-toggle-telemetry');
  if (panel) {
    panel.classList.remove('collapsed');
    if (btn) {
      btn.innerHTML = '[ TELEMETRY: ACTIVE ]';
      btn.className = 'top-bar-btn glow-green';
      btn.style.opacity = '1';
    }
    addSystemLog('sys', 'Déploiement du panneau de télémétrie système');
  }
}

function hideTelemetryPanel() {
  const panel = document.querySelector('.hud-left-panel');
  const btn = document.getElementById('btn-toggle-telemetry');
  if (panel) {
    panel.classList.add('collapsed');
    if (btn) {
      btn.innerHTML = '[ TELEMETRY: DORMANT ]';
      btn.className = 'top-bar-btn glow-cyan';
      btn.style.opacity = '0.45';
    }
    addSystemLog('sys', 'Rétraction du panneau de télémétrie');
  }
}

function toggleTelemetryPanel() {
  const panel = document.querySelector('.hud-left-panel');
  if (panel) {
    if (panel.classList.contains('collapsed')) {
      showTelemetryPanel();
    } else {
      hideTelemetryPanel();
    }
  }
}

function showWorkspacePanel() {
  const panel = document.querySelector('.hud-right-panel');
  const btn = document.getElementById('btn-toggle-workspace');
  if (panel) {
    panel.classList.remove('collapsed');
    if (btn) {
      btn.innerHTML = '[ WORKSPACE: ACTIVE ]';
      btn.className = 'top-bar-btn glow-green';
      btn.style.opacity = '1';
    }
    addSystemLog('sys', 'Déploiement du panneau de calcul workspace');
  }
}

function hideWorkspacePanel() {
  const panel = document.querySelector('.hud-right-panel');
  const btn = document.getElementById('btn-toggle-workspace');
  if (panel) {
    panel.classList.add('collapsed');
    if (btn) {
      btn.innerHTML = '[ WORKSPACE: DORMANT ]';
      btn.className = 'top-bar-btn glow-cyan';
      btn.style.opacity = '0.45';
    }
    addSystemLog('sys', 'Rétraction de la console de travail');
  }
}

function toggleWorkspacePanel() {
  const panel = document.querySelector('.hud-right-panel');
  if (panel) {
    if (panel.classList.contains('collapsed')) {
      showWorkspacePanel();
    } else {
      hideWorkspacePanel();
    }
  }
}

// ── INTÉGRATION SYNTHÈSE VOCALE CLIENT-SIDE DE J.A.R.V.I.S ──
function initVoiceSynthesis() {
  if (!('speechSynthesis' in window)) {
    console.warn('[JARVIS] Synthèse vocale indisponible dans cet environnement');
    addSystemLog('sys', 'Synthèse vocale indisponible');
    return;
  }
  
  // Remplir la liste des voix au départ
  populateVoices();
  if (speechSynthesis.onvoiceschanged !== undefined) {
    speechSynthesis.onvoiceschanged = populateVoices;
  }
  
  // Forcer l'interrupteur visuel selon l'état S
  const toggle = document.getElementById('voice-synthesis-toggle');
  if (toggle) toggle.checked = S.voiceSynthesisActive;
}

function populateVoices() {
  if (!('speechSynthesis' in window)) return;
  const list = speechSynthesis.getVoices();
  S.availableVoices = list;
  
  const select = document.getElementById('voice-select');
  if (!select) return;
  
  // Vider le select
  select.innerHTML = '<option value="default">Par défaut (Navigateur)</option>';
  
  // Trier pour mettre le français à l'honneur
  const frVoices = list.filter(v => v.lang.startsWith('fr-') || v.lang === 'fr');
  const otherVoices = list.filter(v => !v.lang.startsWith('fr-') && v.lang !== 'fr');
  
  // Ajouter les voix françaises
  frVoices.forEach((v, index) => {
    const opt = document.createElement('option');
    opt.value = 'fr-' + index;
    opt.textContent = `${v.name} (${v.lang})`;
    select.appendChild(opt);
  });
  
  // Ajouter les autres voix populaires en option
  otherVoices.slice(0, 15).forEach((v, index) => {
    const opt = document.createElement('option');
    opt.value = 'other-' + index;
    opt.textContent = `${v.name} (${v.lang})`;
    select.appendChild(opt);
  });
}

function updateSelectedVoice() {
  const select = document.getElementById('voice-select');
  if (!select || !('speechSynthesis' in window)) return;
  
  const val = select.value;
  if (val === 'default') {
    S.selectedVoice = null;
    addSystemLog('sys', 'Configuration voix : Auto français');
    return;
  }
  
  const parts = val.split('-');
  const category = parts[0];
  const idx = parseInt(parts[1], 10);
  const list = speechSynthesis.getVoices();
  
  if (category === 'fr') {
    const frVoices = list.filter(v => v.lang.startsWith('fr-') || v.lang === 'fr');
    S.selectedVoice = frVoices[idx] || null;
  } else {
    const otherVoices = list.filter(v => !v.lang.startsWith('fr-') && v.lang !== 'fr');
    S.selectedVoice = otherVoices[idx] || null;
  }
  
  if (S.selectedVoice) {
    addSystemLog('sys', `Voix assignée : ${S.selectedVoice.name}`);
  }
}

function toggleVoiceSynthesis() {
  const toggle = document.getElementById('voice-synthesis-toggle');
  if (toggle) {
    S.voiceSynthesisActive = toggle.checked;
    addSystemLog('sys', `Lecture vocale ${S.voiceSynthesisActive ? 'ARMÉE' : 'MUTÉE'}`);
    if (!S.voiceSynthesisActive && speechSynthesis.speaking) {
      speechSynthesis.cancel();
    }
  }
}

function speakText(rawText) {
  if (!S.voiceSynthesisActive || !('speechSynthesis' in window)) return;
  
  // Annuler toute voix en cours d'émission
  speechSynthesis.cancel();
  
  // Nettoyer les balises d'affichage pour une prononciation claire et humaine
  let speechText = rawText
    .replace(/\*+/g, '') // E.g., bold markers
    .replace(/\_\_/g, '') // Underline
    .replace(/#+/g, '') // Headings
    .replace(/```[\s\S]*?```/g, '') // Supprime les blocs de codes entiers
    .replace(/\[\s*WORKSPACE\s*\:\s*ACTIVE\s*\]/g, '') 
    .replace(/\(Script reporté sur le moniteur de droite\)/g, '')
    .substring(0, 300); // Limiter à 300 caractères pour le dynamisme
    
  if (!speechText.trim()) return;
  
  try {
    const utter = new SpeechSynthesisUtterance(speechText);
    
    // Vitesse
    const rateEl = document.getElementById('voice-rate');
    if (rateEl) utter.rate = parseFloat(rateEl.value);
    
    // Pitch
    const pitchEl = document.getElementById('voice-pitch');
    if (pitchEl) utter.pitch = parseFloat(pitchEl.value);
    
    // Voice selection
    if (S.selectedVoice) {
      utter.voice = S.selectedVoice;
    } else {
      // Trouver la première voix FR par défaut si aucune sélectionnée
      const list = speechSynthesis.getVoices();
      const defaultFr = list.find(v => v.lang.startsWith('fr-') || v.lang === 'fr');
      if (defaultFr) utter.voice = defaultFr;
    }
    
    utter.onstart = () => {
      S.speaking = true;
      const orb = document.getElementById('jarvis-orb');
      if (orb && !orb.classList.contains('state-thinking')) {
        orb.className = 'state-speaking';
      }
      addSystemLog('sys', 'Synthèse vocale active');
    };
    
    utter.onend = () => {
      S.speaking = false;
      const orb = document.getElementById('jarvis-orb');
      if (orb && orb.className === 'state-speaking') {
        orb.className = '';
      }
    };
    
    utter.onerror = () => {
      S.speaking = false;
      const orb = document.getElementById('jarvis-orb');
      if (orb && orb.className === 'state-speaking') {
        orb.className = '';
      }
    };
    
    speechSynthesis.speak(utter);
  } catch (err) {
    console.warn('[JARVIS] Échec d\'amorçage de la synthèse vocale client:', err);
  }
}

function testJarvisVoice() {
  const sampleLines = [
    "Système de retour vocal opérationnel. Je suis J.A.R.V.I.S, prêt à exécuter vos directives.",
    "Protocoles audio armés. Diagnostic nominal des hauts-parleurs effectué.",
    "Liaison neuronale établie. Moteurs de calcul prêts au déploiement."
  ];
  const randLine = sampleLines[Math.floor(Math.random() * sampleLines.length)];
  speakText(randLine);
  
  // Simuler visuellement l'affichage dans le chat
  addSystemMsg("✓ Test de retour vocal lancé");
}

function openVoiceSimSelector() {
  const p = document.getElementById('voice-simulator-panel');
  if (p) {
    // Fermer l'autre popover si ouvert
    const sel = document.getElementById('provider-selector');
    if (sel) sel.style.display = 'none';
    
    p.style.display = 'block';
  }
}

function closeVoiceSimSelector() {
  const p = document.getElementById('voice-simulator-panel');
  if (p) p.style.display = 'none';
}

function simulateVoicePhrase(phrase) {
  closeVoiceSimSelector();
  
  // Animation d'écoute
  setMicStatus(true);
  addSystemLog('mic', `Reconnaissance simulée : "${phrase}"`);
  
  // Court temps de capture audio puis envoi
  setTimeout(() => {
    setMicStatus(false);
    sendToJarvis(phrase);
  }, 1200);
}

// EXPOSITIONS NAVIGATEUR AU CLIENT DOM
window.toggleProviderSelector = toggleProviderSelector;
window.toggleToolsPanel = toggleToolsPanel;
window.toggleCamera = toggleCamera;
window.handleInputSend = handleInputSend;
window.sendToJarvis = sendToJarvis;
window.toggleBrowserView = toggleBrowserView;
window.showTelemetryPanel = showTelemetryPanel;
window.hideTelemetryPanel = hideTelemetryPanel;
window.toggleTelemetryPanel = toggleTelemetryPanel;
window.showWorkspacePanel = showWorkspacePanel;
window.hideWorkspacePanel = hideWorkspacePanel;
window.toggleWorkspacePanel = toggleWorkspacePanel;
window.initVoiceSynthesis = initVoiceSynthesis;
window.toggleVoiceSynthesis = toggleVoiceSynthesis;
window.updateSelectedVoice = updateSelectedVoice;
window.testJarvisVoice = testJarvisVoice;
window.openVoiceSimSelector = openVoiceSimSelector;
window.closeVoiceSimSelector = closeVoiceSimSelector;
window.simulateVoicePhrase = simulateVoicePhrase;
