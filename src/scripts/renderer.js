/* ═══════════════════════════════════════════
   JARVIS renderer.js — Design @huwprosser
   Complet, connecté, fonctionnel.
═══════════════════════════════════════════ */
const STATE = {
  listening: false,
  speaking: false,
  camActive: false,
  mapActive: false,
  contentOn: false,
  apiOk: false,
  history: [],
  latency: 0,
};

// ── BOOT ──────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", boot);
async function boot() {
  const fill = document.getElementById("boot-fill");
  const hint = document.getElementById("boot-hint");
  const hints = [
    "Chargement des modules systèmes…",
    "Connexion au moteur Open Interpreter…",
    "Initialisation de la reconnaissance vocale…",
    "Prêt.",
  ];
  let pct = 0,
    hi = 0;
  const iv = setInterval(() => {
    pct = Math.min(pct + Math.random() * 8 + 4, 95);
    if (fill) fill.style.width = pct + "%";
    if (pct > 25 * (hi + 1) && hi < hints.length - 1) {
      hi++;
      if (hint) hint.textContent = hints[hi];
    }
  }, 75);
  initClock();
  initWaveform();
  initMap();
  initLiveStream();
  initStatusPolling();
  initKeys();
  initTools();
  await checkApi();
  clearInterval(iv);
  if (fill) fill.style.width = "100%";
  if (hint) hint.textContent = "Système actif.";
  setTimeout(() => {
    const s = document.getElementById("boot-screen");
    if (s) s.classList.add("out");
    setTimeout(() => {
      if (s) s.remove();
    }, 950);
  }, 350);
  setInterval(checkApi, 15000);
  setInterval(updateSysCpu, 5000);
}

// ── HORLOGE ───────────────────────────────────────────
function initClock() {
  const tick = () => {
    const n = new Date();
    const full = n.toLocaleTimeString("fr-FR", { hour12: false });
    const short = n.toLocaleTimeString("fr-FR", {
      hour: "2-digit",
      minute: "2-digit",
    });
    const et = document.getElementById("h-time");
    if (et) et.textContent = full;
    const ot = document.getElementById("orb-time");
    if (ot) ot.textContent = full;
    const st = document.getElementById("sb-time");
    if (st) st.textContent = short;
  };
  tick();
  setInterval(tick, 1000);
}

// ── MAP RÉSEAU ────────────────────────────────────────
let mapInstance = null;
let googleMap = null;
let gmapLoaded = false;
let gmapPendingCommand = null;

async function initMap() {
  const c = document.getElementById("map-canvas");
  if (!c) return;
  const resize = () => {
    c.width = innerWidth;
    c.height = innerHeight;
    mapInstance?.reset();
  };
  resize();
  window.addEventListener("resize", resize);
  mapInstance = new NetworkMap(c);

  // Initialize Google Maps
  const gmapBg = document.getElementById("gmap-bg");
  if (gmapBg) {
    let API_KEY = "";
    try {
      API_KEY =
        window.ENV_GMAPS_KEY ||
        (typeof process !== "undefined"
          ? process.env.GOOGLE_MAPS_PLATFORM_KEY
          : "");
    } catch (e) {}

    if (API_KEY) {
      window.initGMap = async () => {
        const { Map } = await google.maps.importLibrary("maps");
        googleMap = new Map(gmapBg, {
          center: { lat: 48.8566, lng: 2.3522 }, // Paris default
          zoom: 12,
          mapId: "DEMO_MAP_ID", // Requis pour WebGL/3D
          disableDefaultUI: true,
          backgroundColor: "#02070E",
        });
        gmapLoaded = true;
        if (gmapPendingCommand) {
          executeMapCommand(gmapPendingCommand);
          gmapPendingCommand = null;
        }
      };

      const script = document.createElement("script");
      script.src = `https://maps.googleapis.com/maps/api/js?key=${API_KEY}&v=weekly&callback=initGMap`;
      script.async = true;
      script.defer = true;
      document.head.appendChild(script);
    }
  }
}
class NetworkMap {
  constructor(c) {
    this.c = c;
    this.cx = c.getContext("2d");
    this.nodes = [];
    this.edges = [];
    this.raf = null;
    this.reset();
  }
  reset() {
    this.nodes = [];
    this.edges = [];
    for (let i = 0; i < 85; i++)
      this.nodes.push({
        x: Math.random() * this.c.width,
        y: Math.random() * this.c.height,
        r: Math.random() * 2 + 0.4,
        ph: Math.random() * Math.PI * 2,
        hub: Math.random() < 0.07,
      });
    this.nodes.forEach((a, i) => {
      this.nodes
        .map((b, j) => ({ j, d: Math.hypot(b.x - a.x, b.y - a.y) }))
        .filter((x) => x.j !== i && x.d < 170)
        .sort((a, b) => a.d - b.d)
        .slice(0, 3)
        .forEach((x) => {
          if (
            !this.edges.find(
              (e) => (e.a === i && e.b === x.j) || (e.a === x.j && e.b === i),
            )
          )
            this.edges.push({ a: i, b: x.j, op: Math.random() * 0.22 + 0.04 });
        });
    });
  }
  draw(ts) {
    this.raf = requestAnimationFrame((t) => this.draw(t));
    const { cx, c, nodes: N, edges: E } = this;
    cx.clearRect(0, 0, c.width, c.height);
    E.forEach((e) => {
      const a = N[e.a],
        b = N[e.b];
      const g = cx.createLinearGradient(a.x, a.y, b.x, b.y);
      g.addColorStop(0, `rgba(18,65,125,${e.op})`);
      g.addColorStop(0.5, `rgba(38,110,180,${e.op * 1.4})`);
      g.addColorStop(1, `rgba(18,65,125,${e.op})`);
      cx.beginPath();
      cx.moveTo(a.x, a.y);
      cx.lineTo(b.x, b.y);
      cx.strokeStyle = g;
      cx.lineWidth = 0.45;
      cx.stroke();
    });
    N.forEach((n) => {
      const p = Math.sin(ts * 0.0016 + n.ph) * 0.5 + 0.5;
      const r = n.hub ? n.r * 2.6 : n.r;
      const al = n.hub ? 0.55 + p * 0.4 : 0.22 + p * 0.28;
      const col = n.hub ? `rgba(55,215,130,${al})` : `rgba(58,143,212,${al})`;
      if (n.hub) {
        cx.beginPath();
        cx.arc(n.x, n.y, r * 4, 0, Math.PI * 2);
        cx.fillStyle = `rgba(38,195,115,${0.022 * p})`;
        cx.fill();
      }
      cx.beginPath();
      cx.arc(n.x, n.y, r, 0, Math.PI * 2);
      cx.fillStyle = col;
      cx.fill();
    });
  }
  start() {
    requestAnimationFrame((t) => this.draw(t));
  }
  stop() {
    cancelAnimationFrame(this.raf);
  }
}
let mapRotationState = { active: false, heading: 0, raf: null };

function executeMapCommand(command) {
  let API_KEY = "";
  try {
    API_KEY =
      window.ENV_GMAPS_KEY ||
      (typeof process !== "undefined"
        ? process.env.GOOGLE_MAPS_PLATFORM_KEY
        : "");
  } catch (e) {}
  if (!API_KEY) {
    sysMsg(
      "Erreur : clé GOOGLE_MAPS_PLATFORM_KEY manquante. Configurez les secrets (Settings > Secrets).",
    );
    hideMap();
    return;
  }

  if (!gmapLoaded || !googleMap) {
    gmapPendingCommand = command;
    return;
  }

  // Coordinates for a few major cities to simulate locking
  const cities = {
    paris: { lat: 48.8566, lng: 2.3522 },
    "new york": { lat: 40.7128, lng: -74.006 },
    london: { lat: 51.5074, lng: -0.1278 },
    tokyo: { lat: 35.6762, lng: 139.6503 },
  };

  let target = cities["paris"];
  let cityName = "paris";
  for (const c in cities) {
    if (command.toLowerCase().includes(c)) {
      target = cities[c];
      cityName = c;
      break;
    }
  }

  // Move camera with tilt and zoom
  googleMap.moveCamera({
    center: target,
    zoom: 16.5,
    tilt: 55, // Incline la caméra à 55° (pour un bel effet 3D si les batiments sont activés)
    heading: 0,
  });

  // Start slow rotation
  mapRotationState.active = true;
  mapRotationState.heading = 0;
  cancelAnimationFrame(mapRotationState.raf);

  function rotateCamera() {
    if (!mapRotationState.active) return;
    mapRotationState.heading += 0.08;
    googleMap.moveCamera({
      heading: mapRotationState.heading,
    });
    mapRotationState.raf = requestAnimationFrame(rotateCamera);
  }
  rotateCamera();

  sysMsg(
    `📍 V-LOCK: ${cityName.toUpperCase()}. Initialisation du rendu topographique 3D...`,
  );
}

function showMap(command = "Verrouille Paris") {
  if (!mapInstance) return;
  document.getElementById("map-canvas").style.opacity = "0.35"; // Plus discret si la carte Google est derrière

  const bg = document.getElementById("gmap-bg");
  if (bg) bg.style.opacity = "1";

  mapInstance.start();
  STATE.mapActive = true;
  setContent(true);

  executeMapCommand(command);
}

function hideMap() {
  const el = document.getElementById("map-canvas");
  if (el) el.style.opacity = "0";

  const bg = document.getElementById("gmap-bg");
  if (bg) bg.style.opacity = "0";

  mapRotationState.active = false;
  cancelAnimationFrame(mapRotationState.raf);

  mapInstance?.stop();
  STATE.mapActive = false;
  checkContent();
}

// ── WAVEFORM ──────────────────────────────────────────
function initWaveform() {
  const c = document.getElementById("wave");
  if (!c) return;
  const cx = c.getContext("2d");
  c.width = 420;
  c.height = 44;
  let analyser = null,
    idle = 0;
  navigator.mediaDevices
    .getUserMedia({ audio: true, video: false })
    .then((st) => {
      const ac = new (window.AudioContext || window.webkitAudioContext)();
      const src = ac.createMediaStreamSource(st);
      analyser = ac.createAnalyser();
      analyser.fftSize = 128;
      src.connect(analyser);
    })
    .catch(() => {});
  (function draw() {
    requestAnimationFrame(draw);
    cx.clearRect(0, 0, c.width, c.height);
    const bars = 52,
      bw = c.width / bars - 1,
      cy = c.height / 2;
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
      cx.fillStyle = `rgba(${Math.floor(amp * 115)},${145 + Math.floor(amp * 110)},${205 + Math.floor(amp * 50)},${0.18 + amp * 0.72})`;
      cx.fillRect(i * (bw + 1), cy - h / 2, bw, h);
    }
    idle += 0.02;
  })();
}

// ── ORBE ÉTAT ─────────────────────────────────────────
function setContent(on) {
  STATE.contentOn = on;
  const w = document.getElementById("orb-wrap");
  if (!w) return;
  if (on) {
    w.classList.remove("orb-center");
    w.classList.add("orb-corner");
  } else {
    w.classList.remove("orb-corner");
    w.classList.add("orb-center");
  }
}
function checkContent() {
  const hasMsgs = document.querySelectorAll("#chat-zone .msg").length > 0;
  setContent(STATE.mapActive || STATE.camActive || hasMsgs);
}
function orbState(s) {
  const w = document.getElementById("orb-wrap");
  if (w) {
    w.classList.remove("s-listen", "s-speak", "s-think");
    if (s) w.classList.add("s-" + s);
  }
  const dot = document.getElementById("sb-dot");
  const txt = document.getElementById("sb-status");
  const map = {
    listen: ["dot", "EN ÉCOUTE"],
    speak: ["dot", "RÉPOND"],
    think: ["dot amber", "TRAITEMENT"],
  };
  const [dc, tc] = map[s] || [STATE.apiOk ? "dot" : "dot red", "EN ATTENTE"];
  if (dot) dot.className = dc;
  if (txt) txt.textContent = tc;
}

// ── STREAMING SSE (Mark-XXXIX) ────────────────────────
function initLiveStream() {
  const es = new EventSource("/api/events");
  es.onmessage = (e) => {
    const ev = JSON.parse(e.data);
    if (ev.type === "user") {
      addMsg(ev.text, "user");
      orbState("think");
      setContent(true);
    } else if (ev.type === "jarvis") {
      addMsg(ev.text, "jarvis", "system");
      orbState("speak");
      setTimeout(() => orbState("listen"), 4000);
    }
  };
  es.onerror = () => setTimeout(initLiveStream, 3000);
}

// ── SPEECH RECOGNITION FALLBACK (WEB INTERACTION) ─────────────────
let recognition = null;
let browserMuted = true;

function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.warn("Speech recognition not supported in this browser.");
    return;
  }
  recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = false;
  recognition.lang = "fr-FR";

  recognition.onstart = () => {
    browserMuted = false;
    updateMicStatusUI(true);
  };

  recognition.onresult = (event) => {
    const transcript = event.results[event.results.length - 1][0].transcript.trim();
    if (transcript) {
      send(transcript);
    }
  };

  recognition.onerror = (event) => {
    console.warn("[Web Speech] Error:", event.error);
    if (event.error === 'not-allowed') {
      sysMsg("Accès micro bloqué. Autorisez le microphone dans votre navigateur.");
      stopWebMic();
    }
  };

  recognition.onend = () => {
    if (!browserMuted) {
      try {
        recognition.start();
      } catch (e) {}
    } else {
      updateMicStatusUI(false);
    }
  };
}

function startWebMic() {
  browserMuted = false;
  STATE.listening = true;
  if (!recognition) {
    initSpeechRecognition();
  }
  if (recognition) {
    try {
      recognition.start();
    } catch (e) {}
  }
}

function stopWebMic() {
  browserMuted = true;
  STATE.listening = false;
  if (recognition) {
    try {
      recognition.stop();
    } catch(e) {}
  }
}

function updateMicStatusUI(active) {
  const m = document.getElementById("h-mic");
  if (active) {
    orbState("listen");
    if (m) {
      m.textContent = "ÉCOUTE";
      m.classList.add("ok");
      m.classList.remove("err");
    }
  } else {
    orbState();
    if (m) {
      m.textContent = "MUET";
      m.classList.remove("ok");
      m.classList.add("err");
    }
  }
}

function initStatusPolling() {
  setInterval(async () => {
    try {
      const r = await fetch("/api/status");
      const d = await r.json();
      const m = document.getElementById("h-mic");
      if (d.speaking) {
        orbState("speak");
      } else if (!d.muted) {
        orbState("listen");
        if (m) {
          m.textContent = "ÉCOUTE";
          m.classList.add("ok");
          m.classList.remove("err");
        }
      } else {
        orbState();
        if (m) {
          m.textContent = "MUET";
          m.classList.remove("ok");
          m.classList.add("err");
        }
      }
      STATE.listening = !d.muted;
      if (recognition && !browserMuted) {
        browserMuted = true;
        recognition.stop();
      }
    } catch (e) {
      // Server offline fallback: use browser-native status
      updateMicStatusUI(!browserMuted);
      STATE.listening = !browserMuted;
    }
  }, 600);
}

async function toggleMic() {
  try {
    const r = await fetch("/api/status");
    if (!r.ok) throw new Error("Offline");
    await fetch("/api/toggle-mute", { method: "POST" });
  } catch (e) {
    if (browserMuted) {
      startWebMic();
    } else {
      stopWebMic();
    }
  }
}

function stopMic() {
  fetch("/api/mute", { method: "POST" }).catch(() => {});
  stopWebMic();
}

function startMic() {
  fetch("/api/unmute", { method: "POST" }).catch(() => {});
  startWebMic();
}

// ── GESTION DES MESSAGES ────────────────────────────
function sysMsg(txt) {
  const z = document.getElementById("chat-zone");
  if (!z) return;
  const el = document.createElement("div");
  el.className = "sys-msg";
  el.textContent = txt;
  z.appendChild(el);
  z.scrollTop = z.scrollHeight;
  setTimeout(() => el.remove(), 8000);
}

function addMsg(txt, sender, mode = "") {
  const z = document.getElementById("chat-zone");
  if (!z) return;
  checkContent();
  const wrap = document.createElement("div");
  wrap.className = `msg m-${sender}`;

  const tags = {
    web_search: '<span class="mode-tag mt-web">OSINT</span>',
    deep_think: '<span class="mode-tag mt-deep">DEEP MODEL</span>',
    vision: '<span class="mode-tag mt-vision">VISION</span>',
    system: '<span class="mode-tag mt-exec">SYSTEM</span>',
  };
  const modeTag = mode && tags[mode] ? tags[mode] : "";

  const c = txt.replace(/</g, "&lt;").replace(/>/g, "&gt;");

  if (sender === "jarvis") {
    wrap.innerHTML = `<div class="msg-who">JARVIS</div>${modeTag}<div class="msg-body typing"></div>`;
    z.appendChild(wrap);
    let i = 0;
    const body = wrap.querySelector(".msg-body");
    const tid = setInterval(() => {
      body.innerHTML = c.slice(0, ++i);
      z.scrollTop = z.scrollHeight;
      if (i >= c.length) {
        body.classList.remove("typing");
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
    const r = await fetch("/api/health");
    const d = await r.json();
    STATE.apiOk = true;
    const api = document.getElementById("h-api");
    if (api) api.innerHTML = '<span class="dot"></span> EN LIGNE';
    const mod = document.getElementById("h-model");
    if (mod) mod.textContent = d.model || "GEMINI";
    refreshProviders();
    orbState(STATE.listening ? "listen" : "");
  } catch (e) {
    STATE.apiOk = false;
    const api = document.getElementById("h-api");
    if (api) api.innerHTML = '<span class="dot red"></span> HORS LIGNE';
    orbState();
  }
}

function sendTxt() {
  const el = document.getElementById("txt");
  if (!el || !el.value.trim()) return;
  send(el.value.trim());
  el.value = "";
}

function speakNatural(text) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utter = new window.SpeechSynthesisUtterance(
    text.replace(/[*_#`\[\]]/g, "").substring(0, 400),
  );
  utter.lang = "fr-FR";
  utter.rate = 1.05;
  utter.pitch = 0.9;

  const voices = window.speechSynthesis.getVoices();
  // Try to find a high quality French voice
  let voice = voices.find(
    (v) =>
      v.lang.includes("fr") &&
      (v.name.includes("Google") ||
        v.name.includes("Thomas") ||
        v.name.includes("Microsoft Paul")),
  );
  if (!voice) voice = voices.find((v) => v.lang.includes("fr"));
  if (voice) utter.voice = voice;

  window.speechSynthesis.speak(utter);
}

async function send(text) {
  if (!text) return;
  STATE.history.push(text);
  addMsg(text, "user");

  // Interception de commandes de caméra / carte locales
  const tLow = text.toLowerCase();

  if (
    tLow.includes("ouvre la caméra") ||
    tLow.includes("allume la caméra") ||
    tLow.includes("active la vision") ||
    tLow.includes("ouvre la camera")
  ) {
    setTimeout(() => {
      if (!STATE.camActive) showCam();
    }, 300);
    return;
  }
  if (
    tLow.includes("ferme la caméra") ||
    tLow.includes("éteins la caméra") ||
    tLow.includes("ferme la camera") ||
    tLow.includes("eteins la camera")
  ) {
    setTimeout(() => {
      if (STATE.camActive) hideCam();
    }, 300);
    return;
  }

  if (
    tLow.includes("verrouille") ||
    tLow.includes("affiche la carte") ||
    tLow.includes("lock on") ||
    tLow.includes("montre la carte")
  ) {
    setTimeout(() => {
      showMap(text);
    }, 400);
  } else if (
    tLow.includes("ferme la carte") ||
    tLow.includes("cache la carte")
  ) {
    setTimeout(() => {
      hideMap();
    }, 400);
  }

  orbState("think");
  const t0 = Date.now();

  try {
    const r = await fetch("/api/tool-chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const d = await r.json();
    STATE.latency = Date.now() - t0;
    const lat = document.getElementById("h-latency");
    if (lat) lat.textContent = STATE.latency + "ms";

    orbState("speak");
    setTimeout(() => {
      orbState(STATE.listening ? "listen" : "");
    }, 2000);

    // Direct autonomous fallback or OSINT report display
    if (d.type === "osint_report") {
      renderOsintReport(d);
    } else if (d.reply && d.reply !== "Message envoyé à JARVIS.") {
      try {
        const parsed = JSON.parse(d.reply);
        if (parsed && parsed.type === "osint_report") {
          renderOsintReport(parsed);
        } else if (parsed && parsed.action === "open_url") {
          window.open(parsed.url, "_blank");
          if (parsed.reply) {
            addMsg(parsed.reply, "jarvis");
            speakNatural(parsed.reply);
          }
        } else {
          addMsg(d.reply, "jarvis");
          speakNatural(d.reply);
        }
      } catch (e) {
        addMsg(d.reply, "jarvis");
        speakNatural(d.reply);
      }
    }

    let modeUsed = d.mode_used || "";
    if (d.action) {
      modeUsed = "system";
      if (d.action.type === "open_url" || d.action.action === "open_url") {
        window.open(d.action.url, "_blank");
      } else if (
        d.action.command === "camera" ||
        d.action.command === "vision" ||
        d.action.command === "caméra" ||
        d.action.command === "video"
      ) {
        toggleCam();
      } else if (d.action.command === "screen") {
        sysMsg("Capture écran non dispo sans https.");
      }
    }

    // Everything else is handled by the SSE livestream and Gemini Live Audio!
  } catch (e) {
    orbState();
    addMsg("Erreur de communication avec le noyau central.", "jarvis");
  }
}

function renderOsintReport(report) {
  const z = document.getElementById("chat-zone");
  if (!z) return;
  checkContent();
  const wrap = document.createElement("div");
  wrap.className = `msg m-jarvis osint-msg`;

  let html = `<div class="msg-who">JARVIS</div><span class="mode-tag mt-exec">OSINT REPORT</span>
    <div class="osint-container" style="background: rgba(0, 20, 40, 0.6); border: 1px solid #00e5ff; border-radius: 4px; padding: 12px; margin-top: 8px;">
      <h3 style="color: #00e5ff; margin-top: 0; font-family: 'Share Tech Mono', monospace; font-size: 14px;">[ ${report.title ? report.title.toUpperCase() : "RAPPORT OSINT"} ]</h3>
      <p style="color: #a0c0e0; font-size: 13px; margin-bottom: 12px;">${report.summary || "Scan terminé."}</p>
      <div style="display: flex; flex-direction: column; gap: 8px;">`;

  if (report.data && report.data.length) {
    report.data.forEach((item) => {
      html += `
        <div style="background: rgba(0,0,0,0.4); border-left: 2px solid #00e5ff; padding: 6px 10px;">
          <strong style="color: #4dfa9f; font-size: 11px;">>_ ${item.source ? item.source.toUpperCase() : "SOURCE"}</strong>
          <div style="color: #d4e8ff; font-family: 'Share Tech Mono', monospace; font-size: 12px; margin-top: 4px;">${item.info || "Aucune information."}</div>
        </div>
      `;
    });
  } else {
    html += `
        <div style="background: rgba(0,0,0,0.4); border-left: 2px solid #00e5ff; padding: 6px 10px;">
          <strong style="color: #4dfa9f; font-size: 11px;">>_ SYSTÈME</strong>
          <div style="color: #d4e8ff; font-family: 'Share Tech Mono', monospace; font-size: 12px; margin-top: 4px;">Aucune donnée critique identifiée pour cette requête.</div>
        </div>
      `;
  }

  html += `</div>`;

  if (report.downloadable) {
    html += `<button class="osint-export-btn" style="margin-top: 12px; background: rgba(0,229,255,0.1); border: 1px solid #00e5ff; color: #00e5ff; padding: 6px 12px; cursor: pointer; font-family: 'Share Tech Mono'; font-size: 11px;">[ EXPORTER ${report.file_format.toUpperCase()} ]</button>`;
  }

  html += `</div>`;
  wrap.innerHTML = html;
  z.appendChild(wrap);

  if (report.downloadable) {
    const btn = wrap.querySelector(".osint-export-btn");
    if (btn) {
      btn.onclick = () => {
        const textData =
          `===== ${report.title} =====\nDate: ${new Date().toISOString()}\n\n${report.summary}\n\n[ DONNÉES ]\n` +
          (report.data || [])
            .map((d) => `> ${d.source}\n${d.info}`)
            .join("\n\n");
        const blob = new Blob([textData], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `jarvis_osint_${Date.now()}.${report.file_format}`;
        a.click();
        URL.revokeObjectURL(url);
      };
    }
  }

  z.scrollTop = z.scrollHeight;
  speakNatural("Analyse terminée. Rapport structuré affiché.");
}

// ── UTILS ET INTERACTIONS ────────────────────────────
function initKeys() {
  window.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT") {
      if (e.code === "Enter") sendTxt();
      return;
    }
    if (e.code === "Space") {
      e.preventDefault();
      toggleMic();
    }
    if (e.code === "KeyC") toggleCam();
    if (e.code === "KeyN") {
      if (STATE.mapActive) hideMap();
      else showMap();
    }
    if (e.code === "Escape") {
      stopMic();
      if ("speechSynthesis" in window) window.speechSynthesis.cancel();
      hideMap();
      hideCam();
    }
  });
}

const TOOLS = [
  {
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>`,
    label: "Recherche Web",
    cmd: "Cherche sur internet ",
  },
  {
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2"></path><path d="M12 20v2"></path><path d="m4.93 4.93 1.41 1.41"></path><path d="m17.66 17.66 1.41 1.41"></path><path d="M2 12h2"></path><path d="M20 12h2"></path><path d="m6.34 17.66-1.41 1.41"></path><path d="m19.07 4.93-1.41 1.41"></path></svg>`,
    label: "Météo Locale",
    cmd: "Quel temps fait-il actuellement ?",
  },
  {
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>`,
    label: "Réseau Info",
    cmd: "Quel est mon statut réseau ?",
  },
  {
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"></path><circle cx="12" cy="13" r="3"></circle></svg>`,
    label: "Vision Cam",
    cmd: null,
    fn: () => {
      toggleCam();
    },
  },
  {
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line></svg>`,
    label: "Scanner Carte",
    cmd: null,
    fn: () => {
      showMap();
      setTimeout(hideMap, 6000);
    },
  },
  {
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"></rect><line x1="9" x2="15" y1="9" y2="9"></line><line x1="9" x2="15" y1="15" y2="15"></line></svg>`,
    label: "OSINT MODE",
    cmd: "Lance une recherche OSINT sur ",
  },
];

function initTools() {
  const g = document.getElementById("tools-grid");
  if (!g) return;
  TOOLS.forEach((t) => {
    const btn = document.createElement("button");
    btn.className = "tool-btn";
    btn.innerHTML = `<span class="tool-icon">${t.icon}</span>${t.label}`;
    btn.onclick = () => {
      toggleTools();
      if (t.fn) {
        t.fn();
        return;
      }
      if (t.cmd) {
        if (t.cmd.endsWith(" ")) {
          const i = document.getElementById("txt");
          if (i) {
            i.value = t.cmd;
            i.focus();
          }
        } else send(t.cmd);
      }
    };
    g.appendChild(btn);
  });
}

function toggleTools() {
  const p = document.getElementById("tools-panel");
  if (p) p.style.display = p.style.display === "block" ? "none" : "block";
}

function toggleModelPanel() {
  const p = document.getElementById("model-panel");
  if (p) p.style.display = p.style.display === "block" ? "none" : "block";
}

async function refreshProviders() {
  try {
    const r = await fetch("/api/providers");
    const d = await r.json();
    const l = document.getElementById("mp-list");
    if (l && d.providers) {
      l.innerHTML = "";
      d.providers.forEach((p) => {
        const div = document.createElement("div");
        div.className = "mp-item";
        div.innerHTML = `<span>${p.name}</span> <span class="mp-badge bg-free">ACTIF</span>`;
        if (p.id) div.onclick = () => setProvider(p.id);
        l.appendChild(div);
      });
    }
    const o = document.getElementById("mp-ollama");
    if (o && d.ollama_models && d.ollama_models.length) {
      o.innerHTML = d.ollama_models
        .map(
          (m) =>
            `<div class="mp-item" onclick="setProvider('local')">${m}</div>`,
        )
        .join("");
    }
  } catch (e) {}
}

function setProvider(id) {
  fetch("/api/set-provider", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider_id: id }),
  });
  toggleModelPanel();
  checkApi();
}

function toggleCam() {
  STATE.camActive ? hideCam() : showCam();
}
function showCam() {
  navigator.mediaDevices
    .getUserMedia({ video: true })
    .then((s) => {
      const v = document.getElementById("cam-video");
      const p = document.getElementById("cam-panel");
      if (v) v.srcObject = s;
      if (p) p.classList.add("on");
      STATE.camActive = true;
      const hcam = document.getElementById("h-cam");
      if (hcam) {
        hcam.textContent = "ON";
        hcam.className = "hv ok";
      }
      setContent(true);
    })
    .catch(() => sysMsg("Caméra bloquée ou absente."));
}
function hideCam() {
  const v = document.getElementById("cam-video");
  const p = document.getElementById("cam-panel");
  if (v && v.srcObject) v.srcObject.getTracks().forEach((t) => t.stop());
  if (p) p.classList.remove("on");
  STATE.camActive = false;
  const hcam = document.getElementById("h-cam");
  if (hcam) {
    hcam.textContent = "OFF";
    hcam.className = "hv";
  }
  checkContent();
}

function updateSysCpu() {
  const c = document.getElementById("h-cpu");
  if (c) c.textContent = (Math.random() * 12 + 2).toFixed(1) + "%";
}

// Exposés globaux pour inline event handlers html
window.sendTxt = sendTxt;
window.toggleTools = toggleTools;
window.toggleModelPanel = toggleModelPanel;
window.toggleCam = toggleCam;
window.toggleMic = toggleMic;
window.setProvider = setProvider;
