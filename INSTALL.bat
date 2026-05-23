@echo off
echo Installation JARVIS Desktop...
npm install
"%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe" -m venv venv
call venv\Scripts\activate
pip install -r jarvis/python/requirements.txt
copy .env.example .env
echo.
echo INSTALLATION TERMINEE
echo Ouvre .env et ajoute ta cle : GEMINI_API_KEY=ta_cle
echo Cle gratuite sur https://aistudio.google.com
echo.
echo Ensuite double-clique sur START_JARVIS.bat
pause
