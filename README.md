# JARVIS Desktop

Bienvenue dans JARVIS Desktop, votre assistant IA personnel multimodale ultra-avancé propulsé par Gemini, avec contrôle système (Windows), OSINT, vision par ordinateur, et mémoire.

## Installation (2 minutes)
1. git clone https://github.com/anonyme-afk/Jarvis-Desktop.git
2. cd Jarvis-Desktop
3. Double-clique sur INSTALL.bat
4. Ouvre .env et colle ta clé GEMINI_API_KEY
   (clé gratuite sur https://aistudio.google.com)
5. Double-clique sur START_JARVIS.bat
6. Ouvre http://localhost:3000

## Lancement manuel (si les .bat ne marchent pas)
Terminal 1 :
  call venv\Scripts\activate
  cd jarvis
  python python\server.py

Terminal 2 :
  npm run build
  npm start

Puis ouvre http://localhost:3000

## Commandes vocales
| Commande | Action |
|---|---|
| "JARVIS, cherche [sujet]" | Recherche web |
| "JARVIS, quel temps à [ville]" | Météo |
| "JARVIS, infos système" | CPU/RAM/Disque |
| "JARVIS, qu'est-ce que tu vois ?" | Analyse webcam |
| "JARVIS, [question]" | Réponse IA |

## Raccourcis clavier
| Touche | Action |
|---|---|
| ESPACE | Activer/désactiver le micro |
| C | Activer/désactiver la caméra |
| N | Carte réseau |
| ⚡ | Panneau d'outils |

## Dépannage
- JARVIS ne répond pas → vérifier que server.py tourne (Terminal 1)
- Micro muet → Paramètres Windows > Confidentialité > Microphone > Autoriser
- Erreur dlib → normal, module optionnel, JARVIS fonctionne sans
- Port 5001 occupé → redémarre le PC
