# JARVIS Desktop

**Live Demo**: [https://anonyme-afk.github.io/Jarvis-Desktop/](https://anonyme-afk.github.io/Jarvis-Desktop/)

Bienvenue dans JARVIS Desktop, votre assistant IA personnel multimodale ultra-avancé propulsé par Gemini, avec contrôle système (Windows), OSINT, vision par ordinateur, et mémoire.

## Installation Ultra Simple (Windows)

1. Double-cliquez sur `install.bat`
2. Attendez la fin de l'installation des dépendances.
3. Ouvrez le fichier `.env` qui a été créé et ajoutez votre `GEMINI_API_KEY`.
4. Double-cliquez sur `START_JARVIS.bat` pour lancer JARVIS.

C'est tout !

---

## Obtenir une Clé API Gratuite

JARVIS utilise par défaut **Gemini 1.5 Flash**, qui est gratuit.
1. Allez sur [Google AI Studio](https://aistudio.google.com)
2. Cliquez sur **Get API Key**
3. Créez une nouvelle clé
4. Collez la clé dans votre fichier `.env` : `GEMINI_API_KEY=votre-clef-ici`

*(Vous pouvez modifier le fournisseur d'IA directement via le menu en haut à droite de l'interface !)*

---

## Commandes vocales courantes

JARVIS comprend le naturel, mais voici quelques exemples d'actions :

| Action | Exemple de formulation verbale / texte |
| --- | --- |
| **Site Web** | *"Jarvis, ouvre Spotify s'il te plaît"* |
| **Caméra (Vision)** | *"Active la caméra", "Qu'est-ce que tu vois ?"* |
| **Rappels** | *"Rappelle-moi dans 5 minutes de sortir le linge"* |
| **Jeux / Farming**| *"Active le mode farm sur la touche espace pour 300 secondes"* |
| **Analyse** | *"Fais un port scan de monsite.com", "Analyse cette adresse IP"* |
| **Mémoire** | *"Souviens-toi que mon film préféré est Inception"* |

---

## Raccourcis clavier (dans l'interface Web)

| Touche | Action |
| --- | --- |
| **`Espace`** | Basculer l'écoute (activer/désactiver le micro) |
| **`C`** | Allumer / éteindre le flux de la caméra web (`/vision`) |
| **`M`** | Activer temporairement l'overlay du scan Neuro-Réseau |

---

## Dépannage (Troubleshooting)

- **Le microphone ne fonctionne pas** : Vérifiez que l'icône de caméra/micro en haut de la barre de votre navigateur (Chrome/Edge) vous permet l'accès. (Erreur "Autorise le micro dans ton navigateur").
- **Statut "HORS LIGNE" en rouge / JARVIS ne répond pas du tout** : Le serveur Python ne tourne pas. Vérifiez que votre terminal où vous avez écrit `python jarvis/python/server.py` ne comporte pas d'erreur de clé manquante ou de module non installé.
- **"Speech recognition error: no-speech" (dans la console)** : C'est normal. C'est l'API de base du navigateur qui dit "Je n'entends rien". JARVIS ignore silencieusement cette erreur.
- **Port 5001 occupé** : Dans `jarvis/python/server.py`, changez le port `5001` par `5005`, et faites le même changement dans `renderer.js` et `vite.config.ts`.
- **Une erreur `dlib` ou `face_recognition` ou `torch` apparait** : Nous avons retiré ces dépendances du fichier `requirements.txt` natif car elles sont très complexes à installer sous Windows. Le système JARVIS ignore silencieusement ces erreurs et fonctionne très bien sans. L'installation de la vision et du VAD local devient alors simplement désactivée (fallback classique).
