# JARVIS Desktop Assistant

Interface holographique style Iron Man, propulsée par Gemini 1.5 Pro (cloud)
ou Ollama (local). Fonctionne sur Windows, Mac et Linux.

## Stack technique
- Electron 28 (interface desktop)
- Python 3.10+ avec Flask (backend IA)
- Google Gemini 1.5 Pro via API (ou Ollama en local)
- Web Speech API (reconnaissance vocale navigateur)
- OpenCV (vision webcam)

## Installation

### Prérequis
- Node.js v18 ou v20 : https://nodejs.org
- Python 3.10+ : https://python.org
- Git : https://git-scm.com

### Étapes

1. Cloner le dépôt
   git clone https://github.com/TON_USERNAME/jarvis-desktop.git
   cd jarvis-desktop

2. Installer les dépendances Node
   npm install

3. Installer les dépendances Python
   pip install -r python/requirements.txt

   Sur Mac si erreur portaudio :
   brew install portaudio && pip install pyaudio

   Sur Windows si erreur PyAudio :
   pip install pipwin && pipwin install pyaudio

4. Configurer la clé API
   Copier .env.example → .env
   Remplacer "ta_cle_ici" par ta vraie clé Gemini
   Obtenir une clé gratuite sur : https://aistudio.google.com

5. Lancer JARVIS
   npm start

## Mode IA locale (optionnel, pour fonctionner sans internet)

1. Installer Ollama : https://ollama.com
2. Télécharger un modèle :
   ollama pull llama3.2
3. Dans .env, ajouter :
   USE_LOCAL_MODEL=true
   OLLAMA_MODEL=llama3.2
4. Relancer avec npm start
   → Fallback automatique vers Gemini si Ollama est indisponible

## Commandes vocales disponibles
- "JARVIS, ouvre Google Maps"
- "JARVIS, montre-moi [ville/pays]"
- "JARVIS, qu'est-ce que tu vois ?" (active la webcam)
- "JARVIS, [n'importe quelle question]"

## Raccourcis clavier
- ESPACE : activer/désactiver le micro
- C : activer/désactiver la caméra
- M : afficher la carte réseau
- S : analyser l'écran

## Structure du projet
jarvis-desktop/
├── main.js              Process principal Electron
├── preload.js           Bridge IPC sécurisé
├── package.json         Config npm + Electron
├── .env                 Clé API (ne jamais commit !)
├── .gitignore           Exclut .env et node_modules
├── renderer/
│   ├── index.html       Interface principale
│   ├── style.css        Styles + animations
│   └── renderer.js      Logique frontend
├── python/
│   ├── server.py        Backend Flask + IA
│   ├── requirements.txt Dépendances Python
│   └── tts.py           Synthèse vocale
└── assets/
    └── icon.png         Icône application

## Variables d'environnement (.env)
GEMINI_API_KEY=ta_clé_gemini
USE_LOCAL_MODEL=false
OLLAMA_MODEL=llama3.2

## Contribuer
Les PR sont les bienvenues. Fork → branche → PR.

## Licence
MIT — Libre d'utilisation, modification et distribution.
