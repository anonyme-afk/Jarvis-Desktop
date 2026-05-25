@echo off
title JARVIS — Demarrage Intelligent
color 0B
echo.
echo  ╔══════════════════════════════════╗
echo  ║  JARVIS DESKTOP — INTELLIGENT    ║
echo  ╚══════════════════════════════════╝
echo.

:: 1. Vérification de Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Node.js est requis pour faire tourner l'interface !
    echo Veuillez l'installer depuis https://nodejs.org/
    pause
    exit /b 1
)

:: 2. Vérification et installation des dépendances Node.js (npm install)
if not exist node_modules (
    echo [Setup] Dossier node_modules introuvable...
    echo [Setup] Installation automatique de vos dependances Node.js (npm install)...
    echo Cela peut prendre un peu de temps pour le premier demarrage. Veuillez patienter...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERREUR] Impossible d'installer les modules Node.js.
        pause
        exit /b 1
    )
    echo [OK] Dependances Node installees avec succes !
) else (
    echo [OK] Dependances Node de l'interface deja installees.
)

:: 3. Vérification de Python & de son environnement virtuel
if not exist venv (
    echo [Setup] Environnement virtuel Python introuvable. Creation automatique...
    
    :: Détecter le chemin Python
    set "PYTHON_PATH=python"
    
    if exist "%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe" (
        set "PYTHON_PATH=%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe"
    ) else if exist "%USERPROFILE%\AppData\Local\Programs\Python\Python312\python.exe" (
        set "PYTHON_PATH=%USERPROFILE%\AppData\Local\Programs\Python\Python312\python.exe"
    ) else if exist "%USERPROFILE%\AppData\Local\Programs\Python\Python310\python.exe" (
        set "PYTHON_PATH=%USERPROFILE%\AppData\Local\Programs\Python\Python310\python.exe"
    ) else (
        where python >nul 2>&1
        if %errorlevel% neq 0 (
            echo [ERREUR] Python est requis pour lancer le moteur de JARVIS.
            echo Veuillez telecharger et installer Python sur https://www.python.org/ (cochez "Add Python to PATH")
            pause
            exit /b 1
        )
    )
    
    echo [Setup] Utilisation de l'executable Python de base.
    call "%PYTHON_PATH%" -m venv venv
    if %errorlevel% neq 0 (
        echo [ERREUR] Impossible de creer l'environnement virtuel venv.
        pause
        exit /b 1
    )
    
    echo [Setup] Installation des extensions et modules requis pour l'IA...
    call venv\Scripts\activate
    python -m pip install --upgrade pip setuptools wheel --quiet
    pip install -r backend\requirements.txt Flask flask-cors
    echo [Setup] Installation des navigateurs pour Browser-Use / Playwright...
    python -m playwright install --with-deps
    if %errorlevel% neq 0 (
        echo [ERREUR] Erreur lors de l'installation de requirements.txt.
        pause
        exit /b 1
    )
    echo [OK] Moteur Python prepare avec succes !
) else (
    echo [OK] Environnement de developpement Python pret.
)

:: 4. Fichier de configuration Environnement (.env)
if not exist .env (
    echo [Setup] Fichier de configuration .env absent. Initialisation automatique...
    copy .env.example .env >nul
    echo [!] AJOUTEZ VOTRE CLE GEMINI_API_KEY dans le fichier .env qui s'ouvre !
    echo Obtenez-en une gratuitement sur : https://aistudio.google.com
    notepad .env
    echo Appuyez sur n'importe quel touche lorsque vous avez fini de configurer et d'enregistrer votre cle.
    pause >nul
)

:: 5. Lancement des serveurs
echo.
echo [1/2] Demarrage du Moteur Python (Flask sur le port 5001)...
start "JARVIS-Flask" cmd /k "title JARVIS Moteur Python && call venv\Scripts\activate && cd backend && python main.py"

echo [2/2] Demarrage de l'Interface Visuelle (HUD)...
timeout /t 2 /nobreak >nul
start http://localhost:3000

:: S'assurer que le build a été fait au moins une fois
if not exist dist (
    echo [Setup] Compilation de l'interface en cours...
    call npm run build
)

title JARVIS — Console d'interface
npm start
