# JARVIS Desktop v4 

Interface holographique avancée style Iron Man intégrant : Vision, Intelligence Artificielle, OSINT, et Contrôles Gaming.
Conçu pour fonctionner de manière fluide sur **Windows, Mac, et Linux**, même sur des configurations anciennes.

---

##  1. Installation Rapide (2 minutes)

### Obtention du Projet
Si vous débutez, récupérer le dossier source :
```bash
git clone https://github.com/anonyme-afk/Jarvis-Desktop.git
cd Jarvis-Desktop
```

### Configuration des Dépendances
**Sous Windows** :
1. Double-cliquez sur `INSTALL.bat`. Cela va créer l'environnement Python et installer les dépendances (Python et Node.js).
2. Rendez-vous sur https://aistudio.google.com → **Get API Key**
3. Configurez votre clé d'API (le script vous y invitera en copiant `.env.example` en `.env`).

**Sous Mac/Linux** :
```bash
npm install
python3 -m venv venv && source venv/bin/activate
pip install -r jarvis/python/requirements.txt
cp .env.example .env
```
N'oubliez pas d'éditer votre fichier `.env` pour y ajouter `GEMINI_API_KEY=votre_clé`.

---

##  2. Lancement du Système (Launch)

Le système complet est divisé en deux parties devant fonctionner simultanément :

**Méthode Automatique (Windows)** :
Double-cliquez simplement sur **`START_JARVIS.bat`**. Le script lancera le serveur IA et ouvrira l'interface.

**Méthode Manuelle (Mac/Linux ou Debug)** :
Lancez ces deux processus dans deux terminaux séparés :
```bash
# Terminal 1 : Démarre le Cerveau (serveur IA "Flask")
# Sous Windows: call venv\Scripts\activate
source venv/bin/activate
python jarvis/python/server.py

# Terminal 2 : Démarre l'Interface Visuelle (HUD)
npm run build && npm start
```
Ensuite, ouvrez votre navigateur et accédez à **http://localhost:3000**

---

##  3. Architecture : Explication des Parties Distinctes

Le projet JARVIS garantit des performances maximales en divisant le travail entre deux "hémisphères" :

###  Le Frontend (Interface HUD — Navigateur web)
C'est le tableau de bord visible, géré par **Vite / Node.js** (basé sur des technologies web classiques pour la fluidité).
- **`index.html` & `style.css`** : Dessine les structures crépusculaires, réticules holographiques et animations cyan typiques du HUD.
- **`renderer.js`** : Moteur événementiel chargé d'écouter votre voix via Web Speech API, de capturer la webcam, et d'envoyer les instructions utilisateur au Cerveau.
- **`server.ts`** : Petit serveur Node local qui sécurise et expose l'interface à l'adresse locale.

###  Le Backend (Le "Cerveau" — Moteur Python)
C'est l'entité qui réfléchit et exécute. Tournant en arrière-plan (serveur sur le port 5001), il gère la véritable IA.
- **`jarvis/python/server.py`** : Réceptionne les données brutes (images, commandes vocales envoyées par le HUD) et pilote les actions complexes.
- **`jarvis/python/providers.py`** : Hub central gérant la communication vers les grands modèles (Gemini, Groq, Llama, Ollama, DeepSeek).
- **`jarvis/python/tools/`** : Outils modulaires injectés à l'IA – permettant la recherche Web (OSINT), l'obtention de la météo ou la récupération IP, exécutés dynamiquement.

---

##  4. Déplacer, Copier ou Héberger votre JARVIS

JARVIS est conçu pour être un projet portable. Si vous avez d'abord testé JARVIS sur le Bureau et que vous souhaitez le ranger ou le passer sur une clé USB, suivez ces règles :

### Comment déplacer le projet (ex : vers `D:\Projets\Jarvis`)
1. **Évitez de déplacer le système tel quel** : L'environnement vituel Python (`venv`) garde en mémoire des chemins "absolus". Si vous déplacez le dossier, les chemins de l'ancien dossier seront cassés.
2. **La bonne méthode de déplacement** :
   - Prenez votre dossier final `Jarvis-Desktop`.
   - **Supprimez les dossiers `venv/` et `node_modules/`** de la copie (ils sont lourds et obsolètes).
   - Déplacez le projet à l'endroit désiré.
   - Assurez-vous d'avoir emporté votre fichier caché `.env` (pour ne pas perdre vos clés API).
   - Relancez le script `INSTALL.bat` (ou les commandes d'installation). Les environnements se reconstruiront spécifiquement pour le nouvel emplacement !

### Comment le dupliquer pour des tests
Si vous souhaitez cloner le projet au même endroit pour bidouiller le code, copiez le dossier `Jarvis-Desktop` vers `Jarvis-Desktop-Test`, effacez `venv/` et exécutez de nouveau l'installation.

---

##  5. Commandes & Raccourcis

### Raccourcis HUD
- **ESPACE** : Activer/désactiver l'écoute vocale (micro)
- **C** : Activer/désactiver la vision/caméra
- **N** : Activer la carte réseau dynamique
- **ESC** : Stopper brutalement JARVIS
- **↑ (Flèche Haut)** : Dernier message textuel envoyé

### Exemples de Commandes Vocales
*JARVIS s'exécute dynamiquement.* 
-  "JARVIS, cherche les dernières actualités sur SpaceX"
-  "JARVIS, quel temps fait-il actuellement à Paris ?"
-  "JARVIS, donne-moi les infos système."
-  "JARVIS, qu'est-ce que tu vois ?" *(Nécessite la caméra "C" active)*
-  "JARVIS, donne l'IP locale du PC."

---

##  6. Dépannage rapide

- **JARVIS ne répond pas ou HUD inactif** : Assurez-vous que le terminal hébergeant le processus Python (Flask) n'a pas crashé, et que `server.py` ou `START_JARVIS` tournent bien.
- **Erreur de Modèle / API limit** : Vérifiez que votre `.env` contient la ligne `GEMINI_API_KEY=` suivie d'une clé correcte et valide.
- **Le micro reste muet** : Pensez à "Autoriser le microphone" dans le navigateur au premier lancement, puis pressez "ESPACE".
- **PyAudio Errors** (Manque de son) *: `pip install pipwin && pipwin install pyaudio` (sur Windows en cas d'absence de module).*
