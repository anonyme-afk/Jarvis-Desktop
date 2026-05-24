@echo off
title JARVIS Desktop
echo.
echo  ===================================
echo   JARVIS Desktop - Demarrage
echo  ===================================
echo.

:: Verifier si le venv existe, sinon le creer
if not exist venv (
    echo [1/3] Creation de l environnement Python 3.11...
    "%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe" -m venv venv
    if errorlevel 1 (
        echo ERREUR: Python 3.11 introuvable.
        echo Telecharge Python 3.11 sur https://python.org
        pause
        exit /b 1
    )
)

:: Activer le venv
call venv\Scripts\activate

:: Verifier si Flask est installe
python -c "import flask" 2>nul
if errorlevel 1 (
    echo [2/3] Installation des dependances Python...
    pip install -r jarvis\python\requirements.txt
    playwright install chromium
    if errorlevel 1 (
        echo ERREUR lors de l installation des dependances.
        pause
        exit /b 1
    )
)

:: Verifier si .env existe
if not exist .env (
    echo [!] Fichier .env manquant. Copie depuis .env.example...
    copy .env.example .env
    echo.
    echo IMPORTANT: Ouvre le fichier .env et ajoute ta cle GEMINI_API_KEY
    echo Cle gratuite sur: https://aistudio.google.com
    echo.
    notepad .env
    timeout /t 3 /nobreak > nul
)

:: Lancer le serveur Flask en arriere-plan
echo [3/3] Demarrage du serveur JARVIS...
start "JARVIS-Flask" cmd /k "call venv\Scripts\activate && cd jarvis && python python\server.py"

:: Attendre que Flask soit pret
timeout /t 4 /nobreak > nul

:: Build et lancer l interface
echo Lancement de l interface...
call npm run build 2>nul
npm start
