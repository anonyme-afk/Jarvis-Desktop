@echo off
title JARVIS - Installation
echo.
echo  ===================================
echo   JARVIS Desktop - Installation
echo  ===================================
echo.

:: Verifier Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Node.js non installe.
    echo Telecharge sur https://nodejs.org (version 18 ou 20)
    pause
    exit /b 1
)
echo [OK] Node.js detecte

:: Installer les dependances Node
echo [1/4] Installation des dependances Node.js...
call npm install
if errorlevel 1 (
    echo ERREUR npm install
    pause
    exit /b 1
)
echo [OK] Dependances Node installees

:: Creer le venv Python 3.11
echo [2/4] Configuration de Python 3.11...
if not exist venv (
    "%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe" -m venv venv
    if errorlevel 1 (
        echo ERREUR: Python 3.11 non trouve.
        echo Telecharge sur https://www.python.org/downloads/release/python-3119/
        echo IMPORTANT: Coche "Add python.exe to PATH" pendant l installation !
        pause
        exit /b 1
    )
    echo [OK] Environnement Python cree
) else (
    echo [OK] Environnement Python existant
)

:: Activer et installer dependances Python
call venv\Scripts\activate
echo [3/4] Installation des dependances Python...
python -m pip install --upgrade pip setuptools wheel --quiet
pip install -r jarvis\python\requirements.txt
if errorlevel 1 (
    echo ATTENTION: Certaines dependances n ont pas pu s installer.
    echo Essayez: pip install pipwin et ensuite pipwin install pyaudio
    echo Continuons quand meme...
)
echo [OK] Dependances Python installees

:: Creer le fichier .env
echo [4/4] Configuration...
if not exist .env (
    copy .env.example .env
    echo [OK] Fichier .env cree
) else (
    echo [OK] Fichier .env existant
)

echo.
echo  ===================================
echo   INSTALLATION TERMINEE !
echo  ===================================
echo.
echo  PROCHAINE ETAPE OBLIGATOIRE:
echo  Ouvre le fichier .env et ajoute:
echo  GEMINI_API_KEY=ta_cle_ici
echo.
echo  Cle GRATUITE sur: https://aistudio.google.com
echo  (Connexion Google requise, clique sur "Get API Key")
echo.
echo  Ensuite double-clique sur START_JARVIS.bat
echo.
notepad .env
pause
