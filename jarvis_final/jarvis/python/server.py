"""
JARVIS Desktop — Serveur Python Principal v3.0
Intègre : Multi-API, OSINT, Vision, NFC, Gaming, VAD, Scheduler, Mem0, Notifier
"""
import os, json, threading, time
from flask import Flask, request, jsonify
from flask_cors import CORS
from providers import ai, PROVIDERS
from memory import memory
from mem0_manager import advanced_memory
from plugins import find_plugin
from tools.tool_registry import executor, TOOLS_SCHEMA
from osint_engine import osint
from gaming_controller import gaming
from browser_agent import browser_agent
from notifier import notifier
from scheduler import JARVISScheduler
from vad_manager import vad
from vision_engine import get_frame_b64, VisionSurveillance
from nfc_manager import nfc_manager
import cv2, base64

app  = Flask(__name__)
CORS(app)
conversation = []

import queue

# TTS
tts_queue = queue.Queue()
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
except:
    USE_TTS = False

def _tts_worker():
    while True:
        text = tts_queue.get()
        if text is None: break
        if USE_TTS and not vad.interrupt_event.is_set():
            vad.set_ai_speaking(True)
            try:
                _tts.say(text)
                _tts.runAndWait()
            except Exception as e:
                print(f"[TTS] Erreur: {e}")
            vad.set_ai_speaking(False)
        tts_queue.task_done()

if USE_TTS:
    threading.Thread(target=_tts_worker, daemon=True).start()

def speak(text: str):
    if not USE_TTS: return
    # Coupe les longues phrases
    if len(text) > 200:
        sentences = [s.strip() for s in text.replace('!', '.').replace('?', '.').split('.') if s.strip()]
        for s in sentences:
            tts_queue.put(s)
    else:
        tts_queue.put(text)

# ===== CALLBACK VISION =====
def on_vision_event(event_type: str, data):
    if event_type == "face_recognized":
        if data != "inconnu":
            speak(f"Bienvenue, {data}. Système déverrouillé.")
            notifier.notify("JARVIS", f"Visage reconnu: {data}")
        else:
            speak("Attention. Personne non reconnue détectée.")
    elif event_type == "intruder_detected":
        speak("Alerte. Intrusion détectée dans le laboratoire.")
        notifier.notify("JARVIS - ALERTE", "Intrusion détectée !", urgent=True)
    elif event_type == "gesture":
        gesture_actions = {
            "open_hand": lambda: speak("Mise en pause."),
            "fist":      lambda: speak("Audio coupé."),
            "peace":     lambda: speak("Screenshot pris.")
        }
        if data in gesture_actions:
            gesture_actions[data]()

# ===== CALLBACK PROACTIVITÉ =====
def on_proactive_message(message: str, priority: str):
    if priority == "wake_screen":
        with app.app_context():
            pass  # Envoyer via WebSocket dans une version future
    speak(message)
    notifier.notify("JARVIS", message, urgent=(priority == "urgent"))

# ===== CALLBACK NFC =====
def on_nfc_card(uid: str, profile: dict):
    speak(f"Carte détectée. Activation du profil {profile.get('name', 'inconnu')}.")
    nfc_manager.execute_profile_actions(profile)

# ===== BACKGROUND CLEANUP =====
def _background_tasks():
    while True:
        time.sleep(300) # 5 minutes
        memory.save()
        if len(conversation) > 0:
            # Nettoyage si très inactif (on simplifie)
            pass

threading.Thread(target=_background_tasks, daemon=True).start()

# ===== DÉMARRAGE DES SERVICES EN FOND =====
def start_background_services():
    global vision_surv, jarvis_scheduler
    # Vision
    vision_surv = VisionSurveillance(callback=on_vision_event)
    vision_surv.start()
    # NFC
    nfc_manager.on_card_detected = on_nfc_card
    nfc_manager.start_listening()
    # VAD
    vad.start_listening()
    # Scheduler
    jarvis_scheduler = JARVISScheduler(on_proactive_message)
    jarvis_scheduler.start()
    print("[JARVIS] Tous les services démarrés")

threading.Thread(target=start_background_services, daemon=True).start()

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
            _tts.stop()
        except:
            pass
        vad.interrupt_event.set()
        time.sleep(0.5)
        vad.interrupt_event.clear()
        vad.set_ai_speaking(False)
    return jsonify({"success": True})

@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "provider": ai.current['name'],
        "provider_id": ai.provider_id,
        "services": {
            "vision": True,
            "nfc": True,
            "vad": vad.model is not None,
            "mem0": advanced_memory.backend,
            "browser_agent": browser_agent.available
        }
    })

@app.route('/providers')
def get_providers():
    return jsonify({
        "providers": ai.get_available_providers(),
        "ollama_models": ai.get_ollama_models()
    })

@app.route('/set-provider', methods=['POST'])
def set_provider():
    pid = request.json.get('provider_id')
    ai.set_provider(pid)
    memory.set_preference('provider', pid)
    return jsonify({"success": True, "provider": ai.current['name']})

@app.route('/tool-chat', methods=['POST'])
def tool_chat():
    global conversation
    message = request.json.get('message', '')

    # Mémoriser les faits
    for fact in memory.extract_facts_from_message(message):
        memory.add_fact(fact)
        advanced_memory.add(fact)

    # Contexte mémoire
    mem_ctx = advanced_memory.get_context_for_prompt(message)

    # Plugins en premier
    plugin = find_plugin(message)
    if plugin:
        result = plugin.handle(message, {"history": conversation})
        if result.get('reply'):
            speak(result['reply'])
            return jsonify(result)

    # Tool calling
    tool_prompt = f"""
Tu es JARVIS. Contexte mémorisé: {mem_ctx}

Outils disponibles: {json.dumps(TOOLS_SCHEMA[:8], ensure_ascii=False)}

Outils OSINT: lookup_ip(ip), whois_domain(domain), check_email_breach(email),
              search_username(username), dns_lookup(domain), port_scan(host)

Outils Gaming: analyze_game_state(), auto_farm(key, interval, duration)

Navigation web autonome: browser_task(task)

Réponds avec JSON:
  {{"tool": "nom", "params": {{...}}}}
  ou {{"reply": "réponse directe"}}

Message: {message}
"""
    try:
        raw = ai.chat([{"role": "user", "content": tool_prompt}]).strip()
        if raw.startswith('```'):
            raw = raw.split('\n',1)[1].rsplit('```',1)[0]
        decision = json.loads(raw)

        if "reply" in decision:
            reply_text = decision["reply"]
            conversation.append({"role":"user","content":message})
            conversation.append({"role":"assistant","content":reply_text})
            conversation = conversation[-10:]
            advanced_memory.add(f"User: {message} | JARVIS: {reply_text[:100]}")
            
            def generate():
                speak(reply_text)
                words = reply_text.split(" ")
                for i, w in enumerate(words):
                    time.sleep(0.05) # Simulation de stream progressif
                    yield json.dumps({"type": "chunk", "text": w + (" " if i < len(words)-1 else "")}) + "\n"
                yield json.dumps({"type": "done"}) + "\n"
                
            return app.response_class(generate(), mimetype='application/x-ndjson')

        tool_name = decision.get('tool')
        params = decision.get('params', {})

        # Router vers le bon module
        if tool_name in ['lookup_ip','whois_domain','check_email_breach',
                         'search_username','dns_lookup','port_scan','analyze_file_metadata']:
            result = getattr(osint, tool_name)(**params)
        elif tool_name == 'analyze_game_state':
            result = {"summary": gaming.analyze_game_state(ai)}
        elif tool_name == 'browser_task':
            result = {"summary": browser_agent.run_task(params.get('task',''))}
        else:
            result = executor.execute(tool_name, params)

        summary = result.get("summary", json.dumps(result, ensure_ascii=False)[:300])
        reply_text = ai.chat([{"role":"user","content":f"Résume en 1-2 phrases l'action effectuée sans dire que c'est un résumé: {summary}"}])
        action = result.get("action", None)

        def generate_tool():
            speak(reply_text)
            words = reply_text.split(" ")
            for i, w in enumerate(words):
                time.sleep(0.05)
                yield json.dumps({"type": "chunk", "text": w + (" " if i < len(words)-1 else "")}) + "\n"
            yield json.dumps({"type": "done", "action": action, "tool_used": tool_name}) + "\n"

        return app.response_class(generate_tool(), mimetype='application/x-ndjson')

    except json.JSONDecodeError:
        # Réponse directe sans outil
        reply_text = ai.chat(conversation + [{"role":"user","content":message}])
        conversation.append({"role":"user","content":message})
        conversation.append({"role":"assistant","content":reply_text})
        conversation = conversation[-10:]
        def generate_direct():
            speak(reply_text)
            words = reply_text.split(" ")
            for i, w in enumerate(words):
                time.sleep(0.05)
                yield json.dumps({"type": "chunk", "text": w + (" " if i < len(words)-1 else "")}) + "\n"
            yield json.dumps({"type": "done"}) + "\n"
            
        return app.response_class(generate_direct(), mimetype='application/x-ndjson')
    except Exception as e:
        return jsonify({"reply": f"Erreur: {str(e)}", "action": None}), 500

@app.route('/vision', methods=['POST'])
def vision():
    cam_idx = request.json.get('camera_index', 0)
    question = request.json.get('question', "Qu'est-ce que tu vois ?")
    img_b64 = get_frame_b64(cam_idx)
    if not img_b64:
        return jsonify({"reply": "Caméra inaccessible."})
    if not ai.current.get('vision'):
        original = ai.provider_id
        ai.set_provider('gemini-free')
        reply = ai.chat([{"role":"user","content":question}], image_b64=img_b64)
        ai.set_provider(original)
    else:
        reply = ai.chat([{"role":"user","content":question}], image_b64=img_b64)
    speak(reply)
    return jsonify({"reply": reply, "frame_b64": img_b64})

@app.route('/memory')
def get_memory():
    return jsonify({**memory.data, "backend": advanced_memory.backend})

@app.route('/memory/add', methods=['POST'])
def add_memory():
    fact = request.json.get('fact','')
    if fact:
        memory.add_fact(fact)
        advanced_memory.add(fact)
    return jsonify({"success": True})

@app.route('/osint/ip', methods=['POST'])
def osint_ip():
    ip = request.json.get('ip','')
    return jsonify(osint.lookup_ip(ip))

@app.route('/osint/username', methods=['POST'])
def osint_username():
    username = request.json.get('username','')
    return jsonify(osint.search_username(username))

@app.route('/reminder', methods=['POST'])
def set_reminder():
    message = request.json.get('message','')
    minutes = request.json.get('minutes', 5)
    jarvis_scheduler.add_reminder(message, minutes)
    return jsonify({"success": True})

@app.route('/gaming/analyze', methods=['POST'])
def gaming_analyze():
    result = gaming.analyze_game_state(ai)
    speak(result)
    return jsonify({"reply": result})

@app.route('/browser/task', methods=['POST'])
def browser_task():
    task = request.json.get('task','')
    result = browser_agent.run_task(task)
    speak(result)
    return jsonify({"reply": result})

if __name__ == '__main__':
    saved_provider = memory.get_preference('provider')
    if saved_provider:
        ai.set_provider(saved_provider)
    print(f"[JARVIS] v3.0 — Provider: {ai.current['name']}")
    
    import socket
    def is_port_in_use(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0

    port_to_use = 5001
    if is_port_in_use(5001):
        print("[JARVIS] Port 5001 occupé, passage au port 5002.")
        port_to_use = 5002

    app.run(host='127.0.0.1', port=port_to_use, debug=False)
