# JARVIS Desktop V2

## Installation rapide

1. Cloner le projet :
   `git clone https://github.com/TON_USERNAME/jarvis-desktop`
   `cd jarvis-desktop`

2. Installer les dépendances Node.js :
   `npm install`

3. Installer les dépendances Python :
   `pip install -r python/requirements.txt`

4. Configurer la clé API :
   - Copier `.env.example` → `.env`
   - Aller sur aistudio.google.com → Get API Key
   - Coller la clé dans `.env`
   - *Optionnel* : pour utiliser Ollama localement, définir `USE_LOCAL_MODEL=true` dans `.env`

5. Lancer JARVIS :
   `npm start`

## Fonctionnalités
- HUD holographique et orbite (mode plein écran puis discret)
- Transcription Vocale (Espace pour parler)
- Modèle Dual : Utilisation de l'API Gemini ou de Ollama local
- Vision (Touche C pour la Caméra, Touche S pour analyser l'écran)
- Exécution de commandes et ouverture d'URLs

## Aide UI :
- `M` pour afficher la carte réseau Constellation
- `Espace` pour démarrer/stopper la reconnaissance vocale
- `C` pour lancer la vision Caméra
- `S` pour analyser l'écran (Screenshot et analyse via Gemini 1.5 Pro)
