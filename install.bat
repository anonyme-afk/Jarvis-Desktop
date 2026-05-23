@echo off
echo Installation de JARVIS Desktop...
npm install
"%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe" -m venv venv
call venv\Scripts\activate
pip install -r jarvis/python/requirements.txt
copy .env.example .env
echo.
echo JARVIS installe avec succes !
echo.
echo Etape suivante : ouvre .env et ajoute ta cle GEMINI_API_KEY
echo Cle gratuite sur : https://aistudio.google.com
echo.
echo Pour lancer JARVIS : double-clique sur START_JARVIS.bat
pause
