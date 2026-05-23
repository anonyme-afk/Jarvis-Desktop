"""
Script de vérification et débogage automatique de JARVIS v3.0
Lance avec : python verify_and_debug.py
"""
import sys, os, subprocess, json

sys.path.insert(0, os.path.dirname(__file__))

CHECKS = []
ERRORS = []
WARNINGS = []

def check(name, fn):
    try:
        result = fn()
        status = "✅" if result else "⚠️"
        CHECKS.append(f"{status} {name}")
        if not result:
            WARNINGS.append(name)
    except Exception as e:
        CHECKS.append(f"❌ {name}: {e}")
        ERRORS.append(f"{name}: {e}")

print("\n🤖 JARVIS v3.0 — Vérification complète\n" + "="*50)

# ---- PYTHON ----
check("Python 3.10+", lambda: sys.version_info >= (3, 10))
check("pip disponible", lambda: subprocess.run([sys.executable,"-m","pip","--version"],
    capture_output=True).returncode == 0)

# ---- FICHIERS CRITIQUES ----
BASE = os.path.dirname(__file__)
critical_files = [
    "server.py","providers.py","memory.py","requirements.txt",
    "tools/tool_registry.py","tools/search_tool.py",
    "plugins/__init__.py"
]
for f in critical_files:
    check(f"Fichier {f}", lambda fp=f: os.path.exists(os.path.join(BASE, fp)))

# ---- .env ----
env_path = os.path.join(BASE, '..', '.env')
check(".env existe", lambda: os.path.exists(env_path))
if os.path.exists(env_path):
    from dotenv import load_dotenv
    load_dotenv(env_path)
    check("GEMINI_API_KEY définie", lambda: bool(os.environ.get('GEMINI_API_KEY')))

# ---- MODULES PYTHON CRITIQUES ----
critical_modules = ["flask","flask_cors","requests","dotenv","cv2","pyttsx3","pyaudio"]
for mod in critical_modules:
    check(f"Module {mod}", lambda m=mod: __import__(m) or True)

# ---- MODULES OPTIONNELS ----
optional_modules = {
    "ultralytics":     "YOLOv8 (détection objets)",
    "mediapipe":       "MediaPipe (gestes)",
    "face_recognition":"Reconnaissance faciale",
    "mem0":            "Mem0 (mémoire avancée)",
    "chromadb":        "ChromaDB (mémoire vectorielle)",
    "apprise":         "Notifications (Discord/Telegram)",
    "apscheduler":     "Planificateur de tâches",
    "pydirectinput":   "Gaming (DirectInput)",
    "browser_use":     "Navigation web autonome",
    "speedtest":       "Test vitesse internet",
    "nfc":             "NFC (lecteur USB requis)",
    "torch":           "PyTorch (VAD Silero)",
    "whois":           "WHOIS domaines",
    "duckduckgo_search":"Recherche web (gratuit)"
}
for mod, desc in optional_modules.items():
    try:
        __import__(mod)
        CHECKS.append(f"  ✅ {desc}")
    except ImportError:
        CHECKS.append(f"  ⚪ {desc} (optionnel)")

# ---- SERVEUR PYTHON ----
import threading, time
server_ok = False
def _start_server():
    subprocess.run([sys.executable, os.path.join(BASE,"server.py")],
        capture_output=True, timeout=5)

try:
    t = threading.Thread(target=_start_server, daemon=True)
    t.start()
    time.sleep(2)
    import requests as req
    r = req.get("http://localhost:5001/health", timeout=3)
    server_ok = r.status_code == 200
    check("Serveur Flask démarre et répond", lambda: server_ok)
    if server_ok:
        data = r.json()
        CHECKS.append(f"  ✅ Provider actif: {data.get('provider','?')}")
        CHECKS.append(f"  ✅ Backend mémoire: {data.get('services',{}).get('mem0','?')}")
except Exception as e:
    check("Serveur Flask", lambda: False)
    ERRORS.append(f"Serveur: {e}")

# ---- NODE.JS / ELECTRON ----
check("Node.js disponible", lambda: subprocess.run(["node","--version"],
    capture_output=True).returncode == 0)
check("npm disponible", lambda: subprocess.run(["npm","--version"],
    capture_output=True).returncode == 0)
check("package.json existe", lambda: os.path.exists(os.path.join(BASE,"..","package.json")))
node_modules = os.path.join(BASE, "..", "node_modules")
check("node_modules installés", lambda: os.path.exists(node_modules))

# ---- RAPPORT FINAL ----
print("\n📋 RÉSULTATS:\n")
for c in CHECKS:
    print(f"  {c}")

print(f"\n{'='*50}")
if ERRORS:
    print(f"\n❌ {len(ERRORS)} ERREUR(S) CRITIQUE(S):")
    for e in ERRORS:
        print(f"  → {e}")
    print("\n💡 CORRECTIONS:")
    if any("flask" in e for e in ERRORS):
        print("  pip install -r python/requirements.txt")
    if any("GEMINI" in e for e in ERRORS):
        print("  Édite .env et ajoute GEMINI_API_KEY=ta_clé")
        print("  Clé gratuite : https://aistudio.google.com")
    if any("node_modules" in e for e in ERRORS):
        print("  cd .. && npm install")
else:
    print("\n✅ TOUT EST OK — Lance JARVIS avec : npm start")

if WARNINGS:
    print(f"\n⚠️ {len(WARNINGS)} avertissement(s) (modules optionnels manquants)")
    print("  pip install -r python/requirements.txt  pour tout installer")

print()
