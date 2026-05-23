@echo off
echo Demarrage de JARVIS...
call venv\Scripts\activate
start "JARVIS Python" cmd /k "cd jarvis && python python/server.py"
timeout /t 3
npm run build
npm start
