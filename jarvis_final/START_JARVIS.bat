@echo off
title JARVIS — Demarrage
color 0B
echo.
echo  ╔══════════════════════════════════╗
echo  ║    JARVIS DESKTOP — DEMARRAGE    ║
echo  ╚══════════════════════════════════╝
echo.

if not exist venv (
    echo [Setup] Creation environnement Python...
    "%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe" -m venv venv
    call venv\Scripts\activate
    pip install -r jarvis\python\requirements.txt --quiet
) else (
    call venv\Scripts\activate
)

if not exist .env (
    copy .env.example .env
    echo [!] Configure ta cle GEMINI_API_KEY dans .env
    notepad .env
    timeout /t 3 /nobreak >nul
)

echo [1/2] Demarrage du serveur IA (Flask)...
start "JARVIS-Flask" cmd /k "title JARVIS-Flask && call venv\Scripts\activate && cd jarvis && python python\server.py"
timeout /t 5 /nobreak >nul

echo [2/2] Demarrage de l interface...
call npm run build 2>nul
npm start
