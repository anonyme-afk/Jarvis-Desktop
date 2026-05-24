from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import re
from datetime import datetime

from providers import ai

app = Flask(__name__)
CORS(app)

conversation = []

def speak(text):
    print(f"[JARVIS SPEAK]: {text}")
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        pass

def detect_mode(message: str) -> dict:
    """
    Analyse le message et retourne le mode optimal.
    Retourne: {"mode": str, "reason": str, "model_override": str|None}
    """
    msg = message.lower().strip()
    now = datetime.now()

    # ===== BROWSER CHAT =====
    browser_triggers = [
        "demande à gemini", "dis à chatgpt", "demande à claude",
        "ouvre gemini", "ouvre chatgpt", "ouvre claude",
        "ask gemini", "ask chatgpt", "via chatgpt", "sur gemini"
    ]
    for t in browser_triggers:
        if t in msg:
            site = "gemini"
            if "chatgpt" in msg or "gpt" in msg: site = "chatgpt"
            elif "claude" in msg: site = "claude"
            elif "perplexity" in msg: site = "perplexity"
            return {"mode": "browser", "site": site, "reason": f"Navigation vers {site}"}

    # ===== RECHERCHE WEB =====
    web_triggers = [
        "aujourd'hui", "maintenant", "actuellement", "en ce moment",
        "dernières nouvelles", "actualité", "récent", "ce matin",
        "cette semaine", "prix de", "cours de", "météo", "température",
        "qui est le président", "résultat de", "score", "match",
        "est-ce que", "vient de", str(now.year), str(now.year - 1)
    ]
    if any(t in msg for t in web_triggers):
        return {"mode": "web_search", "reason": "Information récente détectée", "model_override": None}

    # ===== VISION / CAMÉRA =====
    vision_triggers = [
        "regarde", "vois", "que vois-tu", "qu'est-ce que tu vois",
        "analyse l'écran", "capture", "screenshot", "photo", "image",
        "ce que je tiens", "devant la caméra", "lis ce que"
    ]
    if any(t in msg for t in vision_triggers):
        return {"mode": "vision", "reason": "Analyse visuelle demandée", "model_override": None}

    # ===== RÉFLEXION PROFONDE =====
    deep_triggers = [
        "explique en détail", "analyse complète", "code", "programme",
        "algorithme", "débogage", "bug", "erreur dans mon code",
        "stratégie", "plan détaillé", "compare", "avantages et inconvénients",
        "dissertation", "essai", "raisonne", "étape par étape",
        "comment fonctionne", "pourquoi est-ce que", "philosophie",
        "mathématiques", "calcul complexe", "résous", "démontre"
    ]
    deep_score = sum(1 for t in deep_triggers if t in msg)
    if deep_score >= 1 or len(message) > 200:
        # Choisir un modèle de raisonnement si dispo
        from providers import PROVIDERS
        reasoning_models = ["gpt-o3-mini", "deepseek-r1", "groq-llama3-70b", "gemini-3.1-pro"]
        model_override = None
        for m in reasoning_models:
            if os.environ.get(PROVIDERS.get(m, {}).get("env_key", ""), ""):
                model_override = m
                break
        return {"mode": "deep_think", "reason": "Raisonnement complexe détecté",
                "model_override": model_override}

    # ===== RÉPONSE RAPIDE =====
    quick_triggers = [
        "heure", "date", "quelle heure", "quel jour",
        "ouvre", "lance", "ferme", "mets", "coupe le son",
        "volume", "pause", "stop", "joue"
    ]
    if any(t in msg for t in quick_triggers):
        return {"mode": "quick", "reason": "Action simple", "model_override": "gemini-3.5-flash"}

    # Par défaut : réponse normale
    return {"mode": "normal", "reason": "Conversation standard", "model_override": None}

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "provider": ai.provider_id,
        "services": {"mem0": "disabled"}
    })

@app.route('/browser/chat', methods=['POST'])
def browser_chat():
    try:
        from browser_agent import browser_agent
        site = request.json.get('site', 'gemini')
        message = request.json.get('message', '')
        result = browser_agent.run(site, message)
        if result.get('reply'):
            speak(result['reply'][:300])
        return jsonify(result)
    except Exception as e:
        return jsonify({"reply": f"Erreur: {str(e)}", "success": False})

@app.route('/tool-chat', methods=['POST'])
def tool_chat():
    global conversation
    message = request.json.get('message', '')
    if not message:
        return jsonify({"reply": "Message vide.", "action": None})

    # DÉTECTION AUTOMATIQUE DU MODE
    mode_info = detect_mode(message)
    mode = mode_info["mode"]
    print(f"[MODE] {mode} — {mode_info['reason']}")

    # Changer de modèle si recommandé
    original_provider = ai.provider_id
    if mode_info.get("model_override"):
        try:
            ai.set_provider(mode_info["model_override"])
        except:
            pass

    result = None

    try:
        if mode == "browser":
            from browser_agent import browser_agent
            site = mode_info.get("site", "gemini")
            result = browser_agent.run(site, message)
            reply = result.get("reply", "Navigation échouée.")
            speak(reply[:300])
            return jsonify({"reply": reply, "action": None,
                           "mode_used": "browser", "site": site})

        elif mode == "web_search":
            try:
                from tools.search_tool import web_search, format_results_for_ai
                results = web_search(message, max_results=5)
                context = format_results_for_ai(results)
                enriched = f"Résultats web pour '{message}':\n{context}\n\nRéponds en 2-3 phrases."
                reply = ai.chat([{"role": "user", "content": enriched}])
            except:
                reply = ai.chat([{"role": "user", "content": message}])
            speak(reply)
            conversation.append({"role": "user", "content": message})
            conversation.append({"role": "assistant", "content": reply})
            return jsonify({"reply": reply, "action": None, "mode_used": "web_search"})

        elif mode == "vision":
            import cv2, base64 as b64
            try:
                cap = cv2.VideoCapture(0)
                ret, frame = cap.read()
                cap.release()
                if ret:
                    _, buf = cv2.imencode('.jpg', frame)
                    img_b64 = b64.b64encode(buf.tobytes()).decode()
                    reply = ai.chat([{"role": "user", "content": message}], image_b64=img_b64)
                else:
                    reply = "Je ne peux pas accéder à la caméra."
            except Exception as e:
                reply = f"Erreur de vision: {e}"
            speak(reply)
            return jsonify({"reply": reply, "action": None, "mode_used": "vision"})

        elif mode == "deep_think":
            # Prompt enrichi pour la réflexion profonde
            deep_prompt = f"Analyse cette demande en profondeur et réponds de façon structurée.\nSois précis et complet. Utilise des étapes si nécessaire.\nQuestion: {message}"
            reply = ai.chat([{"role": "user", "content": deep_prompt}])
            speak(reply[:400])
            conversation.append({"role": "user", "content": message})
            conversation.append({"role": "assistant", "content": reply})
            return jsonify({"reply": reply, "action": None, "mode_used": "deep_think"})

        else:
            # Normal ou quick : chat standard
            conversation.append({"role": "user", "content": message})
            if len(conversation) > 20:
                conversation.pop(0)
            reply = ai.chat(conversation[-10:])
            conversation.append({"role": "assistant", "content": reply})
            action = None
            if reply.strip().startswith('{'):
                try:
                    action = json.loads(reply.strip())
                    reply = "Bien sûr."
                except:
                    pass
            speak(reply)
            return jsonify({"reply": reply, "action": action, "mode_used": mode})

    finally:
        # Restaurer le provider original
        if mode_info.get("model_override"):
            ai.set_provider(original_provider)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
