class NetworkMap {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.nodes = [];
    this.connections = [];
    this.animFrame = null;
    this.generateNodes(80);
    this.generateConnections();
  }

  generateNodes(count) {
    for (let i = 0; i < count; i++) {
      this.nodes.push({
        x: Math.random() * this.canvas.width,
        y: Math.random() * this.canvas.height,
        radius: Math.random() * 2.5 + 0.5,
        pulsePhase: Math.random() * Math.PI * 2,
        isHub: Math.random() < 0.1
      });
    }
  }

  generateConnections() {
    this.nodes.forEach((node, i) => {
      const distances = this.nodes
        .map((other, j) => ({
          j,
          dist: Math.hypot(other.x - node.x, other.y - node.y)
        }))
        .filter(d => d.j !== i && d.dist < 180)
        .sort((a, b) => a.dist - b.dist)
        .slice(0, 3);

      distances.forEach(d => {
        if (!this.connections.find(c =>
          (c.a === i && c.b === d.j) || (c.a === d.j && c.b === i)
        )) {
          this.connections.push({
            a: i, b: d.j,
            opacity: Math.random() * 0.3 + 0.05
          });
        }
      });
    });
  }

  draw(timestamp) {
    const { ctx, canvas, nodes, connections } = this;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    connections.forEach(conn => {
      const a = nodes[conn.a];
      const b = nodes[conn.b];
      const gradient = ctx.createLinearGradient(a.x, a.y, b.x, b.y);
      gradient.addColorStop(0, `rgba(0, 96, 128, ${conn.opacity})`);
      gradient.addColorStop(0.5, `rgba(0, 160, 200, ${conn.opacity * 1.5})`);
      gradient.addColorStop(1, `rgba(0, 96, 128, ${conn.opacity})`);
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.strokeStyle = gradient;
      ctx.lineWidth = 0.5;
      ctx.stroke();
    });

    nodes.forEach(node => {
      const pulse = Math.sin(timestamp * 0.002 + node.pulsePhase) * 0.5 + 0.5;
      const r = node.isHub ? node.radius * 2.5 : node.radius;
      const alpha = node.isHub ? 0.7 + pulse * 0.3 : 0.3 + pulse * 0.3;
      const color = node.isHub ? `rgba(0, 255, 136, ${alpha})` : `rgba(0, 191, 255, ${alpha})`;

      if (node.isHub) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, r * 4, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 255, 136, ${0.03 * pulse})`;
        ctx.fill();
      }

      ctx.beginPath();
      ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
    });

    this.animFrame = requestAnimationFrame(ts => this.draw(ts));
  }

  start() { requestAnimationFrame(ts => this.draw(ts)); }
  stop()  { cancelAnimationFrame(this.animFrame); }
}

const state = {
  isListening: false,
  isSpeaking: false,
  cameraActive: false,
  networkMapVisible: false,
  recognition: null,
  recognitionActive: false
};

window.addEventListener('DOMContentLoaded', () => {
  initClock();
  initWaveform();
  initNetworkMap();
  initSpeechRecognition();
  checkApiHealth();

  setTimeout(() => {
    document.getElementById('jarvis-orb').className = 'orb-corner-mode';
    addMessage('jarvis', 'Système en ligne. En attente d\'instructions.');
  }, 2000);
});

function initClock() {
  function tick() {
    const now = new Date();
    const time = now.toLocaleTimeString('fr-FR', {hour12: false});
    document.getElementById('sys-time').textContent = time;
    document.getElementById('status-bar-time').textContent =
      now.toLocaleTimeString('fr-FR', {hour:'2-digit', minute:'2-digit'});
  }
  tick();
  setInterval(tick, 1000);
}

function initWaveform() {
  const canvas = document.getElementById('waveform-canvas');
  const ctx = canvas.getContext('2d');
  canvas.width = 400;
  canvas.height = 60;

  let idlePhase = 0;
  function drawIdle() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const bars = 60;
    const bw = canvas.width / bars;
    for (let i = 0; i < bars; i++) {
      const h = (Math.sin(idlePhase + i * 0.3) * 0.5 + 0.5) * 8 + 2;
      ctx.fillStyle = 'rgba(0,191,255,0.2)';
      ctx.fillRect(i * bw, (canvas.height - h) / 2, bw - 1, h);
    }
    idlePhase += 0.03;
    if (!state.isListening) requestAnimationFrame(drawIdle);
  }
  drawIdle();
}

function initNetworkMap() {
  const canvas = document.getElementById('network-canvas');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  window.networkMap = new NetworkMap(canvas);
}

function showNetworkMap() {
  document.getElementById('network-canvas').style.opacity = '0.6';
  window.networkMap.start();
  state.networkMapVisible = true;
}

function hideNetworkMap() {
  document.getElementById('network-canvas').style.opacity = '0';
  window.networkMap.stop();
  state.networkMapVisible = false;
}

function initSpeechRecognition() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    console.warn('SpeechRecognition non disponible');
    return;
  }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  state.recognition = new SR();
  state.recognition.continuous = true;
  state.recognition.interimResults = true;
  state.recognition.lang = 'fr-FR';

  state.recognition.onstart = () => {
    state.recognitionActive = true;
  };

  state.recognition.onerror = (event) => {
    console.error('Speech recognition error:', event.error);
    if (event.error === 'not-allowed') {
      state.isListening = false;
      const orb = document.getElementById('jarvis-orb');
      const micStatus = document.getElementById('mic-status');
      if (orb) orb.classList.remove('state-listening');
      if (micStatus) {
        micStatus.textContent = 'VEILLE';
        micStatus.style.color = '';
      }
      const bText = document.getElementById('status-bar-text');
      if (bText) bText.textContent = 'ACCÈS REFUSÉ';
    }
  };

  state.recognition.onresult = (event) => {
    const last = event.results[event.results.length - 1];
    const transcript = last[0].transcript.trim();
    if (last.isFinal && transcript.length > 0) {
      sendToJarvis(transcript);
    }
  };

  state.recognition.onend = () => {
    state.recognitionActive = false;
    if (state.isListening) {
      try {
        state.recognition.start();
      } catch (e) {
        console.warn('SpeechRecognition auto-restart ignored:', e);
      }
    }
  };
}

function toggleListening() {
  state.isListening = !state.isListening;
  const orb = document.getElementById('jarvis-orb');
  const micStatus = document.getElementById('mic-status');

  if (state.isListening) {
    if (orb) orb.classList.add('state-listening');
    if (micStatus) {
      micStatus.textContent = 'ÉCOUTE';
      micStatus.style.color = '#00FF88';
    }
    const bText = document.getElementById('status-bar-text');
    if (bText) bText.textContent = 'EN ÉCOUTE';

    if (state.recognition && !state.recognitionActive) {
      try {
        state.recognition.start();
      } catch (e) {
        console.warn('SpeechRecognition start error:', e);
      }
    }
  } else {
    if (orb) orb.classList.remove('state-listening');
    if (micStatus) {
      micStatus.textContent = 'VEILLE';
      micStatus.style.color = '';
    }
    const bText = document.getElementById('status-bar-text');
    if (bText) bText.textContent = 'EN ATTENTE';

    if (state.recognition && state.recognitionActive) {
      try {
        state.recognition.stop();
      } catch (e) {
        console.warn('SpeechRecognition stop error:', e);
      }
    }
    
    // Restart idle waveform
    initWaveform();
  }
}

async function sendToJarvis(message) {
  addMessage('user', message);
  document.getElementById('status-bar-text').textContent = 'TRAITEMENT...';
  document.getElementById('jarvis-orb').classList.add('state-speaking');

  try {
    // Utiliser /tool-chat : l'IA choisit elle-même ses outils
    const r = await fetch('http://127.0.0.1:5001/tool-chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message})
    });
    const result = await r.json();

    // Afficher l'outil ou le mode utilisé
    let modeText = '';
    if (result.mode_used === 'web_search') modeText = '🔍 Recherche Web';
    if (result.mode_used === 'deep_think') modeText = '🧠 Réflexion Profonde';
    if (result.mode_used === 'vision') modeText = '👁 Analyse Visuelle';
    if (result.mode_used === 'browser') modeText = '🌐 Navigateur';
    if (result.mode_used === 'quick') modeText = '⚡ Action Rapide';

    if (modeText) {
      addSystemMessage(`Mode : ${modeText}`);
    } else if (result.tool_used) {
      addSystemMessage(`Outil : ${result.tool_used}`);
    }

    addMessage('jarvis', result.reply);

    if (result.action) handleAction(result.action);

  } catch(err) {
    addMessage('jarvis', 'Connexion au serveur impossible.');
  } finally {
    document.getElementById('jarvis-orb').classList.remove('state-speaking');
    document.getElementById('status-bar-text').textContent = 'EN ÉCOUTE';
  }
}

// Message système (info, pas une réponse IA)
function addSystemMessage(text) {
  const zone = document.getElementById('chat-zone');
  const div = document.createElement('div');
  div.style.cssText = `
    font-family:'Rajdhani',sans-serif; font-size:10px;
    color:rgba(0,191,255,0.5); letter-spacing:0.1em;
    text-align:center; padding:2px;
  `;
  div.textContent = text;
  zone.appendChild(div);
}

function addMessage(role, text) {
  const zone = document.getElementById('chat-zone');
  const div = document.createElement('div');
  div.className = role === 'user' ? 'msg-user' : 'msg-jarvis';

  if (role === 'jarvis') {
    div.classList.add('typing-cursor');
    zone.appendChild(div);
    let i = 0;
    const interval = setInterval(() => {
      div.textContent = text.slice(0, ++i);
      zone.scrollTop = zone.scrollHeight;
      if (i >= text.length) {
        div.classList.remove('typing-cursor');
        clearInterval(interval);
      }
    }, 18);
  } else {
    div.textContent = text;
    zone.appendChild(div);
  }

  zone.scrollTop = zone.scrollHeight;

  setTimeout(() => {
    div.style.transition = 'opacity 1s';
    div.style.opacity = '0';
    setTimeout(() => div.remove(), 1000);
  }, 30000);
}

function handleAction(action) {
  switch (action.type || action.action) {
    case 'open_url':
      window.jarvis.openUrl(action.url);
      showNetworkMap();
      setTimeout(hideNetworkMap, 5000);
      break;
    case 'show_map':
      showNetworkMap();
      setTimeout(hideNetworkMap, 8000);
      break;
    case 'system':
      if (action.command === 'camera') {
        toggleCamera();
      }
      break;
  }
}

async function toggleCamera() {
  const feed = document.getElementById('camera-feed');
  const video = document.getElementById('camera-video');
  const camStatus = document.getElementById('cam-status');

  if (!state.cameraActive) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      video.srcObject = stream;
      feed.style.opacity = '1';
      state.cameraActive = true;
      camStatus.textContent = 'ACTIF';
      camStatus.style.color = '#00FF88';
    } catch (e) {
      addMessage('jarvis', 'Accès à la caméra refusé.');
    }
  } else {
    video.srcObject?.getTracks().forEach(t => t.stop());
    feed.style.opacity = '0';
    state.cameraActive = false;
    camStatus.textContent = 'OFF';
    camStatus.style.color = '';
  }
}

async function checkApiHealth() {
  try {
    const response = await fetch('http://localhost:5001/health');
    if (!response.ok) throw new Error();
    const data = await response.json();
    if (data.status === 'ok') {
      document.getElementById('api-status').textContent = 'CONNECTÉ';
      document.getElementById('api-status').className = 'hud-value status-ok';
      if (data.model) {
        document.getElementById('model-name').textContent = String(data.model).toUpperCase();
      }
    }
  } catch {
    document.getElementById('api-status').textContent = 'HORS LIGNE';
    document.getElementById('api-status').style.color = '#FF4040';
  }
}

window.addEventListener('keydown', (e) => {
  if (e.code === 'Space' && !e.target.matches('input, textarea')) {
    e.preventDefault();
    toggleListening();
  }
  if (e.code === 'KeyC') toggleCamera();
  if (e.code === 'KeyM') showNetworkMap();
});

// ===== PANNEAU D'OUTILS =====

const TOOLS_UI = [
  { label: "Chercher sur le web",     cmd: "JARVIS, cherche " },
  { label: "Actualités",               cmd: "JARVIS, quelles sont les dernières actualités ?" },
  { label: "Météo",                    cmd: "JARVIS, quel temps fait-il à Paris ?" },
  { label: "Infos système",            cmd: "JARVIS, montre-moi les infos système" },
  { label: "Vitesse internet",         cmd: "JARVIS, teste ma connexion internet" },
  { label: "Screenshot",               cmd: "JARVIS, prends un screenshot" },
  { label: "Presse-papier",            cmd: "JARVIS, lis mon presse-papier" },
  { label: "Calculer",                 cmd: "JARVIS, calcule " },
  { label: "YouTube",                  cmd: "JARVIS, cherche sur YouTube " },
  { label: "Wikipedia",               cmd: "JARVIS, que dit Wikipedia sur " },
  { label: "Rappel",                   cmd: "JARVIS, rappelle-moi dans 5 minutes de " },
  { label: "Créer un fichier",         cmd: "JARVIS, crée un fichier texte avec " },
  { label: "Contrôle souris",         cmd: "JARVIS, clique au centre de l'écran" },
  { label: "Taper du texte",           cmd: "JARVIS, tape le texte : " },
  { label: "Téléphone (Android)",      cmd: "JARVIS, montre le téléphone" },
  { label: "Home Assistant",           cmd: "JARVIS, état de la maison" },
];

function renderToolsGrid() {
  const grid = document.getElementById('tools-grid');
  grid.innerHTML = '';
  TOOLS_UI.forEach(tool => {
    const btn = document.createElement('button');
    btn.style.cssText = `
      background:rgba(0,80,130,0.2);
      border:1px solid rgba(0,191,255,0.15);
      border-radius:4px;
      padding:8px 6px;
      cursor:pointer;
      text-align:left;
      color:#C8E4FF;
      font-family:'Rajdhani',sans-serif;
      font-size:11px;
      letter-spacing:0.05em;
      transition:all 0.2s;
      display:flex; align-items:center; gap:6px;
    `;
    btn.innerHTML = `<span>${tool.label}</span>`;
    btn.onmouseenter = () => btn.style.background = 'rgba(0,191,255,0.12)';
    btn.onmouseleave = () => btn.style.background = 'rgba(0,80,130,0.2)';
    btn.onclick = () => {
      // Pré-remplir la commande ou l'exécuter directement
      if (tool.cmd.endsWith(' ')) {
        // La commande attend une suite → mettre dans l'input
        const input = document.getElementById('text-input');
        if (input) { input.value = tool.cmd; input.focus(); }
        else sendToJarvis(tool.cmd + '...');
      } else {
        sendToJarvis(tool.cmd);
      }
      toggleToolsPanel();
    };
    grid.appendChild(btn);
  });
}

function toggleToolsPanel() {
  const panel = document.getElementById('tools-panel');
  panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
  if (panel.style.display === 'block') renderToolsGrid();
}
