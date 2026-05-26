# JARVIS Desktop v5 (Fusion MARK XXXIX)

Interface holographique avancee developpee pour un controle tactique total, fusionnee avec le puissant moteur backend Mark-XXXIX. Concu pour fonctionner de maniere fluide sur Windows, Mac, et Linux.

## Credits et Remerciements

Une gratitude particuliere est adressee au developpeur **FatihMakes** pour son travail inestimable sur l'architecture Mark-XXXIX originale. Ce projet de bureau s'appuie massivement sur son code fondationnel.
- Profil GitHub: https://github.com/FatihMakes
- Depot original Mark-XXXIX: https://github.com/FatihMakes/Mark-XXXIX

## Qu'est-ce qui a change dans cette fusion (Mise a jour Omniscient) ?

- Le frontend holographique exceptionnel de l'ancien Jarvis-Desktop a ete conserve, heberge a la racine du projet pour des raisons de performances Vite.
- Le cerveau backend a ete entierement remplace par le puissant moteur Mark-XXXIX base sur l'IA Gemini Multimodal Live, offrant une latence auditive ultra basse.
- **Systeme de Tools Omniscient (GOD MODE)** : Les capacites ont ete portees a un niveau critique. Mark-XXXIX integre un catalogue colossal : Threat Intelligence (Shodan), OCR et Biometrie Faciale (MediaPipe, Tesseract), Scan Reseau profond (Nmap, Scapy), Cryptographie de grade militaire, geolocalisation par satellite (GeoPy) et bien plus. Il integre egalement l'ecosysteme Composio, Browser-Use, LangChain, et CrewAI.
- **Serveurs Model Context Protocol (MCP)** : Support des plugins contextuels dynamiques d'Anthropic (Filesystem, Google Maps, Postgres, Web Search).
- **Plugins Ecosystème Modulaire** : Intégration simulée et architecture d'attachement aux modules externes (CrewAI, AutoGPT Plugins).
- L'arborescence globale a ete rationalisee (separation logique de la racine (Frontend) vs `backend/`).

---

## Design System : "Millimeter Blueprint Grid"

Cette version reorganise entierement l'interface utilisateur (HUD) :
1. **Papier Millimetre Cyber** : Arriere-plan double-grille bleu crepusculaire et cyan avec reticules filigranes d'angles tactiques.
2. **Orbe Intelligent Rotatif (Le Coeur)** : Un ensemble d'anneaux vectoriels concentriques animes qui varient d'etat en direct (Listening, Thinking, Speaking).
3. **Cognitive Action Flow (Gauche)** : Un fil de logs temps-reel alimente dynamiquement pour suivre la planification interne de JARVIS.
4. **Console d'Execution Native (Droite)** : Sorties brutes du moteur extractees dans un terminal espace et elegant.

---

🔑 **Configuration des Clés d'API (CRITIQUE)**

Pour éviter les limitations de quota d'appel (Erreurs **429 RESOURCE_EXHAUSTED** de l'API Gemini standard), cette version intègre désormais le routage intelligent multi-modèles d'OpenRouter. Il est **STRICTEMENT RECOMMANDÉ** de configurer votre clé d'API OpenRouter.

Ajoutez ces variables dans votre fichier `.env` :
- `OPENROUTER_API_KEY` : Votre clé API OpenRouter personnelle (Créez un compte gratuit sur https://openrouter.ai et générez une clé). Elle donne accès aux modèles gratuits et stables comme *DeepSeek V4 Flash*, *MiniMax M2.5*, *Gemma 4*, o1-oss, etc.
- `GEMINI_API_KEY` : Votre clé API Google AI Studio standard (utilisée en cas de secours ultime si OpenRouter échoue).

---

## 1. Installation et Lancement Automatique (1-Clic)

Tout a ete automatise de A a Z.

### Configuration sous Windows :
1. Telechargez et installez Node.js (https://nodejs.org) et Python (https://python.org - veillez a cocher l'option "Add Python to PATH").
2. Double-cliquez simplement sur `START_JARVIS.bat`.
3. Au premier lancement : Le script detectera l'absence de vos dependances et installera automatiquement tout le necessaire (Node.js, environnement virtuel Python, outils de backend, framework frontend).
4. Le script copiera egalement l'exemple de configuration vers votre propre fichier `.env` puis l'ouvrira dans un editeur de texte. Configurez absolument votre cle d'API OpenRouter via `OPENROUTER_API_KEY` et optionnellement votre clé Gemini via `GEMINI_API_KEY`.
5. Enregistrez le fichier `.env` et fermez-le. Le systeme lancera alors automatiquement le moteur de JARVIS, ouvrira votre navigateur sur l'adresse de l'interface (http://localhost:3000) et compilera le HUD.

### Lancement regulier :
Double-cliquez simplement sur `START_JARVIS.bat`. Il sautera les etapes de telechargement et demarrera le systeme instantanement.

---

## 2. Installation Manuelle ou Mac/Linux

Si vous preferez installer manuellement ou si vous utilisez macOS / Linux :

```bash
# 1. Configurer vos clés d'API
cp .env.example .env
# Editez le fichier .env pour y ajouter :
# OPENROUTER_API_KEY=votre_cle_openrouter
# GEMINI_API_KEY=votre_cle_gemini
```

Puis pour le lancer, ouvrez deux terminaux :
- **Terminal 1 (Serveur Python)** : `source venv/bin/activate && cd backend && python main.py`
- **Terminal 2 (Interface Web)** : `npm run build && npm start`
- Accedez ensuite a **http://localhost:3000**.

---

## 3. Architecture Structurelle

Le projet garantit des performances maximales en divisant le travail entre deux "hemispheres" independants :

### Le Frontend (Interface HUD)
Heberge a la racine du projet. C'est le tableau de bord visible, gere par Vite et Node.js pour une fluidite maximale.
- `index.html` & fichiers sources : Dessinent les structures holographiques tactiques.
- `server.ts` : Petit serveur local executif de gestion des liens statiques.

### Le Backend (Moteur Python MARK XXXIX)
Heberge dans `/backend/`. C'est l'entite qui reflechit, planifie et execute. Tournant en arriere-plan, il gere l'orchestration du modele intelligent via Flask.
- `backend/main.py` : Receptionne les donnees, gere le contexte multimodal live, et declenche de redoutables appels d'outils systeme.
- Outils d'action locaux : Regroupe un repertoire d'aptitudes specifiques de traitement et controle.

---

## 4. Raccourcis Clavier Specifiques

- **ESPACE** : Activer/desactiver la sequence audio (Microphone).
- **C** : Activer/desactiver le module de flux de vision (Cam).
- **N** : Basculer l'affichage de la topologie reseau holographique.
- **ESC** : Suspension systeme immediate.
- **Fleche Haut** : Rappel de la precedente directive inscrite manuellement.

---

## 5. Maintenance et Depannage

- Erreur d'Authentification / Cle d'API : Generez une nouvelle cle depuis Google AI Studio, remplacez celle du fichier `.env`, puis redemarrez.
- Flux audio interrompu : Autorisez le peripherique d'entree dans les parametres du navigateur puis pressez la touche ESPACE.
- PyAudio - Defaillance native : Sous Windows, si l'installation echoue, executez la commande alternative `pip install pipwin && pipwin install pyaudio` depuis la console activee.
