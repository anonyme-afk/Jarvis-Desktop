# Lancement de JARVIS Desktop 🚀

## 1. Démarrer le Cerveau (Backend Python)
Ouvrez un **premier terminal** dans le dossier `Jarvis-Desktop` :
```cmd
call venv\Scripts\activate
python jarvis/python/server.py
```
*(Attendez de voir "Server running on http://127.0.0.1:5001" ou "Provider: Gemini...")*

## 2. Démarrer l'Interface Visuelle (Frontend Web)
Ouvrez un **deuxième terminal** dans le dossier `Jarvis-Desktop` :
```cmd
npm start
```
*(Ceci va lancer le serveur Vite / Express)*

## 3. Accéder à JARVIS
Ouvrez votre navigateur : **http://localhost:3000**

---

### ✅ 3 Vérifications de bon fonctionnement
1. **API Status** : En bas à gauche, vous devriez voir **[CONNECTÉ]** en vert. S'il est rouge, le terminal Python indique probablement une erreur (clé API manquante par exemple).
2. **Microphone (Web Speech API)** : Cliquez sur **VEILLE** en haut à droite ou appuyez sur **ESPACE** pour activer l'écoute. Autorisez le micro dans le navigateur.
3. **TTS (Voix)** : Tapez `Bonjour` dans la barre en bas et validez. JARVIS devrait vous répondre texte et voix (l'orbe pulse).
