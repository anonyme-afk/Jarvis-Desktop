# JARVIS Desktop v4 (Refonte Holographique & Cerveau Open Interpreter)

Interface holographique avancée style **Blueprint Tactique Iron Man** intégrant la nouvelle architecture bidirectionnelle : **Le Cerveau + Les Mains (Open Interpreter)**.
Conçu pour fonctionner de manière fluide sur **Windows, Mac, et Linux** avec un design haute fidélité extrêmement réactif.

---

## 🎨 Design System : "Millimeter Blueprint Grid"
La v4 réorganise entièrement l'interface utilisateur (HUD) pour s'adapter à l'exécution automatique d'Open Interpreter :
1. **Papier Millimétré Cyber** : Arrière-plan double-grille bleu crépusculaire et cyan avec réticules filigranes d'angles tactiques.
2. **Orbe Intelligent Rotatif (Le Coeur)** : Un ensemble d'anneaux vectoriels (SVG) concentriques animés par des vitesses et des rotations opposées (`spin-cw` / `spin-ccw`) qui varient d'état en direct (*Listening/Vert, Thinking/Ambre, Speaking/Bleu*).
3. **Cognitive Action Flow (Gauche)** : Un fil de logs temps-réel alimenté dynamiquement pour suivre la planification interne de JARVIS.
4. **Console d'Exécution Native (Droite)** : Quand Open Interpreter génère des scripts Python ou Shell (`bash / cmd`), le code est extrait du chat et imprimé à haute cadence dans un terminal monospacé sombre avec colorations syntaxiques scifi (`IBM Plex Mono`). Plus de pollution textuelle dans le fil principal !

---

## 🚀 1. Installation & Lancement Automatique (1-Clic)

Plus besoin de lancer plusieurs scripts ! Tout a été automatisé de A à Z.

### Sous Windows :
1. Téléchargez et installez **Node.js** (sur https://nodejs.org) et **Python** (sur https://python.org - *veillez à cocher l'option "Add Python to PATH" pendant l'installation*).
2. Double-cliquez simplement sur **`START_JARVIS.bat`**.
3. **Au premier lancement** : Le script détectera l'absence de vos dépendances et installera automatiquement tout le nécessaire (Node.js, environnement virtuel Python, Playwright, Open Interpreter).
4. Le script copiera également l'exemple de configuration vers votre propre fichier `.env` puis l'ouvrira dans le Bloc-notes. Configurez votre clé d'API Gemini (obtenez-en une sur https://aistudio.google.com).
5. Enregistrez le fichier `.env` et fermez-le. Le système lancera alors automatiquement le moteur de JARVIS, ouvrira automatiquement votre navigateur sur l'adresse de l'interface (**http://localhost:3000**) et compilera le HUD !

### Au quotidien (Lancements suivants) :
Double-cliquez simplement sur **`START_JARVIS.bat`**. Il détectera que tout est déjà configuré, sautera les étapes de téléchargement et démarrera JARVIS instantanément en ouvrant votre navigateur internet !

---

## 🎙️ 2. Sortie Vocale Premium Local : Kokoro-82M (Recommandé)

Pour une immersion totale digne d'Iron Man, le serveur intègre désormais un support natif pour le modèle **Kokoro-82M** !

### Pourquoi utiliser Kokoro-82M avec JARVIS ?
* **Zéro Latence** : Étant un modèle ultra-léger (~82 millions de paramètres), il synthétise le texte en voix à la vitesse de l'éclair, sans temps d'attente.
* **Qualité Studio** : Les intonations françaises sont d'une clarté et d'un réalisme bluffant, surpassant les solutions cloud payantes.
* **100% Local, Privé & Gratuit** : Fonctionne entièrement sur votre PC, sans connexion Internet requise, et sans coût d'API.

### Comment l'installer sur votre machine d'exécution ?
Activez la console de votre environnement virtuel (`venv/Scripts/activate` sous Windows) et tapez :
```bash
pip install kokoro sounddevice soundfile
```
*Note : Sur Linux ou macOS, vous aurez également besoin de la bibliothèque système d'analyse phonétique `espeak-ng` (ex: `sudo apt-get install espeak-ng` ou `brew install espeak`).*

Une fois ces modules installés, le serveur JARVIS **détectera automatiquement** Kokoro et l'utilisera en lieu et place du moteur standard `pyttsx3` pour une voix d'exception !

---

## 🛠️ 3. Installation Manuelle ou Mac/Linux

Si vous préférez installer pas à pas ou si vous êtes sur macOS / Linux :

```bash
# 1. Installer les dépendances de l'interface (Node.js)
npm install

# 2. Créer l'environnement virtuel Python et installer les dépendances de calcul
python3 -m venv venv
source venv/bin/activate
pip install -r jarvis/python/requirements.txt

# 3. Configurer votre clé d'API
cp .env.example .env
# Éditez le fichier .env pour y ajouter votre GEMINI_API_KEY
```

Puis pour le lancer, ouvrez deux terminaux :
* **Terminal 1** : `source venv/bin/activate && python jarvis/python/server.py`
* **Terminal 2** : `npm run build && npm start`
* Accédez ensuite à **http://localhost:3000** dans votre navigateur.

---

## 🧠 4. Architecture : Le Cerveau + Les Mains (Open Interpreter)

Le projet JARVIS garantit des performances maximales en divisant le travail entre deux "hémisphères" :

### Le Frontend (Interface HUD — Navigateur web)
C'est le tableau de bord visible, géré par **Vite / Node.js** pour une fluidité maximale.
* **`index.html` & `style.css`** : Dessine les structures crépusculaires, réticules holographiques et animations cyan tactiques du HUD.
* **`renderer.js`** : Moteur événementiel chargé d'écouter votre voix via Web Speech API, de capturer la webcam, et d'envoyer les instructions utilisateur au Cerveau NodeJS/Python.
* **`server.ts`** : Petit serveur Node local qui sécurise et expose l'interface à l'adresse locale.

### Le Backend (Moteur Python & Open Interpreter Core)
C'est l'entité qui réfléchit, planifie et exécute. Tournant en arrière-plan (serveur Flask sur le port 5001), il gère l'orchestration du modèle intelligent.
* **`jarvis/python/server.py`** : Réceptionne les données brutes envoyées par l'interface HUD et utilise **Open Interpreter** pour piloter les actions locales.
* **Open Interpreter Core** : Plus de routage rigide ou de fonctions limitées ! Tout ce que vous dites est analysé par l'IA, qui écrit elle-même en direct les scripts Python ou les scripts Shell (Bash / Windows Command Line) nécessaires pour l'exécuter, puis les lance sur votre machine (en mode automatique grâce à `interpreter.auto_run = True`).
  * *"Ouvre Chrome sur YouTube"* ➔ Génère et exécute le script `webbrowser.open("https://youtube.com")`
  * *"Écris un script Python de tri"* ➔ Génère et lance le script d'écriture locale.
  * *"Quel est mon CPU ?"* ➔ Génère et lance `psutil.cpu_percent()` et répond précisément.

---

## 🎛️ 5. Commandes & Raccourcis Clavier du HUD

* **ESPACE** : Activer/désactiver l'écoute vocale (micro)
* **C** : Activer/désactiver la vision (caméra webcam)
* **N** : Activer la carte réseau holographique interactive
* **ESC** : Stopper brutalement JARVIS (coupe nette des vocalises)
* **↑ (Flèche Haut)** : Rappeler la dernière directive envoyée dans l'éditeur de commande

---

## 🌐 6. Mode Navigateur Autonome (Playwright)

JARVIS intègre un mode d'automatisation de navigateur (via Playwright) qui lui permet d'utiliser l'interface web de modèles comme Gemini ou ChatGPT **à votre place, avec votre propre compte**, sans avoir besoin d'utiliser (ni de payer) une clé API.

* **HUD (View Mode)** : Pour voir ce que JARVIS fait ou s'il est bloqué, cliquez sur le bouton **VIEW CHROME** dans la barre de statut (en bas). Chrome sortira de l'ombre en mode visible, et vous pourrez le masquer plus tard en cliquant sur "HIDE CHROME".
* **Installation** : JARVIS a besoin des navigateurs Playwright. Si l'installation ne s'est pas faite seule au premier lancement, exécutez la commande `python -m playwright install` depuis votre console activée.

---

## 🩸 7. Dépannage rapide

* **Erreur de Modèle / "API key expired"** : Allez sur [Google AI Studio](https://aistudio.google.com), créez une nouvelle clé d'API gratuite, collez-la dans le fichier `.env` (`GEMINI_API_KEY=AIzaSy...`) et relancez `START_JARVIS.bat`.
* **Le micro reste muet** : Pensez à "Autoriser le microphone" dans le navigateur au premier lancement, puis pressez "ESPACE".
* **PyAudio Errors** : Sur Windows, si l'installation de requirements échoue sur PyAudio, exécutez `pip install pipwin && pipwin install pyaudio`.
