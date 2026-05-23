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

// Web Preview Mock pour que ça marche dans AI Studio sans Electron
if (!window.jarvis) {
  console.log("Running in Web Preview. Using local API fallback.");
  window.jarvis = {
    sendMessage: async (message) => {
      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message })
        });
        return await res.json();
      } catch (e) {
        return { reply: "Serveur API non disponible en preview web." };
      }
    },
    openUrl: (url) => { window.open(url, '_blank'); },
    onJarvisResponse: () => {},
    onTranscription: () => {},
    onPythonLog: () => {}
  };
}

window.addEventListener('DOMContentLoaded', () => {
  initClock();
  initWaveform();
  initNetworkMap();
  initSpeechRecognition();
  checkApiHealth();

  // Add click handler to mic status panel for fallback activation
  const micStatus = document.getElementById('mic-status');
  if (micStatus && micStatus.parentElement) {
    micStatus.parentElement.style.cursor = 'pointer';
    micStatus.parentElement.addEventListener('click', toggleListening);
  }

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
    document.getElementById('status-time').textContent =
      now.toLocaleTimeString('fr-FR', {hour:'2-digit', minute:'2-digit'});
  }
  tick();
  setInterval(tick, 1000);
}

function initWaveform() {
  const canvas = document.getElementById('waveform-canvas');
  const ctx = canvas.getContext('2d');
  canvas.width  = 500;
  canvas.height = 55;

  let analyser = null;
  let dataArray = null;
  let idlePhase = 0;

  // Connecter le micro si dispo
  navigator.mediaDevices.getUserMedia({ audio: true, video: false })
    .then(stream => {
      const audioCtx = new AudioContext();
      const source   = audioCtx.createMediaStreamSource(stream);
      analyser        = audioCtx.createAnalyser();
      analyser.fftSize = 128;
      source.connect(analyser);
      dataArray = new Uint8Array(analyser.frequencyBinCount);
    })
    .catch(() => {}); // pas de micro → mode idle

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const bars   = 64;
    const barW   = canvas.width / bars - 1;
    const cy     = canvas.height / 2;

    for (let i = 0; i < bars; i++) {
      let amplitude;

      if (analyser && dataArray) {
        analyser.getByteFrequencyData(dataArray);
        amplitude = dataArray[i] / 255;
      } else {
        // Animation idle organique
        amplitude = (
          Math.sin(idlePhase + i * 0.28) * 0.3 +
          Math.sin(idlePhase * 1.7 + i * 0.15) * 0.15 +
          0.06
        );
        amplitude = Math.max(0.03, amplitude);
      }

      const h = amplitude * (canvas.height * 0.82);

      // Couleur : cyan quand bas, blanc pur quand haut
      const brightness = Math.floor(amplitude * 255);
      const r = brightness;
      const g = 191 + Math.floor(amplitude * 64);
      const b = 255;
      const alpha = 0.25 + amplitude * 0.75;

      // Barre symétrique (vers le haut ET vers le bas depuis le centre)
      ctx.fillStyle = `rgba(${r},${g},${b},${alpha})`;
      ctx.fillRect(i * (barW + 1), cy - h / 2, barW, h);

      // Reflet en dessous (opacité réduite de moitié)
      ctx.fillStyle = `rgba(${r},${g},${b},${alpha * 0.3})`;
      ctx.fillRect(i * (barW + 1), cy + h / 2, barW, h * 0.4);
    }

    idlePhase += 0.022;
    requestAnimationFrame(draw);
  }

  draw();
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
      const bText = document.getElementById('status-text');
      if (bText) bText.textContent = 'ACCÈS REFUSÉ';
    }
  };

  state.recognition.onresult = (event) => {
    const last = event.results[event.results.length - 1];
    const transcript = last[0].transcript.trim();
    if (last.isFinal && transcript.length > 0) {
      if (window.sendToJarvis) window.sendToJarvis(transcript);
      else sendToJarvis(transcript);
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
    const bText = document.getElementById('status-text');
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
    const bText = document.getElementById('status-text');
    if (bText) bText.textContent = 'EN ATTENTE';

    if (state.recognition && state.recognitionActive) {
      try {
        state.recognition.stop();
      } catch (e) {
        console.warn('SpeechRecognition stop error:', e);
      }
    }
  }
}

async function sendToJarvis(message) {
  addMessage('user', message);
  document.getElementById('status-text').textContent = 'TRAITEMENT...';

  document.getElementById('jarvis-orb').classList.add('state-speaking');

  try {
    const result = await window.jarvis.sendMessage(message);

    addMessage('jarvis', result.reply);
    document.getElementById('status-text').textContent = 'EN ÉCOUTE';

    if (result.action) {
      handleAction(result.action);
    }
  } catch (err) {
    addMessage('jarvis', 'Je rencontre une difficulté de connexion.');
  } finally {
    document.getElementById('jarvis-orb').classList.remove('state-speaking');
  }
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
      } else if (action.command === 'screen') {
        analyzeScreen();
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

async function analyzeScreen() {
  document.getElementById('jarvis-orb').classList.add('state-listening');
  addMessage('jarvis', 'Analyse de l\'écran en cours...');
  
  if (window.jarvis && window.jarvis.analyzeScreen) {
    try {
      const result = await window.jarvis.analyzeScreen();
      addMessage('jarvis', result.reply);
    } catch (e) {
      console.error(e);
      addMessage('jarvis', 'Erreur d\'accès à l\'écran.');
    }
  } else {
    // Web Fallback
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({ video: { cursor: "always" }, audio: false });
      addMessage('jarvis', 'Aperçu acquis (Mode Web : analyse sommaire)');
      setTimeout(() => stream.getTracks().forEach(t => t.stop()), 1000);
    } catch(err) {
      addMessage('jarvis', 'Capture annulée ou refusée.');
    }
  }
  document.getElementById('jarvis-orb').classList.remove('state-listening');
}

async function checkApiHealth() {
  try {
    const response = await fetch('/api/health'); // fallback web endpoint
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
  if ((e.code === 'Space' || e.key === ' ') && !e.target.matches('input, textarea, [contenteditable]')) {
    e.preventDefault();
    toggleListening();
  }
  if (e.code === 'KeyC') toggleCamera();
  if (e.code === 'KeyM') showNetworkMap();
  if (e.code === 'KeyS') analyzeScreen();
});

// Déclencher la carte réseau à chaque réponse de JARVIS
const originalSendToJarvis = sendToJarvis;
window.sendToJarvis = async function(message) {
  showNetworkMap();
  await originalSendToJarvis(message);
  // Masquer après 8 secondes
  setTimeout(hideNetworkMap, 8000);
};

// Charger les providers disponibles
async function loadProviders() {
  try {
    const r = await fetch('http://127.0.0.1:5001/providers');
    const data = await r.json();
    renderProviderList(data.providers, data.ollama_models);
  } catch(e) {
    console.warn("Could not load providers", e);
  }
}

function renderProviderList(providers, ollama_models) {
  const list = document.getElementById('provider-list');
  list.innerHTML = '';
  providers.forEach(p => {
    const div = document.createElement('div');
    div.style.cssText = `
      padding:5px 8px; margin:2px 0; cursor:pointer;
      border-radius:3px; font-family:'Rajdhani',sans-serif;
      font-size:11px; letter-spacing:0.08em;
      color:${p.available ? '#C8E4FF' : '#3A5A7A'};
      border:1px solid ${p.available ? 'rgba(0,191,255,0.15)' : 'transparent'};
      display:flex; justify-content:space-between; align-items:center;
    `;
    const badge = p.free
      ? '<span style="color:#00E676;font-size:9px">GRATUIT</span>'
      : '<span style="color:#FFB300;font-size:9px">PAYANT</span>';
    div.innerHTML = `<span>${p.name}</span>${p.available ? badge : '<span style="color:#555;font-size:9px">CLEF MANQUANTE</span>'}`;
    if (p.available) {
      div.onmouseenter = () => div.style.background = 'rgba(0,191,255,0.08)';
      div.onmouseleave = () => div.style.background = '';
      div.onclick = () => switchProvider(p.id);
    }
    list.appendChild(div);
  });

  // Modèles Ollama
  const ollamaList = document.getElementById('ollama-list');
  ollamaList.innerHTML = '';
  if (ollama_models.length === 0) {
    ollamaList.innerHTML = '<div style="color:#3A5A7A;font-size:10px;font-family:Rajdhani">Ollama non détecté</div>';
  } else {
    ollama_models.forEach(m => {
      const div = document.createElement('div');
      div.style.cssText = 'padding:4px 8px;cursor:pointer;color:#C8E4FF;font-family:Rajdhani,sans-serif;font-size:11px;';
      div.textContent = `▸ ${m}`;
      div.onclick = () => {
        fetch('http://127.0.0.1:5001/set-provider', {
          method:'POST', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({provider_id:'ollama-auto'})
        });
        document.getElementById('model-name').textContent = m.toUpperCase();
        toggleProviderSelector();
      };
      ollamaList.appendChild(div);
    });
  }
}

async function switchProvider(providerId) {
  const r = await fetch('http://127.0.0.1:5001/set-provider', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({provider_id: providerId})
  });
  const data = await r.json();
  document.getElementById('model-name').textContent = data.provider.toUpperCase().slice(0,16);
  toggleProviderSelector();
  addMessage('jarvis', `Modèle changé : ${data.provider}`);
}

function toggleProviderSelector() {
  const sel = document.getElementById('provider-selector');
  sel.style.display = sel.style.display === 'none' ? 'block' : 'none';
}

// Appeler au démarrage
loadProviders();
