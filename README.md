# JARVIS Desktop v3.0

Assistant IA holographique style Iron Man.
Vision, OSINT, Gaming, NFC, Mémoire, Domotique, Navigation web autonome.
Fonctionne sur Windows, Mac et Linux. Même les vieux PC.

**Lien du site preview (GitHub) :** [https://github.com/anonyme-afk/Jarvis-Desktop](https://github.com/anonyme-afk/Jarvis-Desktop)
**Aperçu Web AI Studio :** [https://ais-pre-hzhw3abu2vanfcaj65gfij-114166625783.europe-west2.run.app](https://ais-pre-hzhw3abu2vanfcaj65gfij-114166625783.europe-west2.run.app)

## Ce que JARVIS peut faire

### IA & Recherche
- Répond à n'importe quelle question (10 providers IA supportés)
- Recherche web en temps réel (DuckDuckGo, gratuit)
- Briefing météo sans clé API (wttr.in)
- Résumés Wikipedia instantanés
- Navigation web autonome (browser-use)

### Vision
- Voit via la webcam (YOLOv8 — reconnaît 80+ objets)
- Reconnaît ton visage et te salue automatiquement
- Détecte les intrus et envoie une alerte
- Détecte les gestes de la main (MediaPipe)
    - Index levé → volume +
    - Main ouverte → pause
    - Poing → mute

### OSINT (Sources Ouvertes)
- Géolocalisation d'une IP
- WHOIS d'un domaine
- Vérification d'email compromis (HIBP)
- Recherche de pseudo sur 7 plateformes
- DNS lookup
- Scan de ports
- Extraction de métadonnées EXIF

### Gaming
- Analyse ton écran de jeu en direct
- Contrôle clavier/souris via signaux matériels (DirectX)
- Mode farm automatique

### Système
- Infos CPU/RAM/Disque/Batterie en temps réel
- Test vitesse internet
- Screenshot et analyse
- Ouvrir des applications
- Taper du texte automatiquement

### Mémoire
- Mémorise tes préférences et habitudes (Mem0 + ChromaDB)
- Contexte persistant entre les sessions
- Se souvient de "je préfère Python" 2 semaines plus tard

### Proactivité
- Briefing matinal automatique à 7h
- Alerte si CPU/RAM > 90%
- Rappels vocaux planifiés

### Notifications
- Discord, Telegram, Gotify
- Alertes urgentes pour intrusions

### NFC (avec lecteur USB ~10€)
- Déverrouillage par badge
- Profils instantanés (Mode Code, Mode Gaming, etc.)

## Installation

### 1. Prérequis
- Node.js v18+ : https://nodejs.org
- Python 3.10+ : https://python.org
- Git : https://git-scm.com

### 2. Cloner
```bash
git clone https://github.com/anonyme-afk/Jarvis-Desktop.git
cd Jarvis-Desktop
```

### 3. Dépendances Node
```bash
npm install
```

### 4. Dépendances Python
```bash
pip install -r python/requirements.txt
```

Problèmes courants :
- PyAudio Windows : `pip install pipwin && pipwin install pyaudio`
- PyAudio Mac : `brew install portaudio && pip install pyaudio`
- face_recognition : `pip install cmake && pip install face_recognition`

### 5. Configurer
```bash
cp .env.example .env
# Édite .env et mets au moins GEMINI_API_KEY
# Clé gratuite sur : https://aistudio.google.com
```

### 6. Lancer
```bash
npm start
```

## Commandes vocales

| Commande | Action |
|---|---|
| "JARVIS, cherche [sujet]" | Recherche web DuckDuckGo |
| "JARVIS, qu'est-ce que tu vois ?" | Analyse webcam |
| "JARVIS, qui est là ?" | Reconnaissance faciale |
| "JARVIS, IP de 8.8.8.8" | Géolocalisation IP |
| "JARVIS, infos sur le pseudo [nom]" | Recherche OSINT |
| "JARVIS, infos système" | CPU/RAM/Disque |
| "JARVIS, quel temps à [ville]" | Météo |
| "JARVIS, rappelle-moi dans 10 min de [tâche]" | Rappel |
| "JARVIS, analyse le jeu" | Screenshot + analyse IA |
| "JARVIS, va sur [site] et [tâche]" | Navigation autonome |

## Raccourcis clavier

| Touche | Action |
|---|---|
| ESPACE | Activer/désactiver le micro |
| C | Activer/désactiver la caméra |
| N | Afficher/masquer la carte réseau |
| ⚡ (bouton bas gauche) | Panneau d'outils |
| ⚙ (bouton haut droit) | Changer de modèle IA |

## Structure du projet

```
Jarvis-Desktop/
├── index.html              Interface principale
├── style.css               Styles + animations HUD
├── renderer.js             Logique frontend
├── main.js                 Process Electron
├── preload.js              Bridge IPC sécurisé
├── package.json
├── .env                    Clés API (ne jamais commit)
├── .gitignore
├── python/
│   ├── server.py           Serveur principal v3.0
│   ├── providers.py        Multi-API (10 providers)
│   ├── memory.py           Mémoire basique
│   ├── mem0_manager.py     Mémoire avancée (Mem0/ChromaDB)
│   ├── osint_engine.py     Outils OSINT
│   ├── vision_engine.py    Vision (YOLO/MediaPipe/FaceRec)
│   ├── gaming_controller.py Contrôle gaming
│   ├── browser_agent.py    Navigation autonome
│   ├── nfc_manager.py      Gestion NFC
│   ├── notifier.py         Notifications (Discord/Telegram)
│   ├── scheduler.py        Tâches autonomes
│   ├── vad_manager.py      Détection vocale (interruption)
│   ├── requirements.txt
│   ├── faces/              Photos pour reconnaissance faciale
│   ├── tools/
│   │   ├── search_tool.py  Recherche web
│   │   └── tool_registry.py Registre des outils
│   └── plugins/
│       ├── phone_plugin.py  Contrôle Android (ADB)
│       └── browser_plugin.py Navigation basique
└── debug.md                Guide de débogage
```

## Ajouter un outil personnalisé

1. Créer `python/plugins/mon_outil.py`
2. Hériter de `BasePlugin`
3. Implémenter `can_handle()` et `handle()`
4. Ajouter dans `python/plugins/__init__.py`

## Ajouter un profil NFC

1. Brancher le lecteur USB NFC
2. Passer une carte sur le lecteur
3. L'UID apparaît dans les logs
4. Éditer `python/nfc_profiles.json`

## Contribuer

Fork → branche → PR.
Issues bienvenues pour les bugs et les demandes de fonctionnalités.

## Licence

MIT — Libre d'utilisation, modification et distribution.
