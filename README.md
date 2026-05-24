# JARVIS Desktop

Interface holographique style Iron Man — Vision, IA, OSINT, Gaming.
Fonctionne sur **Windows, Mac et Linux**. Même les vieux PC.

## 🚀 Installation & Lancement Rapide

### 1. Obtenir le projet (Cloner ou Copier)
**Si vous clonez depuis GitHub :**
```bash
git clone https://github.com/anonyme-afk/Jarvis-Desktop.git
cd Jarvis-Desktop
```

**Si vous déplacez/copiez le projet manuellement :**
Vous pouvez copier le dossier entier `Jarvis-Desktop` n'importe où sur votre PC ou sur une clé USB. Pensez simplement à garder le dossier `.env` si vous l'aviez déjà configuré. Si vous changez de PC, il est recommandé de supprimer les dossiers `venv` et `node_modules` et de refaire l'installation pour éviter les erreurs de chemins.

### 2. Installer les dépendances
Double-cliquez sur **`INSTALL.bat`** (ou lancez-le depuis votre terminal).
Cela va configurer Python (création du `venv`, installation des modules) et Node (installation des bibliothèques nécessaires).

### 3. Configurer la clé API (indispensable)
- Allez sur **https://aistudio.google.com**
- Cliquez sur **Get API Key** → **Create API Key**
- Renommez ou copiez le fichier `.env.example` pour créer un fichier **`.env`**
- Ouvrez-le et collez votre clé à la première ligne :
```
GEMINI_API_KEY=ta_clé_ici
```

### 4. Lancer JARVIS

**Méthode 1 : Automatique (Recommandé sous Windows)**
Double-cliquez sur **`START_JARVIS.bat`**. Cela va ouvrir directement le serveur backend et l'interface dans votre navigateur par défaut.

**Méthode 2 : Manuel (en deux étapes, utile pour debug ou sur Mac/Linux)**
1. **Démarrer le Cerveau (Backend Python)**
Ouvrez un terminal, activez le venv, et lancez le serveur :
```cmd
call venv\Scripts\activate
python jarvis/python/server.py
```
*(Attendez de voir "Server running on http://127.0.0.1:5001" dans la console)*

2. **Démarrer l'Interface Visuelle (Frontend Web)**
Ouvrez un deuxième terminal et lancez le frontend :
```cmd
npm start
```
Puis accédez à l'interface dans votre navigateur sur **http://localhost:3000**

---

## 🧐 Comment ça marche ? (Détails des modules)

Le projet JARVIS est divisé en deux parties principales qui communiquent en permanence :

### 1. Le Frontend (L'Interface Web / HUD Holographique)
Géré par Node.js et Vite, il dessine l'UI en temps réel, écoute le microphone (Web Speech API), active la caméra, et gère les animations.
- **`index.html`** : La structure principale (réticules, cadrans, grilles).
- **`style.css`** : Le style néon HUD, les couleurs cyan, et toutes les animations visuelles.
- **`renderer.js`** : La mécanique visuelle dans le navigateur : envoi des requêtes au backend, affichage flux cam, effets de tchat.
- **`server.ts`** : Le serveur web Node.js qui héberge le frontend pour le navigateur.

### 2. Le Backend (Le "Cerveau" Python)
C'est le système nerveux central. Il fait le vrai travail en local via Python : analyse d'images, pilotage de l'IA, OSINT, etc.
- **`jarvis/python/server.py`** : Serveur Flask recevant les événements du HUD (texte, commandes vocales, images) et décidant comment les traiter.
- **`jarvis/python/providers.py`** : Permet de choisir et centraliser l'accès aux dizaines d'IA (Gemini Flash/Pro, Llama, Ollama, etc.).
- **`jarvis/python/tools/`** : Outils spécifiques appelés par l'IA ou le joueur (recherche web externe, météo pure, récupération IP).

---

## 🗂 Déplacer, Copier ou Dupliquer JARVIS

JARVIS est conçu pour être entièrement **portable**.

- **Sauvegarder ou Transférer sur le même PC** : Vous pouvez sans problème déplacer ou copier/coller tout le dossier parent `Jarvis-Desktop` vers votre Disque D:, ou un autre bureau.
- **Transférer sur une clé USB ou un autre ordinateur** :
  - L'environnement virtuel Python (`venv`) utilise des chemins stricts liés au PC d'origine.
  - **La bonne méthode** pour changer de PC : 
    1. Supprimez les gros fichiers générés (`venv/` et `node_modules/`).
    2. Copiez le dossier de base sur la nouvelle machine (gardez bien votre `.env`).
    3. Sur le nouveau PC, exécutez de nouveau le script d'installation (`INSTALL.bat`). Ça recréera un environnement sain et JARVIS marchera parfaitement là-bas.

---

## 🎙 Commandes & Raccourcis

### Raccourcis clavier (HUD)
- **ESPACE** : Activer/désactiver l'écoute vocale (micro)
- **C** : Activer/désactiver la vision/caméra pour que l'IA puisse voir.
- **ECHAP** : Stopper brutalement Jarvis (stop écoute / synthéteur vocal)
- **⚙ (Haut droite)** : Panneau des options moteurs d'IA
- **⚡ (Bas gauche)** : Outils rapides / Fonctions en 1 clic

### Commandes Vocales / Chaton de Base
*(La vision active est requise pour certaines actions :)*
- *"JARVIS, qu'est-ce que tu vois ?"* 
- *"JARVIS, quel temps à Paris ?"*
- *"JARVIS, donne-moi les infos système de l'ordinateur"*
- *"JARVIS, cherche les dernières news sur SpaceX"*

---

## 🛠 Dépannage et Vérifications

**🔴 L'API est déconnectée (Statut en rouge)**
- L'interface ne parvient pas à parler au Cerveau Python.
- Vérifiez la console noire Python. Si elle a crashé à l'ouverture, c'est sûrement la clé `.env` qui est vide ou invalide.

**🎙 Le micro ne marche pas**
- Assurez-vous d'avoir cliqué sur "*Autoriser le microphone*" en haut à gauche du navigateur à la 1ʳᵉ ouverture.
- Appuyez bien sur "ESPACE" pour allumer le signal "VEILLE" en vert "ÉCOUTE".

**🔇 Pas de son (Jarvis ne parle pas)**
- Lors d'une réponse de texte, le TTS (synthèse vocale) doit utiliser l'API Web Speech interne au système d'exploitation.
- Assurez-vous que le son n'est pas coupé ou qu'une voix est bien disponible dans les paramètres de votre PC (Windows Paramètres > Voix).
