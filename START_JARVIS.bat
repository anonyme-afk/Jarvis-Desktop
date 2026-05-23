@echo off
echo Demarrage de JARVIS...
call venv\Scripts\activate
start "Flask" cmd /k "cd jarvis && python python/server.py"
timeout /t 3 /nobreak
npm run build
npm start
