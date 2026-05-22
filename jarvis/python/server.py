import os
import json
import base64
import threading
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import speech_recognition as sr
import cv2

try:
    import pyttsx3
    tts_engine = pyttsx3.init()
    tts_engine.setProperty('rate', 165)
    tts_engine.setProperty('volume', 0.9)
    USE_PYTTSX3 = True
except:
    USE_PYTTSX3 = False

app = Flask(__name__)
CORS(app)

# Configuration for models
USE_LOCAL_MODEL = os.environ.get('USE_LOCAL_MODEL', 'false').lower() == 'true'

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
# Initialize models even if key is missing, to allow local fallback logic to proceed
model = genai.GenerativeModel('gemini-1.5-pro') if GEMINI_API_KEY else None
vision_model = genai.GenerativeModel('gemini-1.5-pro-vision') if GEMINI_API_KEY else None

conversation_history = []

SYSTEM_PROMPT = """
Tu es JARVIS, l'assistant IA de l'utilisateur. Tu es calme, précis, légèrement formel
mais jamais condescendant. Tu parles comme l'IA dans Iron Man : concis, factuel,
avec parfois une touche d'humour sec. Tu peux :
- Répondre à des questions
- Ouvrir des sites web (réponds avec un JSON {"action":"open_url","url":"..."})
- Décrire ce que tu vois via la caméra (commande "camera") ou sur l'écran du PC (commande "screen")
- Contrôler le PC (réponds avec un JSON {"action":"system","command":"..."})
- Chercher des infos
Sois bref. 1-3 phrases max sauf si on demande plus de détails.
Si on dit "ouvre [site]", "montre-moi [lieu]", "que vois-tu sur l'écran" ou active la vision, réponds avec un JSON. 
Exemples: {"action":"open_url","url":"https://maps.google.com"}, {"action":"system", "command":"camera"}, {"action":"system", "command":"screen"}
Ne réponds que le JSON si l'intention est technique, pour faciliter le parsing.
"""

def generate_local_response(history_text):
    """Fallback to local Ollama API"""
    try:
        res = requests.post("http://localhost:11434/api/generate", json={
            "model": "llama3",  # or adjust to your local model
            "prompt": history_text,
            "stream": False,
            "system": SYSTEM_PROMPT
        }, timeout=8)
        if res.status_code == 200:
            return res.json().get("response", "")
    except Exception as e:
        print(f"[Ollama Error] {e}")
    return None

def generate_gemini_response(prompt_messages):
    """Use Gemini API"""
    if not model:
        raise Exception("API Gemini non configurée (clé manquante)")
    response = model.generate_content(prompt_messages)
    return response.text

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')

    conversation_history.append({
        "role": "user",
        "parts": [user_message]
    })

    if len(conversation_history) > 20:
        conversation_history.pop(0)

    try:
        reply = None
        current_model = "gemini-1.5-pro"
        
        if USE_LOCAL_MODEL:
            history_text = "\n".join([f"{'User' if m['role'] == 'user' else 'JARVIS'}: {m['parts'][0]}" for m in conversation_history])
            reply = generate_local_response(history_text)
            if reply: current_model = "ollama-local"
            
        if not reply:
             prompt_messages = [SYSTEM_PROMPT] + [f"{'User' if m['role'] == 'user' else 'JARVIS'}: {m['parts'][0]}" for m in conversation_history]
             reply = generate_gemini_response(prompt_messages)
             current_model = "gemini-1.5-pro"

        conversation_history.append({
            "role": "model",
            "parts": [reply]
        })

        if USE_PYTTSX3:
            threading.Thread(target=speak, args=(reply,), daemon=True).start()

        action = None
        if reply.strip().startswith('{'):
            try:
                # Attempt to parse json from the reply
                start_idx = reply.find('{')
                end_idx = reply.rfind('}') + 1
                json_str = reply[start_idx:end_idx]
                action = json.loads(json_str)
                reply = reply[:start_idx].strip()
                if not reply:
                    reply = "Bien sûr. J'exécute l'action."
            except Exception as e:
                print(f"[JSON Parse Error] {e}")
                pass

        return jsonify({
            "reply": reply,
            "action": action,
            "model_used": current_model
        })

    except Exception as e:
        return jsonify({"reply": f"Erreur de communication : {str(e)}", "action": None}), 500

@app.route('/vision', methods=['POST'])
def analyze_vision():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return jsonify({"reply": "Je n'arrive pas à accéder à la caméra."})

    _, buffer = cv2.imencode('.jpg', frame)
    image_bytes = buffer.tobytes()
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')

    question = request.json.get('question', "Qu'est-ce que tu vois ? Décris en détail mais sois concis.")

    try:
        if not vision_model:
            raise Exception("Modèle Vision non configuré")
            
        response = vision_model.generate_content([
            f"{SYSTEM_PROMPT}\n{question}",
            {
                "mime_type": "image/jpeg",
                "data": image_b64
            }
        ])
        reply = response.text
        if USE_PYTTSX3:
            threading.Thread(target=speak, args=(reply,), daemon=True).start()
        return jsonify({"reply": reply, "frame_b64": image_b64})
    except Exception as e:
        return jsonify({"reply": f"Erreur d'analyse visuelle : {str(e)}"}), 500

@app.route('/vision/screen', methods=['POST'])
def analyze_screen():
    try:
        from PIL import ImageGrab
        import io
        screenshot = ImageGrab.grab()
        screenshot = screenshot.convert("RGB")
        buffer = io.BytesIO()
        screenshot.save(buffer, format="JPEG")
        image_bytes = buffer.getvalue()
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')

        question = request.json.get('question', "Que vois-tu à l'écran ? Décris-le brièvement.")

        if not vision_model:
            raise Exception("Modèle Vision non configuré")
            
        response = vision_model.generate_content([
            f"{SYSTEM_PROMPT}\n{question}",
            {
                "mime_type": "image/jpeg",
                "data": image_b64
            }
        ])
        reply = response.text
        if USE_PYTTSX3:
            threading.Thread(target=speak, args=(reply,), daemon=True).start()
        return jsonify({"reply": reply, "frame_b64": image_b64})
    except Exception as e:
        return jsonify({"reply": f"Erreur d'analyse d'écran : {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok", 
        "model": "ollama-local" if USE_LOCAL_MODEL else "gemini-1.5-pro",
        "gemini_configured": bool(GEMINI_API_KEY)
    })

def speak(text):
    if USE_PYTTSX3:
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
        except:
            pass

if __name__ == '__main__':
    print(f"[JARVIS] Serveur Python démarré sur port 5001. Local Model: {USE_LOCAL_MODEL}")
    app.run(host='127.0.0.1', port=5001, debug=False)
