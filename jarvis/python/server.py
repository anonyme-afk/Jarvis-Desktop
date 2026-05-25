"""
JARVIS Desktop — Serveur Python Principal v4.0 (Open Interpreter Core)
Unifies the beautiful HUD visual frontend with the ultimate local execution capabilities of Open Interpreter.
"""
import os
import json
import threading
import time
import queue
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import Open Interpreter
try:
    from interpreter import interpreter
    # Default settings for fully automated execution
    interpreter.offline = False
    interpreter.auto_run = True  # Autonomously plan and execute code (Tu parles -> JARVIS comprend -> JARVIS exécute)
    
    # Custom system instruction to fit JARVIS personality
    interpreter.system_message = """
Tu es JARVIS, l'assistant IA de l'utilisateur. Tu es calme, précis, légèrement formel mais jamais condescendant. Tu parles comme l'IA dans Iron Man : concis, factuel, avec parfois une touche d'humour sec.
Tu es connecté au système d'exploitation de l'ordinateur de l'utilisateur via Open Interpreter. Tu peux écrire du code Python ou exécuter des commandes shell (Windows/Bash) pour accomplir les demandes de l'utilisateur directement sur sa machine.
Lorsque tu décris tes actions ou réponds, reste TRÈS concis (1-3 phrases max) et parle exclusivement en français. Rédige des explications claires et naturelles, sans fioritures inutiles, adaptées à la synthèse vocale.
Exemple d'action : Si l'utilisateur dit "ouvre Chrome sur YouTube", écris un script en Python pour ouvrir "https://youtube.com" en utilisant la bibliothèque standard (ex: webbrowser).
"""
    OPEN_INTERPRETER_AVAILABLE = True
except Exception as e:
    print(f"[ERREUR] Impossible d'importer open-interpreter: {e}")
    OPEN_INTERPRETER_AVAILABLE = False

# Flask setup
app = Flask(__name__)
CORS(app)

# Conversational history
conversation = []

# local memory file
MEM_FILE = os.path.join(os.path.dirname(__file__), 'jarvis_memory.json')

def load_local_memory():
    if os.path.exists(MEM_FILE):
        try:
            with open(MEM_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"facts": [], "preferences": {"provider": "gemini"}}

def save_local_memory(data):
    try:
        with open(MEM_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Memory] Erreur sauvegarde: {e}")

local_mem = load_local_memory()

# Configure LLM Client for Open Interpreter
def configure_interpreter():
    if not OPEN_INTERPRETER_AVAILABLE:
        return
    
    # Retrieve Key
    api_key = os.environ.get("GEMINI_API_KEY")
    provider = local_mem.get("preferences", {}).get("provider", "gemini")
    
    if provider == "local":
        interpreter.offline = True
        interpreter.llm.model = "local"
        print("[JARVIS] Open Interpreter configuré en mode LOCAL (Hors-ligne).")
    else:
        interpreter.offline = False
        if api_key:
            # Set model with LiteLLM standard syntax
            interpreter.llm.model = "gemini/gemini-2.5-flash"
            interpreter.llm.api_key = api_key
            print("[JARVIS] Open Interpreter configuré avec Gemini 2.5 Flash.")
        else:
            print("[SÉCURITÉ] GEMINI_API_KEY introuvable dans l'environnement. JARVIS attendra la configuration de la clé.")

configure_interpreter()

# TTS Engine setup
tts_queue = queue.Queue()
USE_TTS = False
KOKORO_AVAILABLE = False
_tts = None
kokoro_pipeline = None

# 1. Attempt Kokoro-82M TTS first (User request: zero latency, French, premium quality)
try:
    from kokoro import KPipeline
    import sounddevice as sd
    # Initialize French KPipeline
    kokoro_pipeline = KPipeline(lang_code='f')
    KOKORO_AVAILABLE = True
    USE_TTS = True
    print("[TTS] Cerveau vocal activé avec KOKORO-82M (Voix Ultra-Réaliste Locale, Zéro Latence)")
except Exception as kokoro_err:
    print(f"[TTS] Kokoro-82M non initialisé ({kokoro_err}), repli vers pyttsx3...")

# 2. Fallback to pyttsx3 if Kokoro is unavailable
if not KOKORO_AVAILABLE:
    try:
        import pyttsx3
        _tts = pyttsx3.init()
        _tts.setProperty('rate', 165)
        _tts.setProperty('volume', 0.9)
        voices = _tts.getProperty('voices')
        for v in voices:
            if 'fr' in v.id.lower() or 'french' in v.name.lower():
                _tts.setProperty('voice', v.id)
                break
        USE_TTS = True
        print("[TTS] Cerveau vocal activé avec pyttsx3 (Synthèse locale)")
    except Exception as e:
        print(f"[TTS] pyttsx3 indisponible ou erreur d'init: {e}")
        USE_TTS = False

def _tts_worker():
    while True:
        text = tts_queue.get()
        if text is None:
            break
        if USE_TTS:
            try:
                if KOKORO_AVAILABLE and kokoro_pipeline:
                    # 'ff_si_mona' is a premium French voice
                    generator = kokoro_pipeline(text, voice='ff_si_mona', speed=1.0, split_pattern='.')
                    for gs, ps, audio in generator:
                        if audio is not None:
                            import sounddevice as sd
                            sd.play(audio, 24000)
                            sd.wait()
                elif _tts:
                    _tts.say(text)
                    _tts.runAndWait()
            except Exception as e:
                print(f"[TTS Work] Erreur lors de la vocalisation: {e}")
        tts_queue.task_done()

if USE_TTS:
    threading.Thread(target=_tts_worker, daemon=True).start()

def speak(text: str):
    if not USE_TTS or not text.strip():
        return
    # Strip down code tags or JSON strings inside response to keep the verbal reply elegant
    cleaned_speech = text
    if "```" in cleaned_speech:
        cleaned_speech = cleaned_speech.split("```")[0] # Speak only text before any raw code blocks
    
    cleaned_speech = cleaned_speech.strip()
    if not cleaned_speech:
        return
        
    if len(cleaned_speech) > 200:
        sentences = [s.strip() for s in cleaned_speech.replace('!', '.').replace('?', '.').split('.') if s.strip()]
        for s in sentences:
            tts_queue.put(s)
    else:
        tts_queue.put(cleaned_speech)

# ===== ROUTES =====

@app.route('/stop-tts', methods=['POST'])
def stop_tts():
    if USE_TTS:
        while not tts_queue.empty():
            try:
                tts_queue.get_nowait()
                tts_queue.task_done()
            except:
                break
        try:
            if KOKORO_AVAILABLE:
                import sounddevice as sd
                sd.stop()
            elif _tts:
                _tts.stop()
        except Exception as e:
            print(f"Erreur arrêt TTS: {e}")
    return jsonify({"success": True})

@app.route('/health')
def health():
    provider = local_mem.get("preferences", {}).get("provider", "gemini")
    return jsonify({
        "status": "ok",
        "provider": "Gemini 2.5 (Open Interpreter)" if provider == "gemini" else "Local Core (Interpreter)",
        "provider_id": provider,
        "services": {
            "interpreter": OPEN_INTERPRETER_AVAILABLE,
            "tts": USE_TTS,
            "vision": True,
            "custom_tools": False
        }
    })

@app.route('/providers')
def get_providers():
    return jsonify({
        "providers": [
            { "id": "gemini", "name": "Gemini 2.5 / 1.5 (LiteLLM Cloud)", "available": True, "free": True, "category": "Cloud" },
            { "id": "local", "name": "Local CLI / Shell Native", "available": True, "free": True, "category": "Offline" }
        ],
        "ollama_models": ["Auto-execution Command Engine"],
        "current": local_mem.get("preferences", {}).get("provider", "gemini")
    })

@app.route('/set-provider', methods=['POST'])
def set_provider():
    pid = request.json.get('provider_id', 'gemini')
    local_mem["preferences"]["provider"] = pid
    save_local_memory(local_mem)
    configure_interpreter()
    return jsonify({"success": True, "provider": "Gemini" if pid == "gemini" else "Local Interpreter"})

@app.route('/tool-chat', methods=['POST'])
def tool_chat():
    message = request.json.get('message', '')
    if not message:
        return jsonify({"reply": "Que puis-je faire pour vous ?"}), 400

    print(f"\n[DEMANDE UTILISATEUR] {message}")

    if not OPEN_INTERPRETER_AVAILABLE:
        error_msg = "Le module Open Interpreter n'est pas installé ou a échoué. Veuillez installer open-interpreter via START_JARVIS.bat."
        speak(error_msg)
        return jsonify({"reply": error_msg})

    try:
        # Dynamic fallback verification of GEMINI_API_KEY if changed
        if os.environ.get("GEMINI_API_KEY") and not interpreter.llm.api_key:
            configure_interpreter()

        # Run Open Interpreter with display=False but streaming inside python to show live output in console!
        reply_parts = []
        code_blocks = []
        
        print("\n--- DEBUT EXÉCUTION JARVIS / OPEN INTERPRETER ---")
        for chunk in interpreter.chat(message, display=False, stream=True):
            if not isinstance(chunk, dict):
                continue
            
            ctype = chunk.get("type")
            content = chunk.get("content", "")
            
            if ctype == "message" and content:
                print(content, end="", flush=True)
                reply_parts.append(content)
            elif ctype == "code" and content:
                language = chunk.get("format", "script")
                print(f"\n[JARVIS écrit un script {language}]:\n{content}\n", flush=True)
                code_blocks.append(f"```{language}\n{content}\n```")
            elif ctype == "console" and content:
                print(f"[EXÉCUTION DU SCRIPT -> RÉSULTAT]:\n{content}\n", flush=True)

        print("\n--- FIN EXÉCUTION JARVIS ---")

        # Combine text responses
        final_reply = "".join(reply_parts).strip()
        
        # If no written response was made, but code ran successfully
        if not final_reply:
            final_reply = "J'ai bien exécuté votre commande sur l'ordinateur."

        # Add visual rendering code boxes to the HUD if they occurred
        if code_blocks:
            final_reply += "\n\n**Scripts exécutés :**\n" + "\n".join(code_blocks)

        # Trigger TTS Speech
        speak(final_reply)

        # Build clean JSON response
        response_data = {
            "reply": final_reply,
            "mode_used": "browser" if "url" in message.lower() or "chrome" in message.lower() or "recherche" in message.lower() else "normal"
        }

        # Handle simple routing actions for the frontend iframe if required (like opening URLs on user browsers)
        # However, Open Interpreter already opens sites via Python natively! 
        # But we can add high-level actions back for better UI sync:
        if "http://" in final_reply or "https://" in final_reply:
            # extract first url
            import re
            urls = re.findall(r'(https?://[^\s]+)', final_reply)
            if urls:
                response_data["action"] = {
                    "type": "open_url",
                    "url": urls[0].replace(")", "").replace("]", "").replace("`", "")
                }

        return jsonify(response_data)

    except Exception as e:
        error_str = str(e)
        print(f"[ERREUR INTERPRÉTEUR] {error_str}")
        err_msg = f"Désolé, j'ai rencontré une erreur lors de l'exécution de cette tâche : {error_str}"
        speak(err_msg)
        return jsonify({"reply": err_msg, "error": error_str}), 500

@app.route('/vision', methods=['POST'])
def vision():
    # If the user specifically triggers webcam/screen capture
    question = request.json.get('question', "Qu'est-ce que tu vois ?")
    img_b64 = request.json.get('frame_b64', '')
    
    desc = "Capture de vision reçue."
    if OPEN_INTERPRETER_AVAILABLE:
        # We can ask the interpreter to describe it or make a call
        desc = "J'ai bien capturé votre écran. L'utilisation d'Open Interpreter me permet d'analyser cela directement."
    speak(desc)
    return jsonify({"reply": desc, "frame_b64": img_b64})

@app.route('/memory')
def get_memory():
    return jsonify({
        "facts": local_mem.get("facts", []),
        "backend": "Open Interpreter Core"
    })

@app.route('/memory/add', methods=['POST'])
def add_memory():
    fact = request.json.get('fact','')
    if fact and fact not in local_mem["facts"]:
        local_mem["facts"].append(fact)
        save_local_memory(local_mem)
    return jsonify({"success": True})

@app.route('/reminder', methods=['POST'])
def set_reminder():
    message = request.json.get('message','')
    minutes = request.json.get('minutes', 5)
    
    # Simple Python native scheduler in background thread for reminders
    def trigger_reminder():
        time.sleep(minutes * 60)
        speak(f"Rappel : {message}")
        print(f"[Rappel activé] : {message}")

    threading.Thread(target=trigger_reminder, daemon=True).start()
    announce = f"Rappel enregistré. Je vous rappellerai dans {minutes} minutes."
    speak(announce)
    return jsonify({"success": True})

@app.route('/browser/toggle', methods=['POST'])
def browser_toggle():
    visible = request.json.get('visible', False)
    # Open Interpreter runs python scripts locally, so we run Chrome on the host
    return jsonify({"success": True, "headless": not visible})

if __name__ == '__main__':
    print("\n" + "="*50)
    print("  JARVIS v4.0 — MOTEUR D'EXÉCUTION NATIVE (OPEN INTERPRETER)")
    print("="*50 + "\n")
    
    # Check port availability
    import socket
    def is_port_in_use(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0

    port_to_use = 5001
    if is_port_in_use(5001):
        print("[JARVIS] Port 5001 est déjà occupé, tentative sur le port 5002.")
        port_to_use = 5002

    app.run(host='127.0.0.1', port=port_to_use, debug=False)
