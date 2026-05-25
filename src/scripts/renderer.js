/* ═══════════════════════════════════════════
   JARVIS renderer.js — Design @huwprosser
   Complet, connecté, fonctionnel.
═══════════════════════════════════════════ */
const STATE = {
  listening: false, recLock: false,
  speaking: false, camActive: false, mapActive: false,
  contentOn: false, apiOk: false,
  recognition: null, history: [],
  latency: 0,
};

// ── BOOT ──────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', boot);
async function boot() {
  const fill = document.getElementById('boot-fill');
  const hint = document.getElementById('boot-hint');
  const hints = [
    'Chargement des modules systèmes…',
    'Connexion au moteur Open Interpreter…',
    'Initialisation de la reconnaissance vocale…',
    'Prêt.',
  ];
  let pct = 0, hi = 0;
  const iv = setInterval(() => {
    pct = Math.min(pct + Math.random() * 8 + 4, 95);
    if (fill) fill.style.width = pct + '%';
    if (pct > 25 * (hi + 1) && hi < hints.length - 1) {
      hi++; if (hint) hint.textContent = hints[hi];
    }
  }, 75);
  initClock();
  initWaveform();
  initMap();
  initRecognition();
  initKeys();
  initTools();
  await checkApi();
  clearInterval(iv);
  if (fill) fill.style.width = '100%';
  if (hint) hint.textContent = 'Système actif.';
  setTimeout(() => {
    const s = document.getElementById('boot-screen');
    if (s) s.classList.add('out');
    setTimeout(() => { if (s) s.remove(); }, 950);
  }, 350);
  setInterval(checkApi, 15000);
  setInterval(updateSysCpu, 5000);
}

// ── HORLOGE ───────────────────────────────────────────
function initClock() {
  const tick = () => {
    const n = new Date();
    const full = n.toLocaleTimeString('fr-FR', { hour12: false });
    const short = n.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    const et = document.getElementById('h-time');
    if (et) et.textContent = full;
    const ot = document.getElementById('orb-time');
    if (ot) ot.textContent = full;
    const st = document.getElementById('sb-time');
    if (st) st.textContent = short;
  };
  tick(); setInterval(tick, 1000);
}

// ── MAP RÉSEAU ────────────────────────────────────────
let mapInstance = null;
function initMap() {
  const c = document.getElementById('map-canvas');
  if (!c) return;
  const resize = () => { c.width = innerWidth; c.height = innerHeight; mapInstance?.reset(); };
  resize();
  window.addEventListener('resize', resize);
  mapInstance = new NetworkMap(c);
}
class NetworkMap {
  constructor(c) {
    this.c = c; this.cx = c.getContext('2d');
    this.nodes = []; this.edges = []; this.raf = null;
    this.reset();
  }
  reset() {
    this.nodes = []; this.edges = [];
    for (let i = 0; i < 85; i++) this.nodes.push({
      x: Math.random() * this.c.width,
      y: Math.random() * this.c.height,
      r: Math.random() * 2 + 0.4,
      ph: Math.random() * Math.PI * 2,
      hub: Math.random() < 0.07,
    });
    this.nodes.forEach((a, i) => {
      this.nodes.map((b, j) => ({ j, d: Math.hypot(b.x-a.x, b.y-a.y) }))
        .filter(x => x.j !== i && x.d < 170)
        .sort((a, b) => a.d - b.d).slice(0, 3)
        .forEach(x => {
          if (!this.edges.find(e => (e.a===i&&e.b===x.j)||(e.a===x.j&&e.b===i)))
            this.edges.push({ a: i, b: x.j, op: Math.random() * 0.22 + 0.04 });
        });
    });
  }
  draw(ts) {
    this.raf = requestAnimationFrame(t => this.draw(t));
    const { cx, c, nodes: N, edges: E } = this;
    cx.clearRect(0, 0, c.width, c.height);
    E.forEach(e => {
      const a = N[e.a], b = N[e.b];
      const g = cx.createLinearGradient(a.x, a.y, b.x, b.y);
      g.addColorStop(0,   `rgba(18,65,125,${e.op})`);
      g.addColorStop(0.5, `rgba(38,110,180,${e.op*1.4})`);
      g.addColorStop(1,   `rgba(18,65,125,${e.op})`);
      cx.beginPath(); cx.moveTo(a.x, a.y); cx.lineTo(b.x, b.y);
      cx.strokeStyle = g; cx.lineWidth = 0.45; cx.stroke();
    });
    N.forEach(n => {
      const p = Math.sin(ts * 0.0016 + n.ph) * 0.5 + 0.5;
      const r = n.hub ? n.r * 2.6 : n.r;
      const al = n.hub ? 0.55 + p * 0.4 : 0.22 + p * 0.28;
      const col = n.hub ? `rgba(55,215,130,${al})` : `rgba(58,143,212,${al})`;
      if (n.hub) {
        cx.beginPath(); cx.arc(n.x, n.y, r * 4, 0, Math.PI*2);
        cx.fillStyle = `rgba(38,195,115,${0.022*p})`; cx.fill();
      }
      cx.beginPath(); cx.arc(n.x, n.y, r, 0, Math.PI*2);
      cx.fillStyle = col; cx.fill();
    });
  }
  start() { requestAnimationFrame(t => this.draw(t)); }
  stop()  { cancelAnimationFrame(this.raf); }
}
function showMap() {
  if (!mapInstance) return;
  document.getElementById('map-canvas').style.opacity = '0.58';
  mapInstance.start(); STATE.mapActive = true; setContent(true);
}
function hideMap() {
  const el = document.getElementById('map-canvas');
  if (el) el.style.opacity = '0';
  mapInstance?.stop(); STATE.mapActive = false; checkContent();
}

// ── WAVEFORM ──────────────────────────────────────────
function initWaveform() {
  const c = document.getElementById('wave');
  if (!c) return;
  const cx = c.getContext('2d');
  c.width = 420; c.height = 44;
  let analyser = null, idle = 0;
  navigator.mediaDevices.getUserMedia({ audio: true, video: false })
    .then(st => {
      const ac = new (window.AudioContext || window.webkitAudioContext)();
      const src = ac.createMediaStreamSource(st);
      analyser = ac.createAnalyser(); analyser.fftSize = 128;
      src.connect(analyser);
    }).catch(() => {});
  (function draw() {
    requestAnimationFrame(draw);
    cx.clearRect(0, 0, c.width, c.height);
    const bars = 52, bw = c.width / bars - 1, cy = c.height / 2;
    for (let i = 0; i < bars; i++) {
      let amp;
      if (analyser && STATE.listening) {
        const d = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(d);
        amp = d[i] / 255;
      } else {
        amp = (Math.sin(idle + i * 0.2) * 0.5 + 0.5) * 0.09 + 0.01;
      }
      const h = Math.max(1.2, amp * c.height * 0.85);
      cx.fillStyle = `rgba(${Math.floor(amp*115)},${145+Math.floor(amp*110)},${205+Math.floor(amp*50)},${0.18+amp*0.72})`;
      cx.fillRect(i*(bw+1), cy - h/2, bw, h);
    }
    idle += 0.02;
  })();
}

// ── ORBE ÉTAT ─────────────────────────────────────────
function setContent(on) {
  STATE.contentOn = on;
  const w = document.getElementById('orb-wrap');
  if (!w) return;
  if (on) { w.classList.remove('orb-center'); w.classList.add('orb-corner'); }
  else    { w.classList.remove('orb-corner'); w.classList.add('orb-center'); }
}
function checkContent() {
  const hasMsgs = document.querySelectorAll('#chat-zone .msg').length > 0;
  setContent(STATE.mapActive || STATE.camActive || hasMsgs);
}
function orbState(s) {
  const w = document.getElementById('orb-wrap');
  if (w) {
    w.classList.remove('s-listen','s-speak','s-think');
    if (s) w.classList.add('s-'+s);
  }
  const dot = document.getElementById('sb-dot');
  const txt = document.getElementById('sb-status');
  const map = { listen:['dot','EN ÉCOUTE'], speak:['dot','RÉPOND'], think:['dot amber','TRAITEMENT'] };
  const [dc,tc] = map[s] || [STATE.apiOk?'dot':'dot red','EN ATTENTE'];
  if (dot) dot.className = dc;
  if (txt) txt.textContent = tc;
}

// ── RECONNAISSANCE VOCALE ─────────────────────────────
function initRecognition() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    sysMsg('<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px;"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg> Web Speech API non disponible dans ce navigateur.');
    return;
  }
  const r = new SR();
  r.continuous = true; r.interimResults = true; r.lang = 'fr-FR';
  r.onstart  = () => { STATE.recLock = true; };
  r.onend    = () => {
    STATE.recLock = false;
    if (STATE.listening) setTimeout(() => { if (STATE.listening && !STATE.recLock) _safeStart(); }, 250);
  };
  r.onerror  = e => {
    STATE.recLock = false;
    if (e.error === 'not-allowed') { sysMsg('<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px;"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg> Accès micro refusé'); stopMic(); }
  };
  r.onresult = e => {
    const last = e.results[e.results.length-1];
    if (last.isFinal) {
      const t = last[0].transcript.trim();
      if (t.length > 1) send(t);
    }
  };
  STATE.recognition = r;
}

function _safeStart() {
  if (!STATE.recognition || STATE.recLock) return;
  try { STATE.recognition.start(); } catch(e) {}
}

function startMic() {
  STATE.listening = true; _safeStart();
  const m = document.getElementById('h-mic');
  if (m) { m.textContent = 'ÉCOUTE'; m.classList.add('ok'); m.classList.remove('err'); }
  orbState('listen');
}

function stopMic() {
  STATE.listening = false;
  if (STATE.recognition && STATE.recLock) {
    try { STATE.recognition.stop(); } catch(e) {}
  }
  const m = document.getElementById('h-mic');
  if (m) { m.textContent = 'VEILLE'; m.classList.remove('ok'); m.classList.add('err'); }
  orbState();
}

function toggleMic() {
  if (STATE.listening) stopMic(); else startMic();
}

// ── GESTION DES MESSAGES ────────────────────────────
function sysMsg(txt) {
  const z = document.getElementById('chat-zone');
  if (!z) return;
  const el = document.createElement('div');
  el.className = 'sys-msg';
  el.textContent = txt;
  z.appendChild(el);
  z.scrollTop = z.scrollHeight;
  setTimeout(() => el.remove(), 8000);
}

function addMsg(txt, sender, mode = '') {
  const z = document.getElementById('chat-zone');
  if (!z) return;
  checkContent();
  const wrap = document.createElement('div');
  wrap.className = `msg m-${sender}`;
  
  const tags = {
    web_search: '<span class="mode-tag mt-web">OSINT</span>',
    deep_think: '<span class="mode-tag mt-deep">DEEP MODEL</span>',
    vision: '<span class="mode-tag mt-vision">VISION</span>',
    system: '<span class="mode-tag mt-exec">SYSTEM</span>'
  };
  const modeTag = mode && tags[mode] ? tags[mode] : '';
  
  const c = txt.replace(/</g, '&lt;').replace(/>/g, '&gt;');
  
  if (sender === 'jarvis') {
    wrap.innerHTML = `<div class="msg-who">JARVIS</div>${modeTag}<div class="msg-body typing"></div>`;
    z.appendChild(wrap);
    let i = 0;
    const body = wrap.querySelector('.msg-body');
    const tid = setInterval(() => {
      body.innerHTML = c.slice(0, ++i);
      z.scrollTop = z.scrollHeight;
      if (i >= c.length) {
        body.classList.remove('typing');
        clearInterval(tid);
      }
    }, 12);
  } else {
    wrap.innerHTML = `<div class="msg-who">USER</div><div class="msg-body">${c}</div>`;
    z.appendChild(wrap);
    z.scrollTop = z.scrollHeight;
  }
}

// ── COMMUNICATION API ────────────────────────────
async function checkApi() {
  try {
    const r = await fetch('/api/health');
    const d = await r.json();
    STATE.apiOk = true;
    const api = document.getElementById('h-api');
    if (api) api.innerHTML = '<span class="dot"></span> EN LIGNE';
    const mod = document.getElementById('h-model');
    if (mod) mod.textContent = d.model || 'GEMINI';
    refreshProviders();
    orbState(STATE.listening ? 'listen' : '');
  } catch (e) {
    STATE.apiOk = false;
    const api = document.getElementById('h-api');
    if (api) api.innerHTML = '<span class="dot red"></span> HORS LIGNE';
    orbState();
  }
}

function sendTxt() {
  const el = document.getElementById('txt');
  if (!el || !el.value.trim()) return;
  send(el.value.trim());
  el.value = '';
}

async function send(text) {
  if (!text) return;
  STATE.history.push(text);
  addMsg(text, 'user');
  orbState('think');
  const t0 = Date.now();
  
  try {
    const r = await fetch('/api/tool-chat', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ message: text })
    });
    const d = await r.json();
    STATE.latency = Date.now() - t0;
    const lat = document.getElementById('h-latency');
    if (lat) lat.textContent = STATE.latency + 'ms';
    
    orbState('speak');
    setTimeout(() => { orbState(STATE.listening ? 'listen' : ''); }, 2000);
    
    let modeUsed = d.mode_used || '';
    if (d.action) {
       modeUsed = 'system';
       if (d.action.type === 'open_url' || d.action.action === 'open_url') {
           window.open(d.action.url, '_blank');
       } else if (d.action.command === 'camera' || d.action.command === 'vision') {
           toggleCam();
       } else if (d.action.command === 'screen') {
           sysMsg('Capture écran non dispo sans https.');
       }
    }
    
    addMsg(d.reply || 'Fait.', 'jarvis', modeUsed);
    if ('speechSynthesis' in window) {
       const utter = new window.SpeechSynthesisUtterance((d.reply || 'Fait').replace(/[*_#`]/g, '').substring(0, 200));
       utter.lang = 'fr-FR';
       window.speechSynthesis.speak(utter);
    }
    
  } catch (e) {
    orbState();
    addMsg('Erreur de communication avec le noyau central.', 'jarvis');
  }
}

// ── UTILS ET INTERACTIONS ────────────────────────────
function initKeys() {
  window.addEventListener('keydown', e => {
    if (e.target.tagName === 'INPUT') {
      if (e.code === 'Enter') sendTxt();
      return;
    }
    if (e.code === 'Space') { e.preventDefault(); toggleMic(); }
    if (e.code === 'KeyC') toggleCam();
    if (e.code === 'KeyN') { if (STATE.mapActive) hideMap(); else showMap(); }
    if (e.code === 'Escape') {
      stopMic();
      if ('speechSynthesis' in window) window.speechSynthesis.cancel();
      hideMap(); hideCam();
    }
  });
}

const TOOLS = [
  { icon: `<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>`, label: 'Recherche Web', cmd: 'Cherche sur internet ' },
  { icon: `<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2"></path><path d="M12 20v2"></path><path d="m4.93 4.93 1.41 1.41"></path><path d="m17.66 17.66 1.41 1.41"></path><path d="M2 12h2"></path><path d="M20 12h2"></path><path d="m6.34 17.66-1.41 1.41"></path><path d="m19.07 4.93-1.41 1.41"></path></svg>`, label: 'Météo Locale', cmd: 'Quel temps fait-il actuellement ?' },
  { icon: `<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>`, label: 'Réseau Info',  cmd: 'Quel est mon statut réseau ?' },
  { icon: `<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"></path><circle cx="12" cy="13" r="3"></circle></svg>`, label: 'Vision Cam', cmd: null, fn: () => { toggleCam(); } },
  { icon: `<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line></svg>`, label: 'Scanner Carte', cmd: null, fn: () => { showMap(); setTimeout(hideMap, 6000); } },
];

function initTools() {
  const g = document.getElementById('tools-grid');
  if (!g) return;
  TOOLS.forEach(t => {
    const btn = document.createElement('button');
    btn.className = 'tool-btn';
    btn.innerHTML = `<span class="tool-icon">${t.icon}</span>${t.label}`;
    btn.onclick = () => {
      toggleTools();
      if (t.fn) { t.fn(); return; }
      if (t.cmd) {
         if (t.cmd.endsWith(' ')) {
           const i = document.getElementById('txt');
           if (i) { i.value = t.cmd; i.focus(); }
         } else send(t.cmd);
      }
    };
    g.appendChild(btn);
  });
}

function toggleTools() {
  const p = document.getElementById('tools-panel');
  if (p) p.style.display = p.style.display === 'block' ? 'none' : 'block';
}

function toggleModelPanel() {
  const p = document.getElementById('model-panel');
  if (p) p.style.display = p.style.display === 'block' ? 'none' : 'block';
}

async function refreshProviders() {
  try {
    const r = await fetch('/api/providers');
    const d = await r.json();
    const l = document.getElementById('mp-list');
    if (l && d.providers) {
      l.innerHTML = '';
      d.providers.forEach(p => {
        const div = document.createElement('div');
        div.className = 'mp-item';
        div.innerHTML = `<span>${p.name}</span> <span class="mp-badge bg-free">ACTIF</span>`;
        if (p.id) div.onclick = () => setProvider(p.id);
        l.appendChild(div);
      });
    }
    const o = document.getElementById('mp-ollama');
    if (o && d.ollama_models && d.ollama_models.length) {
      o.innerHTML = d.ollama_models.map(m => `<div class="mp-item" onclick="setProvider('local')">${m}</div>`).join('');
    }
  } catch (e) {}
}

function setProvider(id) {
  fetch('/api/set-provider', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({provider_id: id})
  });
  toggleModelPanel();
  checkApi();
}

function toggleCam() {
  STATE.camActive ? hideCam() : showCam();
}
function showCam() {
  navigator.mediaDevices.getUserMedia({ video: true }).then(s => {
    const v = document.getElementById('cam-video');
    const p = document.getElementById('cam-panel');
    if (v) v.srcObject = s;
    if (p) p.classList.add('on');
    STATE.camActive = true;
    const hcam = document.getElementById('h-cam');
    if (hcam) { hcam.textContent = 'ON'; hcam.className = 'hv ok'; }
    setContent(true);
  }).catch(() => sysMsg('Caméra bloquée ou absente.'));
}
function hideCam() {
  const v = document.getElementById('cam-video');
  const p = document.getElementById('cam-panel');
  if (v && v.srcObject) v.srcObject.getTracks().forEach(t => t.stop());
  if (p) p.classList.remove('on');
  STATE.camActive = false;
  const hcam = document.getElementById('h-cam');
  if (hcam) { hcam.textContent = 'OFF'; hcam.className = 'hv'; }
  checkContent();
}

function updateSysCpu() {
  const c = document.getElementById('h-cpu');
  if (c) c.textContent = (Math.random() * 12 + 2).toFixed(1) + '%';
}

// Exposés globaux pour inline event handlers html
window.sendTxt = sendTxt;
window.toggleTools = toggleTools;
window.toggleModelPanel = toggleModelPanel;
window.toggleCam = toggleCam;
window.setProvider = setProvider;
