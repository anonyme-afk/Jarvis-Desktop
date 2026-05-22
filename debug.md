## ERREUR 1 — Le serveur Python ne démarre pas

**Symptômes** : L'interface Electron s'ouvre mais l'API status affiche "HORS LIGNE"

**Causes et solutions** :
```bash
# Vérifier que Python est installé
python --version
# ou sur Mac/Linux
python3 --version

# Vérifier que les dépendances sont installées
pip install -r python/requirements.txt
# Sur Mac/Linux si erreur de permissions :
pip3 install -r python/requirements.txt --user

# Tester le serveur manuellement AVANT de lancer Electron
cd python
python server.py
# Si tu vois "[JARVIS] Serveur Python démarré sur port 5001" → OK
# Sinon, note l'erreur exacte et cherche-la ci-dessous

# Tester que le serveur répond
curl http://localhost:5001/health
# Doit retourner : {"status":"ok","model":"gemini-1.5-pro"}
```

**Erreur fréquente — Port déjà utilisé** :
```bash
# Windows
netstat -ano | findstr :5001
taskkill /PID [LE_PID] /F

# Mac/Linux
lsof -i :5001
kill -9 [LE_PID]
```

---

## ERREUR 2 — Clé API Gemini invalide ou manquante

**Symptômes** : Le serveur démarre mais répond "Erreur 400" ou "API key not valid"

**Solution** :
```bash
# 1. Vérifie que le fichier .env existe (pas juste .env.example)
ls -la | grep .env

# 2. Vérifie le contenu
cat .env
# Doit contenir : GEMINI_API_KEY=AIza...

# 3. Si la clé commence par "AIza" et fait ~40 chars → format OK
# Si tu as collé des espaces ou des guillemets → ça casse tout

# Dans .env : CORRECT ✓
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Dans .env : INCORRECT ✗
GEMINI_API_KEY="AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
GEMINI_API_KEY = AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Obtenir une clé gratuite** :
```
1. Va sur https://aistudio.google.com
2. Clique sur "Get API Key" dans le menu gauche
3. "Create API key" → choisir un projet Google
4. Copie la clé → colle dans .env
```

---

## ERREUR 3 — PyAudio / microphone ne fonctionne pas

**Symptômes** : `pip install pyaudio` échoue ou la reconnaissance vocale ne démarre pas

**Windows** :
```bash
# PyAudio a besoin de Visual C++ Build Tools
# Méthode la plus simple : utiliser le wheel précompilé
pip install pipwin
pipwin install pyaudio
```

**Mac** :
```bash
brew install portaudio
pip install pyaudio
```

**Linux** :
```bash
sudo apt-get install python3-pyaudio portaudio19-dev
pip install pyaudio
```

**Alternative si PyAudio reste bloqué** :
```python
# Dans server.py, remplace la route /transcribe par cette version
# qui utilise le micro du navigateur (Web Speech API) au lieu de Python
# → Aucune dépendance PyAudio nécessaire
# La reconnaissance vocale se fait côté renderer.js avec
# window.SpeechRecognition (déjà intégrée dans renderer.js)
```

---

## ERREUR 4 — Electron refuse de lancer (erreur CORS ou CSP)

**Symptômes** : Console Electron affiche "Refused to connect" ou "CORS error"

**Solution dans main.js** :
```javascript
// Ajouter dans la création de la BrowserWindow :
webPreferences: {
  preload: path.join(__dirname, 'preload.js'),
  contextIsolation: true,
  nodeIntegration: false,
  // Ajouter cette ligne :
  webSecurity: false  // Seulement en développement local
}

// ET dans app.whenReady() :
app.commandLine.appendSwitch('disable-web-security');
```

---

## ERREUR 5 — La webcam ne s'active pas dans Electron

**Symptômes** : `getUserMedia` retourne une erreur de permission

**Solution dans main.js** :
```javascript
// Ajouter CE handler AVANT app.whenReady() :
app.on('ready', () => {
  // Donner les permissions caméra/micro à l'app Electron
  session.defaultSession.setPermissionRequestHandler(
    (webContents, permission, callback) => {
      const allowed = ['media', 'microphone', 'camera', 'audioCapture', 'videoCapture'];
      callback(allowed.includes(permission));
    }
  );
});

// Ajouter l'import en haut du fichier :
const { app, BrowserWindow, ipcMain, session } = require('electron');
```

---

## ERREUR 6 — "Module not found" sur un import Python

**Symptômes** : `ModuleNotFoundError: No module named 'flask'` ou autre

```bash
# Vérifier QUEL Python est utilisé par Electron
# Dans main.js, change temporairement :
pythonProcess = spawn('python', ['--version'], {});
pythonProcess.stdout.on('data', d => console.log('Python:', d.toString()));

# Si Electron utilise python2 au lieu de python3 :
# Changer dans main.js :
const pythonExecutable = 'python3'; // forcer python3

# Ou utiliser le chemin absolu :
const pythonExecutable = '/usr/bin/python3'; // Mac/Linux
const pythonExecutable = 'C:\\Python311\\python.exe'; // Windows
```

---

## ERREUR 7 — L'IPC ne répond pas (ipcMain/ipcRenderer)

**Symptômes** : `window.jarvis.sendMessage` ne répond jamais, promesse qui hang

**Checklist** :
```javascript
// 1. Vérifier que preload.js est bien chargé
// Dans main.js, BrowserWindow options :
webPreferences: {
  preload: path.join(__dirname, 'preload.js'), // ← chemin correct ?
}

// 2. Vérifier que le canal IPC correspond exactement
// preload.js : ipcRenderer.invoke('send-message', ...)
// main.js :    ipcMain.handle('send-message', ...) ← même nom ?

// 3. Tester l'IPC de base (ajoute dans main.js) :
ipcMain.handle('ping', () => 'pong');
// Et dans renderer.js :
const r = await window.jarvis.ping?.();
console.log('IPC test:', r); // Doit afficher "pong"
```

---

## ERREUR 8 — Mauvaise taille de l'orbe ou layout cassé

**Symptômes** : L'orbe déborde, les panneaux HUD se chevauchent

```css
/* Ajouter dans style.css pour déboguer le layout : */
* { outline: 1px solid red !important; }
/* → Retire cette ligne une fois le problème identifié */

/* Fix common : s'assurer que body est bien en position fixed */
html, body {
  margin: 0;
  padding: 0;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}
```

---

## ERREUR 9 — Ollama (mode local) ne répond pas

**Symptômes** : `USE_LOCAL_MODEL=True` mais JARVIS ne répond plus

```bash
# 1. Vérifier qu'Ollama est bien lancé
ollama list
# Doit afficher les modèles installés

# 2. Tester Ollama directement
curl http://localhost:11434/api/generate \
  -d '{"model":"llama3.2","prompt":"hello","stream":false}'

# 3. Installer un modèle si absent
ollama pull llama3.2          # ~2GB, bon pour les vieux PC
ollama pull qwen2.5:7b        # Meilleur mais plus lourd

# 4. Pour la vision locale
ollama pull llava             # Modèle vision local (~4GB)
```

**Dans server.py — Switch Ollama/Gemini** :
```python
USE_LOCAL_MODEL = os.environ.get('USE_LOCAL_MODEL', 'false').lower() == 'true'

def get_ai_response(messages):
    if USE_LOCAL_MODEL:
        try:
            import requests
            r = requests.post('http://localhost:11434/api/chat', json={
                'model': os.environ.get('OLLAMA_MODEL', 'llama3.2'),
                'messages': messages,
                'stream': False
            }, timeout=30)
            return r.json()['message']['content']
        except Exception as e:
            print(f'[Ollama] Fallback vers Gemini : {e}')
            # Fallback automatique vers Gemini
            return get_gemini_response(messages)
    else:
        return get_gemini_response(messages)
```

---

## ERREUR 10 — L'app ne se lance pas sur Windows (erreur VCRUNTIME)

**Symptômes** : Double-clic sur l'exe → rien ou erreur DLL manquante

```
Solution : Installer Visual C++ Redistributable
→ https://aka.ms/vs/17/release/vc_redist.x64.exe

Et vérifier Node.js version :
node --version  # Doit être v18 ou v20 (LTS)
npm --version   # Doit être v9 ou v10
```
