@echo off
title JARVIS — Installation
color 0B
echo.
echo  ╔══════════════════════════════════╗
echo  ║   JARVIS DESKTOP — INSTALLATION  ║
echo  ╚══════════════════════════════════╝
echo.

node --version >nul 2>&1 || (echo [ERREUR] Node.js manquant. Telecharge sur nodejs.org && pause && exit /b 1)
echo [OK] Node.js detecte

echo [1/3] Dependances Node...
call npm install
if errorlevel 1 (echo [ERREUR] npm install && pause && exit /b 1)
echo [OK] Node installe

echo [2/3] Environnement Python 3.11...
if not exist venv (
    "%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe" -m venv venv
    if errorlevel 1 (echo [ERREUR] Python 3.11 introuvable. Telecharge sur python.org && pause && exit /b 1)
)
call venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel --quiet
pip install -r Mark-XXXIX-main\requirements.txt Flask flask-cors
echo [OK] Python configure

echo [3/3] Fichier de config...
if not exist .env (copy .env.example .env && notepad .env)
echo [OK] Config prete

echo.
echo  ╔══════════════════════════════════╗
echo  ║       INSTALLATION TERMINEE      ║
echo  ║  Double-clique sur START_JARVIS  ║
echo  ╚══════════════════════════════════╝
echo.
pause
