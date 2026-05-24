# JARVIS Desktop

Interface holographique style Iron Man — Vision, IA, OSINT, Gaming.
Fonctionne sur **Windows, Mac et Linux**. Même les vieux PC.

## Installation en 3 clics

### 1. Cloner
```bash
git clone https://github.com/anonyme-afk/Jarvis-Desktop.git
cd Jarvis-Desktop
```

### 2. Installer
Double-clique sur **`INSTALL.bat`**
*(ou dans le terminal : `INSTALL.bat`)*

### 3. Configurer la clé API (gratuite)
- Va sur **https://aistudio.google.com**
- Clique **Get API Key** → **Create API Key**
- Ouvre le fichier **`.env`** et colle :
```
GEMINI_API_KEY=ta_clé_ici
```

### 4. Lancer
Double-clique sur **`START_JARVIS.bat`**
Puis ouvre **http://localhost:3000**

---

## Commandes vocales

| Commande | Action |
|---|---|
| "JARVIS, cherche [sujet]" | Recherche web |
| "JARVIS, quel temps à [ville]" | Météo |
| "JARVIS, infos système" | CPU/RAM/Disque |
| "JARVIS, qu'est-ce que tu vois ?" | Analyse webcam |
| "JARVIS, IP de 8.8.8.8" | Géolocalisation IP |
| "JARVIS, [question]" | Réponse IA |

## Raccourcis clavier

| Touche | Action |
|---|---|
| **ESPACE** | Activer/désactiver le micro |
| **C** | Activer/désactiver la caméra |
| **ECHAP** | Couper JARVIS |
| **MODÈLE** (haut droite) | Changer de modèle IA |
| **CMD** (bas gauche) | Panneau d'outils |

---

## Modèles IA supportés

**Gratuits (aucune carte bancaire) :**
- Gemini 3.5 Flash ← **Défaut recommandé**
- Gemini 3.1 Pro
- Groq Llama 4 Scout (ultra-rapide)
- Groq Llama 3.3 70B
- OpenRouter : Llama 4, DeepSeek R1, Qwen VL (via clé OpenRouter)

**Payants :**
- Claude Sonnet/Opus/Haiku (Anthropic)
- GPT-4o, GPT-4o Mini (OpenAI)
- Grok 3 (xAI)
- DeepSeek V3/R1
- Gemini 2.5 Pro/Flash

---

## Dépannage

**JARVIS ne répond pas**
→ Vérifier que la fenêtre "JARVIS-Flask" est ouverte (CMD noir)
→ Elle doit afficher : `[JARVIS] v3.1 démarré`

**Micro ne fonctionne pas**
→ Paramètres Windows → Confidentialité → Microphone → Autoriser

**Erreur "model not found"**
→ La clé Gemini est invalide ou vide dans `.env`
→ Vérifier sur https://aistudio.google.com

**Port 5001 occupé**
→ Redémarre le PC

**Erreur dlib ou face_recognition**
→ Normal, ces modules sont optionnels. JARVIS fonctionne sans.

**PyAudio manquant (Windows)**
```
pip install pipwin
pipwin install pyaudio
```

---

## Structure

```
Jarvis-Desktop/
├── INSTALL.bat          ← Installation automatique
├── START_JARVIS.bat     ← Lancement (double-clique)
├── .env                 ← Tes clés API (ne jamais commit)
├── .env.example         ← Modèle de configuration
├── index.html           ← Interface principale
├── renderer.js          ← Logique frontend
├── style.css            ← Styles HUD
├── server.ts            ← Serveur Node.js/Express
├── vite.config.ts       ← Config build
└── jarvis/
    └── python/
        ├── server.py    ← Serveur Flask + IA
        ├── providers.py ← 30+ modèles IA
        ├── memory.py    ← Mémoire persistante
        ├── osint_engine.py
        ├── vision_engine.py
        └── tools/
```

## Licence
MIT — Libre d'utilisation et de modification.
