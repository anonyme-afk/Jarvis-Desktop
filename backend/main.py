import asyncio
import re
import threading
import json
import sys
import traceback
import time
from pathlib import Path

import sounddevice as sd
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from memory.memory_manager import (
    load_memory, update_memory, format_memory_for_prompt,
)

from actions.file_processor import file_processor
from actions.flight_finder     import flight_finder
from actions.open_app          import open_app
from actions.weather_report    import weather_action
from actions.send_message      import send_message
from actions.reminder          import reminder
from actions.computer_settings import computer_settings
from actions.screen_processor  import screen_process
from actions.youtube_video     import youtube_video
from actions.desktop           import desktop_control
from actions.browser_control   import browser_control
from actions.file_controller   import file_controller
from actions.code_helper       import code_helper
from actions.dev_agent         import dev_agent
from actions.web_search        import web_search as web_search_action
from actions.computer_control  import computer_control
from actions.game_updater      import game_updater

def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

BASE_DIR        = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
PROMPT_PATH     = BASE_DIR / "core" / "prompt.txt"
LIVE_MODEL          = "models/gemini-2.5-flash-native-audio-preview-12-2025"
CHANNELS            = 1
SEND_SAMPLE_RATE    = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE          = 1024

def _get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key
    
    # Fallback to older config format if .env is missing
    if API_CONFIG_PATH.exists():
        try:
            with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f).get("gemini_api_key", "")
        except Exception:
            pass
            
    return ""

def _load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return (
            "You are JARVIS, Tony Stark's AI assistant. "
            "Be concise, direct, and always use the provided tools to complete tasks. "
            "Never simulate or guess results — always call the appropriate tool."
        )

_CTRL_RE = re.compile(r"<ctrl\d+>", re.IGNORECASE)

def _clean_transcript(text: str) -> str:    
    text = _CTRL_RE.sub("", text)
    text = re.sub(r"[\x00-\x08\x0b-\x1f]", "", text)
    return text.strip()

TOOL_DECLARATIONS = [
  # ═══ SYSTÈME & PC ═══
  {
    "name": "execute_command",
    "description": "Exécute une commande système (cmd/bash). Contrôle total du PC.",
    "parameters": {"type":"object","properties":{
      "command": {"type":"string","description":"La commande à exécuter"},
      "shell": {"type":"boolean","description":"Utiliser le shell système"}
    },"required":["command"]}
  },
  {
    "name": "get_system_info",
    "description": "Obtenir CPU, RAM, disque, batterie, processus, température.",
    "parameters": {"type":"object","properties":{
      "detail": {"type":"string","enum":["cpu","ram","disk","battery","processes","all"]}
    },"required":["detail"]}
  },
  {
    "name": "manage_processes",
    "description": "Lister, tuer ou lancer des processus.",
    "parameters": {"type":"object","properties":{
      "action": {"type":"string","enum":["list","kill","start"]},
      "name": {"type":"string"}
    },"required":["action"]}
  },
  {
    "name": "control_window",
    "description": "Minimiser, maximiser, fermer, focus sur une fenêtre.",
    "parameters": {"type":"object","properties":{
      "action": {"type":"string","enum":["minimize","maximize","close","focus","list"]},
      "window_title": {"type":"string"}
    },"required":["action"]}
  },
  {
    "name": "take_screenshot",
    "description": "Capture d'écran complète ou d'une région.",
    "parameters": {"type":"object","properties":{
      "region": {"type":"string","description":"'full' ou 'window:titre'"},
      "analyze": {"type":"boolean","description":"Analyser avec vision IA après capture"}
    }}
  },
  {
    "name": "control_mouse_keyboard",
    "description": "Déplacer souris, cliquer, taper du texte, raccourcis clavier.",
    "parameters": {"type":"object","properties":{
      "action": {"type":"string","enum":["click","double_click","right_click","move","type","hotkey","scroll"]},
      "x": {"type":"integer"}, "y": {"type":"integer"},
      "text": {"type":"string"},
      "keys": {"type":"array","items":{"type":"string"}}
    },"required":["action"]}
  },

  # ═══ FICHIERS & DOSSIERS ═══
  {
    "name": "manage_files",
    "description": "Lire, écrire, créer, supprimer, déplacer, copier des fichiers.",
    "parameters": {"type":"object","properties":{
      "action": {"type":"string","enum":["read","write","create","delete","move","copy","list","search","exists"]},
      "path": {"type":"string"},
      "content": {"type":"string"},
      "destination": {"type":"string"}
    },"required":["action","path"]}
  },
  {
    "name": "analyze_file",
    "description": "Analyser le contenu d'un fichier PDF, image, code, CSV, Excel.",
    "parameters": {"type":"object","properties":{
      "path": {"type":"string"},
      "question": {"type":"string"}
    },"required":["path"]}
  },
  {
    "name": "manage_clipboard",
    "description": "Lire ou écrire dans le presse-papier.",
    "parameters": {"type":"object","properties":{
      "action": {"type":"string","enum":["read","write","clear"]},
      "content": {"type":"string"}
    },"required":["action"]}
  },

  # ═══ NAVIGATEUR WEB ═══
  {
    "name": "browser_navigate",
    "description": "Ouvrir une URL, cliquer sur des éléments, remplir des formulaires, scraper.",
    "parameters": {"type":"object","properties":{
      "action": {"type":"string","enum":["open","click","fill","scrape","screenshot","back","forward","scroll","find"]},
      "url": {"type":"string"},
      "selector": {"type":"string"},
      "text": {"type":"string"},
      "visible": {"type":"boolean","description":"Rendre Chrome visible ou non"}
    },"required":["action"]}
  },
  {
    "name": "web_search",
    "description": "Recherche DuckDuckGo, Google, Bing. Résultats en temps réel.",
    "parameters": {"type":"object","properties":{
      "query": {"type":"string"},
      "engine": {"type":"string","enum":["duckduckgo","google","bing"],"default":"duckduckgo"},
      "num_results": {"type":"integer","default":5}
    },"required":["query"]}
  },
  {
    "name": "fetch_webpage",
    "description": "Récupérer et lire le contenu d'une page web.",
    "parameters": {"type":"object","properties":{
      "url": {"type":"string"},
      "extract": {"type":"string","enum":["text","links","images","all"],"default":"text"}
    },"required":["url"]}
  },

  # ═══ MÉDIAS & YOUTUBE ═══
  {
    "name": "media_control",
    "description": "Contrôler YouTube, Spotify, VLC. Pause, lecture, volume, recherche.",
    "parameters": {"type":"object","properties":{
      "action": {"type":"string","enum":["play","pause","stop","next","previous","volume","search","download"]},
      "platform": {"type":"string","enum":["youtube","spotify","vlc","system"]},
      "query": {"type":"string"},
      "volume_level": {"type":"integer","minimum":0,"maximum":100}
    },"required":["action"]}
  },
  {
    "name": "download_media",
    "description": "Télécharger vidéo/audio YouTube ou autre site via yt-dlp.",
    "parameters": {"type":"object","properties":{
      "url": {"type":"string"},
      "format": {"type":"string","enum":["mp4","mp3","best"],"default":"best"},
      "output_path": {"type":"string"}
    },"required":["url"]}
  },

  # ═══ COMMUNICATION ═══
  {
    "name": "send_notification",
    "description": "Envoyer notification sur Discord, Telegram, Slack, email.",
    "parameters": {"type":"object","properties":{
      "platform": {"type":"string","enum":["discord","telegram","slack","email","windows"]},
      "message": {"type":"string"},
      "title": {"type":"string"},
      "urgent": {"type":"boolean"}
    },"required":["platform","message"]}
  },
  {
    "name": "send_email",
    "description": "Envoyer un email via Gmail ou SMTP.",
    "parameters": {"type":"object","properties":{
      "to": {"type":"string"},
      "subject": {"type":"string"},
      "body": {"type":"string"},
      "attachments": {"type":"array","items":{"type":"string"}}
    },"required":["to","subject","body"]}
  },

  # ═══ OSINT & SÉCURITÉ ═══
  {
    "name": "osint_lookup",
    "description": "Recherche OSINT : IP, domaine, email, username, numéro de téléphone.",
    "parameters": {"type":"object","properties":{
      "type": {"type":"string","enum":["ip","domain","email","username","phone","image_reverse"]},
      "target": {"type":"string"},
      "deep": {"type":"boolean","description":"Recherche approfondie (plus lent)"}
    },"required":["type","target"]}
  },
  {
    "name": "network_scan",
    "description": "Scanner le réseau local, ports ouverts, appareils connectés.",
    "parameters": {"type":"object","properties":{
      "action": {"type":"string","enum":["scan_network","scan_ports","ping","traceroute","wifi_networks"]},
      "host": {"type":"string"},
      "ports": {"type":"array","items":{"type":"integer"}}
    },"required":["action"]}
  },
  {
    "name": "check_security",
    "description": "Vérifier si email/mot de passe compromis (HaveIBeenPwned), analyser URL.",
    "parameters": {"type":"object","properties":{
      "action": {"type":"string","enum":["check_breach","analyze_url","check_ssl","virustotal"]},
      "target": {"type":"string"}
    },"required":["action","target"]}
  },

  # ═══ HARDWARE AUTO-DÉTECTION ═══
  {
    "name": "detect_hardware",
    "description": "Détecter automatiquement les appareils branchés : USB, caméras, Arduino, Raspberry Pi, NFC, manettes.",
    "parameters": {"type":"object","properties":{
      "type": {"type":"string","enum":["all","usb","cameras","serial","audio","bluetooth","network_devices"]}
    },"required":["type"]}
  },
  {
    "name": "control_hardware",
    "description": "Interagir avec Arduino/Raspberry Pi via USB série, lire capteurs.",
    "parameters": {"type":"object","properties":{
      "action": {"type":"string","enum":["send_serial","read_serial","list_ports","read_sensor"]},
      "port": {"type":"string"},
      "command": {"type":"string"},
      "baudrate": {"type":"integer","default":9600}
    },"required":["action"]}
  },
  {
    "name": "control_camera",
    "description": "Activer webcam, prendre photo, analyser ce que la caméra voit.",
    "parameters": {"type":"object","properties":{
      "action": {"type":"string","enum":["capture","analyze","stream","detect_objects","detect_faces"]},
      "camera_index": {"type":"integer","default":0},
      "question": {"type":"string"}
    },"required":["action"]}
  },

  # ═══ DOMOTIQUE ═══
  {
    "name": "home_assistant",
    "description": "Contrôler les appareils domotiques via Home Assistant.",
    "parameters": {"type":"object","properties":{
      "action": {"type":"string","enum":["turn_on","turn_off","toggle","get_state","list_entities"]},
      "entity_id": {"type":"string"},
      "attributes": {"type":"object"}
    },"required":["action"]}
  },

  # ═══ DONNÉES & ANALYSE ═══
  {
    "name": "data_analysis",
    "description": "Analyser des données CSV/Excel, créer des graphiques, statistiques.",
    "parameters": {"type":"object","properties":{
      "action": {"type":"string","enum":["analyze","chart","stats","clean","export"]},
      "file_path": {"type":"string"},
      "query": {"type":"string"},
      "output_format": {"type":"string","enum":["text","chart","excel","csv"]}
    },"required":["action","file_path"]}
  },
  {
    "name": "get_weather",
    "description": "Météo actuelle et prévisions pour n'importe quelle ville.",
    "parameters": {"type":"object","properties":{
      "city": {"type":"string"},
      "days": {"type":"integer","default":1}
    },"required":["city"]}
  },
  {
    "name": "get_news",
    "description": "Actualités récentes sur n'importe quel sujet.",
    "parameters": {"type":"object","properties":{
      "topic": {"type":"string"},
      "language": {"type":"string","default":"fr"},
      "num_results": {"type":"integer","default":5}
    },"required":["topic"]}
  },
  {
    "name": "wikipedia_search",
    "description": "Rechercher des informations sur Wikipedia.",
    "parameters": {"type":"object","properties":{
      "query": {"type":"string"},
      "lang": {"type":"string","default":"fr"}
    },"required":["query"]}
  },
  {
    "name": "calculate",
    "description": "Calculs mathématiques, conversions, statistiques.",
    "parameters": {"type":"object","properties":{
      "expression": {"type":"string"}
    },"required":["expression"]}
  },

  # ═══ GÉNÉRATION DE CONTENU ═══
  {
    "name": "generate_document",
    "description": "Créer Word, PDF, Excel, Markdown, code source.",
    "parameters": {"type":"object","properties":{
      "type": {"type":"string","enum":["word","pdf","excel","markdown","html","python","javascript"]},
      "content": {"type":"string"},
      "filename": {"type":"string"},
      "output_path": {"type":"string"}
    },"required":["type","content","filename"]}
  },
  {
    "name": "set_reminder",
    "description": "Créer des rappels, alarmes, tâches planifiées.",
    "parameters": {"type":"object","properties":{
      "message": {"type":"string"},
      "delay_minutes": {"type":"integer"},
      "repeat": {"type":"boolean","default":False},
      "cron": {"type":"string","description":"Expression cron pour répétition"}
    },"required":["message","delay_minutes"]}
  },

  # ═══ TÉLÉPHONE ANDROID ═══
  {
    "name": "android_control",
    "description": "Contrôler un téléphone Android branché en USB via ADB.",
    "parameters": {"type":"object","properties":{
      "action": {"type":"string","enum":["screenshot","tap","swipe","type","open_app","volume","brightness","list_apps","call","sms"]},
      "params": {"type":"object"}
    },"required":["action"]}
  },

  # ═══ GIT & CODE ═══
  {
    "name": "git_operations",
    "description": "Opérations Git : clone, commit, push, pull, status.",
    "parameters": {"type":"object","properties":{
      "action": {"type":"string","enum":["clone","commit","push","pull","status","log","branch","checkout"]},
      "repo_path": {"type":"string"},
      "message": {"type":"string"},
      "url": {"type":"string"}
    },"required":["action"]}
  },
  # ═══ RENSEIGNEMENT CENTRAL (GOD MODE / FBI LEVEL) ═══
  {
    "name": "global_threat_intel",
    "description": "Recherche avancée globale via Shodan (moteurs, caméras IP, serveurs vulnérables, systèmes industriels). Niveau NSA.",
    "parameters": {"type":"object","properties":{
      "query": {"type":"string"},
      "type": {"type":"string","enum":["shodan_search","exploit_search"]}
    },"required":["query"]}
  },
  {
    "name": "biometric_and_vision",
    "description": "Analyse biométrique faciale, détection d'objets, OCR et tracking de posture (Iron Man HUD) via MediaPipe et Tesseract.",
    "parameters": {"type":"object","properties":{
      "action": {"type":"string","enum":["detect_faces","read_text","track_pose"]},
      "image_path": {"type":"string"}
    },"required":["action", "image_path"]}
  },
  {
    "name": "advanced_network_recon",
    "description": "Scan réseau profond (Nmap), interception de paquets (Scapy), détection d'intrusions et mapping topologique.",
    "parameters": {"type":"object","properties":{
      "action": {"type":"string","enum":["nmap_scan","packet_sniff","traceroute"]},
      "target": {"type":"string"},
      "options": {"type":"string"}
    },"required":["action", "target"]}
  },
  {
    "name": "satellite_geolocation",
    "description": "Géolocalisation précise, reverse geocoding, et calculs de distance tactique mondiaux.",
    "parameters": {"type":"object","properties":{
      "action": {"type":"string","enum":["locate_ip","geocode_address","reverse_geocode"]},
      "target": {"type":"string"}
    },"required":["action", "target"]}
  },
  {
    "name": "crypto_and_stealth",
    "description": "Chiffrement de grade militaire, déchiffrement, génération de hash et opérations de stéganographie.",
    "parameters": {"type":"object","properties":{
      "action": {"type":"string","enum":["encrypt","decrypt","hash"]},
      "text_or_path": {"type":"string"},
      "key": {"type":"string"}
    },"required":["action", "text_or_path"]}
  },
  {
    "name": "run_code",
    "description": "Exécuter du code Python, JavaScript, Bash directement. À utiliser COMME FALLBACK si un outil n'existe pas.",
    "parameters": {"type":"object","properties":{
      "language": {"type":"string","enum":["python","javascript","bash","powershell"]},
      "code": {"type":"string"},
      "safe_mode": {"type":"boolean","default":True}
    },"required":["language","code"]}
  },
  {
    "name": "database_query",
    "description": "Exécuter une requête SQL sur une base de données MySQL, PostgreSQL ou SQLite.",
    "parameters": {"type":"object","properties":{
      "db_type": {"type":"string","enum":["sqlite","mysql","postgresql"]},
      "connection_string": {"type":"string"},
      "query": {"type":"string"}
    },"required":["db_type", "query"]}
  },
  {
    "name": "run_crewai_tool",
    "description": "Utilisater des outils CrewAI (YoutubeVideoSearchTool, WebsiteSearchTool, GithubSearchTool, DirectoryReadTool) pour extraire des connaissances.",
    "parameters": {"type":"object","properties":{
      "tool_name": {"type":"string","enum":["youtube_search", "website_search", "github_search", "directory_read"]},
      "query": {"type":"string"}
    },"required":["tool_name", "query"]}
  },
  {
    "name": "run_mcp_action",
    "description": "Interagir avec des serveurs Model Context Protocol (MCP) pour filesystem, bash, postgres, brave-search, google-maps.",
    "parameters": {"type":"object","properties":{
      "server_type": {"type":"string","enum":["filesystem", "google-maps", "brave-search", "sqlite", "fetch"]},
      "action": {"type":"string"},
      "params": {"type":"string","description":"JSON params"}
    },"required":["server_type", "action"]}
  },
  {
    "name": "social_media_action",
    "description": "Gérer les réseaux sociaux et communication (Twitter, e-mail IMAP, Spotify). Inspiré des plugins AutoGPT.",
    "parameters": {"type":"object","properties":{
      "platform": {"type":"string","enum":["twitter", "spotify", "email"]},
      "action": {"type":"string","enum":["post", "read", "play", "pause", "send", "search"]},
      "content": {"type":"string"}
    },"required":["platform", "action"]}
  },
  {
    "name": "open_interpreter",
    "description": "À utiliser uniquement lorsque l'utilisateur demande une action technique sur son système d'exploitation, ses fichiers locaux, ou des installations de paquets que tu ne peux pas faire toi-même. L'outil Open Interpreter est un délégué IA qui peut programmer et exécuter des scripts de manière autonome pour accomplir la tâche.",
    "parameters": {"type":"object","properties":{
      "task": {"type":"string","description":"La tâche technique ou script que Open Interpreter doit accomplir en toute autonomie sur la machine locale."}
    },"required":["task"]}
  },
  {
    "name": "osint_toolkit",
    "description": "Boîte à outils OSINT complète intégrant Holehe, Toutatis, DaProfiler, OnionSearch, xurlfind3r, user-scanner et le catalogue d'outils OSINT.",
    "parameters": {"type":"object","properties":{
      "target": {"type":"string", "description": "L'adresse IP, le domaine, le nom d'utilisateur, ou l'email cible."},
      "action": {"type":"string", "enum":["whois", "dns_lookup", "ip_info", "username_search", "email_search", "darkweb_search", "instagram_search", "comprehensive_profile", "advanced_search"]}
    },"required":["target", "action"]}
  },
  {
    "name": "self_inspector",
    "description": "Inspects JARVIS's own source code, counts files/lines, and lists loaded skills/plugins. Call this to report internal health, status, or capabilities.",
    "parameters": {"type":"object","properties":{}}
  }
]

class DummyPlayer:
    def __init__(self):
        self.muted = False
        self.current_file = None
    def write_log(self, text: str):
        print(f"[LOG] {text}")
    def set_state(self, state: str):
        pass

_frontend_events = []
_frontend_lock = threading.Lock()
_jarvis_instance = None

def _push_event(event_type, text):
    with _frontend_lock:
        _frontend_events.append({
            "type": event_type,
            "text": text,
            "ts": time.time()
        })
        if len(_frontend_events) > 50:
            _frontend_events.pop(0)

flask_app = Flask(__name__)
CORS(flask_app)

@flask_app.route('/api/health')
def api_health():
    return jsonify({
        "status": "ok",
        "model": "Mark XXXIX — Gemini Live",
        "listening": not _jarvis_instance.ui.muted if _jarvis_instance else False,
        "speaking": _jarvis_instance._is_speaking if _jarvis_instance else False
    })

@flask_app.route('/api/events')
def api_events():
    def generate():
        last_idx = 0
        while True:
            with _frontend_lock:
                new_events = _frontend_events[last_idx:]
                last_idx = len(_frontend_events)
            for ev in new_events:
                yield f"data: {json.dumps(ev)}\n\n"
            time.sleep(0.15)
    return Response(generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        })

@flask_app.route('/api/status')
def api_status():
    if not _jarvis_instance:
        return jsonify({"listening": False, "speaking": False, "muted": True})
    return jsonify({
        "listening": True,
        "speaking": _jarvis_instance._is_speaking,
        "muted": _jarvis_instance.ui.muted
    })

@flask_app.route('/api/mute', methods=['POST'])
def api_mute():
    if _jarvis_instance:
        _jarvis_instance.ui.muted = True
    return jsonify({"success": True, "muted": True})

@flask_app.route('/api/unmute', methods=['POST'])
def api_unmute():
    if _jarvis_instance:
        _jarvis_instance.ui.muted = False
    return jsonify({"success": True, "muted": False})

@flask_app.route('/api/toggle-mute', methods=['POST'])
def api_toggle_mute():
    if _jarvis_instance:
        _jarvis_instance.ui.muted = not _jarvis_instance.ui.muted
        return jsonify({"success": True, "muted": _jarvis_instance.ui.muted})
    return jsonify({"success": False})

@flask_app.route('/api/tool-chat', methods=['POST'])
def api_tool_chat():
    message = request.json.get('message', '')
    if _jarvis_instance and _jarvis_instance.session:
        # Note: In Live api we must send via `send_client_content` instead of `send`
        import asyncio
        asyncio.run_coroutine_threadsafe(
            _jarvis_instance.session.send_client_content(
                turns={"parts": [{"text": message}]},
                turn_complete=True
            ),
            _jarvis_instance._loop
        )
    return jsonify({"reply": "Message envoyé à JARVIS.", "action": None})

@flask_app.route('/api/providers')
def api_providers():
    return jsonify({
        "providers": [{
            "id": "gemini-live",
            "name": "Gemini Multimodal Live",
            "free": False,
            "available": True,
            "vision": True,
            "category": "Mark XXXIX"
        }],
        "ollama_models": [],
        "current": "gemini-live"
    })

def start_flask():
    flask_app.run(
        host='127.0.0.1', port=5001,
        debug=False, use_reloader=False
    )

class JarvisLive:
    def __init__(self, ui):
        self.ui             = ui
        self.session        = None
        self.audio_in_queue = None
        self.out_queue      = None
        self._loop          = None
        self._is_speaking   = False
        self._speaking_lock = threading.Lock()
        self.ui.on_text_command = self._on_text_command
        self._turn_done_event = None

    async def _update_memory_async(self, user_input: str, assistant_response: str):
        """
        Background task to extract and store long-term memory facts via OpenRouter.
        Drains web-hud memory tasks to Free API models.
        """
        if not user_input or not assistant_response:
            return
        try:
            from memory.memory_manager import should_extract_memory, extract_memory, update_memory
            loop = asyncio.get_event_loop()
            should = await loop.run_in_executor(None, should_extract_memory, user_input, assistant_response)
            if should:
                print(f"[Memory Async] Intelligent insights found inside turn. Extracting facts...")
                extracted = await loop.run_in_executor(None, extract_memory, user_input, assistant_response)
                if extracted and isinstance(extracted, dict) and extracted != {}:
                    print(f"[Memory Async] Extracted data: {extracted}")
                    await loop.run_in_executor(None, update_memory, extracted)
                    print(f"[Memory Async] Long-term memory successfully updated in background.")
                    self.ui.write_log(f"[Mémoire] 💾 Nouvelle connaissance enregistrée : {list(extracted.keys())}")
                else:
                    print(f"[Memory Async] Extraction yielded no structured updates.")
            else:
                print(f"[Memory Async] Interaction parsed. No stable long-term facts learned.")
        except Exception as e:
            print(f"[Memory Async] Exception in memory background task: {e}")


    def _on_text_command(self, text: str):
        if not self._loop or not self.session:
            return
        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(
                turns={"parts": [{"text": text}]},
                turn_complete=True
            ),
            self._loop
        )

    def set_speaking(self, value: bool):
        with self._speaking_lock:
            self._is_speaking = value
        if value:
            self.ui.set_state("SPEAKING")
        elif not getattr(self.ui, 'muted', False):
            self.ui.set_state("LISTENING")

    def speak(self, text: str):
        if not self._loop or not self.session:
            return
        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(
                turns={"parts": [{"text": text}]},
                turn_complete=True
            ),
            self._loop
        )

    def speak_error(self, tool_name: str, error: str):
        short = str(error)[:120]
        self.ui.write_log(f"ERR: {tool_name} — {short}")
        self.speak(f"Sir, {tool_name} encountered an error. {short}")

    def _build_config(self) -> types.LiveConnectConfig:
        from datetime import datetime

        memory     = load_memory()
        mem_str    = format_memory_for_prompt(memory)
        sys_prompt = _load_system_prompt()

        now      = datetime.now()
        time_str = now.strftime("%A, %B %d, %Y — %I:%M %p")
        time_ctx = (
            f"[CURRENT DATE & TIME]\n"
            f"Right now it is: {time_str}\n"
            f"Use this to calculate exact times for reminders.\n\n"
        )

        parts = [time_ctx]
        if mem_str:
            parts.append(mem_str)
        parts.append(sys_prompt)

        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription={"model": "models/gemini-2.5-flash"},
            input_audio_transcription={"model": "models/gemini-2.5-flash"},
            system_instruction="\n".join(parts),
            tools=[{"function_declarations": TOOL_DECLARATIONS}],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Charon"
                    )
                )
            ),
        )

    async def _tool_osint_lookup(self, args):
        target_type = args.get("type")
        target = args.get("target")

        if target_type == "ip":
            import requests
            try:
                r = requests.get(f"http://ip-api.com/json/{target}", timeout=5)
                return str(r.json())
            except Exception as e:
                return f"Error: {e}"

        elif target_type == "username":
            platforms = {
                "GitHub": f"https://github.com/{target}",
                "Twitter": f"https://twitter.com/{target}",
                "Instagram": f"https://instagram.com/{target}",
                "Reddit": f"https://reddit.com/user/{target}",
                "TikTok": f"https://tiktok.com/@{target}",
                "YouTube": f"https://youtube.com/@{target}",
                "LinkedIn": f"https://linkedin.com/in/{target}",
                "Twitch": f"https://twitch.tv/{target}",
            }
            found = []
            import requests
            for platform, url in platforms.items():
                try:
                    r = requests.head(url, timeout=3, allow_redirects=True)
                    if r.status_code == 200:
                        found.append({"platform": platform, "url": url})
                except: pass
            return str({"username": target, "found_on": found})

        elif target_type == "domain":
            try:
                import whois, socket
                w = whois.whois(target)
                ip = socket.gethostbyname(target)
                return str({"domain": target, "ip": ip, "registrar": str(w.registrar), "created": str(w.creation_date)})
            except Exception as e:
                return f"Error: {e}"
                
        return "Unsupported osint type"

    async def _tool_detect_hardware(self, args):
        import psutil, cv2
        try:
            import serial.tools.list_ports
        except ImportError:
            serial = None
        result = {}

        cameras = []
        for i in range(5):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    cameras.append(f"Camera {i}")
                    cap.release()
            except Exception: pass
        result["cameras"] = cameras

        if serial:
            ports = [str(p) for p in serial.tools.list_ports.comports()]
            result["serial_ports"] = ports
        else:
            result["serial_ports"] = []

        try:
            result["disks"] = [d.device for d in psutil.disk_partitions() if "removable" in d.opts.lower()]
        except Exception:
            result["disks"] = []

        return str({"detected": result, "summary": f"Caméras: {cameras}, Ports série: {result['serial_ports']}"})

    async def _execute_tool(self, fc) -> types.FunctionResponse:
        name = fc.name
        args = dict(fc.args or {})

        print(f"[JARVIS] 🔧 {name}  {args}")
        self.ui.set_state("THINKING")

        if name == "save_memory":
            category = args.get("category", "notes")
            key      = args.get("key", "")
            value    = args.get("value", "")
            if key and value:
                update_memory({category: {key: {"value": value}}})
                print(f"[Memory] 💾 save_memory: {category}/{key} = {value}")
            if not getattr(self.ui, 'muted', False):
                self.ui.set_state("LISTENING")
            return types.FunctionResponse(
                id=fc.id, name=name,
                response={"result": "ok", "silent": True}
            )

        loop   = asyncio.get_event_loop()
        result = "Done."

        try:
            if name == "osint_lookup":
                r = await self._tool_osint_lookup(args)
                result = r or "Done."

            elif name == "detect_hardware":
                r = await self._tool_detect_hardware(args)
                result = r or "Done."

            elif name == "open_app":
                r = await loop.run_in_executor(None, lambda: open_app(parameters=args, response=None, player=self.ui))
                result = r or f"Opened {args.get('app_name')}."

            elif name == "weather_report":
                r = await loop.run_in_executor(None, lambda: weather_action(parameters=args, player=self.ui))
                result = r or "Weather delivered."

            elif name == "browser_control":
                r = await loop.run_in_executor(None, lambda: browser_control(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "file_controller":
                r = await loop.run_in_executor(None, lambda: file_controller(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "send_message":
                r = await loop.run_in_executor(None, lambda: send_message(parameters=args, response=None, player=self.ui, session_memory=None))
                result = r or f"Message sent to {args.get('receiver')}."

            elif name == "reminder":
                r = await loop.run_in_executor(None, lambda: reminder(parameters=args, response=None, player=self.ui))
                result = r or "Reminder set."

            elif name == "youtube_video":
                r = await loop.run_in_executor(None, lambda: youtube_video(parameters=args, response=None, player=self.ui))
                result = r or "Done."

            elif name == "screen_process":
                threading.Thread(
                    target=screen_process,
                    kwargs={"parameters": args, "response": None,
                            "player": self.ui, "session_memory": None},
                    daemon=True
                ).start()
                result = "Vision module activated. Stay completely silent — vision module will speak directly."

            elif name == "computer_settings":
                r = await loop.run_in_executor(None, lambda: computer_settings(parameters=args, response=None, player=self.ui))
                result = r or "Done."

            elif name == "desktop_control":
                r = await loop.run_in_executor(None, lambda: desktop_control(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "code_helper":
                r = await loop.run_in_executor(None, lambda: code_helper(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."

            elif name == "dev_agent":
                r = await loop.run_in_executor(None, lambda: dev_agent(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."

            elif name == "agent_task":
                from agent.task_queue import get_queue, TaskPriority
                priority_map = {"low": TaskPriority.LOW, "normal": TaskPriority.NORMAL, "high": TaskPriority.HIGH}
                priority = priority_map.get(args.get("priority", "normal").lower(), TaskPriority.NORMAL)
                task_id  = get_queue().submit(goal=args.get("goal", ""), priority=priority, speak=self.speak)
                result   = f"Task started (ID: {task_id})."

            elif name == "web_search":
                r = await loop.run_in_executor(None, lambda: web_search_action(parameters=args, player=self.ui))
                result = r or "Done."
                
            elif name == "file_processor":
                curr_file = ""
                try: curr_file = self.ui.current_file
                except: pass
                if not args.get("file_path") and curr_file:
                    args["file_path"] = curr_file
                r = await loop.run_in_executor(
                    None,
                    lambda: file_processor(parameters=args, player=self.ui, speak=self.speak)
                )
                result = r or "Done."

            elif name == "computer_control":
                r = await loop.run_in_executor(None, lambda: computer_control(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "game_updater":
                r = await loop.run_in_executor(None, lambda: game_updater(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."

            elif name == "flight_finder":
                r = await loop.run_in_executor(None, lambda: flight_finder(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "shutdown_jarvis":
                self.ui.write_log("SYS: Shutdown requested.")
                self.speak("Goodbye, sir.")
                def _shutdown():
                    import time, os
                    time.sleep(1)
                    os._exit(0)
                threading.Thread(target=_shutdown, daemon=True).start()

            elif name == "execute_command":
                import subprocess
                cmd = args.get("command", "")
                try:
                    res = subprocess.getoutput(cmd)
                    result = res[:2000] + ("..." if len(res)>2000 else "")
                except Exception as e:
                    result = str(e)
            
            elif name == "get_system_info":
                import psutil
                result = f"CPU: {psutil.cpu_percent()}%, RAM: {psutil.virtual_memory().percent}%"

            elif name == "manage_clipboard":
                import pyperclip
                if args.get("action") == "read": result = pyperclip.paste()
                elif args.get("action") == "write": 
                    pyperclip.copy(args.get("content", ""))
                    result = "Copied."

            elif name == "wikipedia_search":
                try:
                    import wikipediaapi
                    wiki = wikipediaapi.Wikipedia('Jarvis/1.0', args.get('lang', 'fr'))
                    page = wiki.page(args.get('query', ''))
                    result = page.summary[0:1500] if page.exists() else "Not found."
                except Exception as e: result = str(e)

            elif name == "manage_files":
                import shutil, os
                action = args.get("action")
                path = args.get("path")
                try:
                    if action == "read":
                        with open(path, "r", encoding="utf-8") as f: result = f.read()
                    elif action == "write": 
                        with open(path, "w", encoding="utf-8") as f: f.write(args.get("content", ""))
                        result = f"File {path} written."
                    elif action == "delete":
                        os.remove(path)
                        result = "File deleted."
                    elif action == "move":
                        shutil.move(path, args.get("destination"))
                        result = "Moved."
                    elif action == "copy":
                        shutil.copy(path, args.get("destination"))
                        result = "Copied."
                    elif action == "list":
                        result = str(os.listdir(path if path else "."))
                    elif action == "exists":
                        result = str(os.path.exists(path))
                    else: result = f"Unknown manage_files action {action}"
                except Exception as e: result = str(e)

            elif name == "control_mouse_keyboard":
                try:
                    import pyautogui
                    action = args.get("action")
                    if action == "click": pyautogui.click(args.get("x"), args.get("y"))
                    elif action == "double_click": pyautogui.doubleClick(args.get("x"), args.get("y"))
                    elif action == "right_click": pyautogui.rightClick(args.get("x"), args.get("y"))
                    elif action == "move": pyautogui.moveTo(args.get("x"), args.get("y"))
                    elif action == "type": pyautogui.write(args.get("text", ""))
                    elif action == "hotkey":
                        keys = args.get("keys", [])
                        if keys: pyautogui.hotkey(*keys)
                    elif action == "scroll": pyautogui.scroll(args.get("y", -100))
                    result = "Input executed successfully."
                except ImportError:
                    result = "pyautogui is not installed. Use pip install pyautogui."

            elif name == "take_screenshot":
                try:
                    import pyautogui, tempfile, os
                    path = os.path.join(tempfile.gettempdir(), "jarvis_screenshot.png")
                    pyautogui.screenshot(path)
                    result = f"Capture effectuée : {path}. Veuillez utiliser ce chemin pour l'analyser si nécessaire."
                except Exception as e:
                    result = f"Capture échouée: {e}"

            elif name == "browser_navigate":
                action = args.get("action")
                if action == "open":
                    import webbrowser
                    webbrowser.open(args.get("url", ""))
                    result = "URL ouverte."
                else:
                    result = "Pour scraper ou faire des actions complexes, merci d'utiliser l'outil run_code avec Playwright ou selenium, car l'intégration Browser-Use complète est en cours d'installation."

            elif name == "calculate":
                import math
                safe_dict = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
                try:
                    res = eval(args.get("expression", ""), {"__builtins__": None}, safe_dict)
                    result = str(res)
                except Exception as e:
                    result = f"Erreur de calcul: {e}"

            elif name == "run_code":
                import subprocess, tempfile, os
                code = args.get("code", "")
                lang = args.get("language", "python")
                if lang == "python":
                    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
                        f.write(code)
                        tmp = f.name
                    try:
                        res = subprocess.getoutput(f"python {tmp}")
                        result = res[:3000] + ("\n[Output truncated...]" if len(res)>3000 else "")
                    except Exception as e:
                        result = str(e)
                    finally:
                        os.remove(tmp)
                elif lang in ["bash", "powershell"]:
                    try:
                        res = subprocess.getoutput(code)
                        result = res[:3000] + ("\n[Output truncated...]" if len(res)>3000 else "")
                    except Exception as e:
                        result = str(e)
                else:
                    result = f"Unsupported language {lang} for direct run."

            elif name == "global_threat_intel":
                try:
                    import shodan
                    # On tente de voir si une clé est dans l'environnement, sinon on prévient l'IA de le mentionner
                    api_key = os.environ.get("SHODAN_API_KEY", "")
                    if not api_key:
                        result = "L'accès au réseau global Shodan nécessite une SHODAN_API_KEY. Demandez à Monsieur de la configurer."
                    else:
                        api = shodan.Shodan(api_key)
                        res = api.search(args.get("query", ""))
                        result = f"Shodan Report: {res['total']} résultats. Top 2 IPs: {[match['ip_str'] for match in res['matches'][:2]]}"
                except ImportError:
                    result = "Erreur: shodan n'est pas installé."
                except Exception as e:
                    result = f"Global Threat Intel Error: {e}"

            elif name == "biometric_and_vision":
                action = args.get("action")
                path = args.get("image_path")
                if action == "read_text":
                    try:
                        import pytesseract
                        from PIL import Image
                        text = pytesseract.image_to_string(Image.open(path))
                        result = f"Texte extrait (OCR): {text}"
                    except Exception as e:
                        result = f"Erreur OCR (Assurez-vous que Tesseract-OCR est installé sur le système) : {e}"
                elif action in ["detect_faces", "track_pose"]:
                    try:
                        import cv2
                        import mediapipe as mp
                        img = cv2.imread(path)
                        mp_face_detection = mp.solutions.face_detection
                        with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
                            results = face_detection.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                            num_faces = len(results.detections) if results.detections else 0
                        result = f"Analyse Biométrique : {num_faces} visage(s) détecté(s) dans le flux."
                    except Exception as e:
                        result = f"Erreur biométrique: {e}"

            elif name == "advanced_network_recon":
                import subprocess
                action = args.get("action")
                target = args.get("target", "127.0.0.1")
                opts = args.get("options", "")
                try:
                    if action == "nmap_scan":
                        res = subprocess.getoutput(f"nmap {opts} {target}")
                        result = res[:1500] + "\n[Tronqué]" if len(res)>1500 else res
                    elif action == "traceroute":
                        cmd = "tracert" if os.name == "nt" else "traceroute"
                        res = subprocess.getoutput(f"{cmd} {target}")
                        result = res[:1500] if len(res)>1500 else res
                    else:
                        result = "Action réseau non supportée directement sans droits Admin élevés (Scapy nécessite root)."
                except Exception as e:
                    result = str(e)

            elif name == "satellite_geolocation":
                try:
                    from geopy.geocoders import Nominatim
                    action = args.get("action")
                    target = args.get("target", "")
                    geolocator = Nominatim(user_agent="JARVIS_MARK_XXXIX")
                    if action == "geocode_address":
                        loc = geolocator.geocode(target)
                        result = f"Cible verrouillée. Coordonnées: {loc.latitude}, {loc.longitude}" if loc else "Cible introuvable."
                    else:
                        loc = geolocator.reverse(target)
                        result = f"Emplacement: {loc.address}" if loc else "Emplacement introuvable."
                except Exception as e:
                    result = f"Système de géolocalisation hors ligne: {e}"

            elif name == "crypto_and_stealth":
                try:
                    import hashlib
                    action = args.get("action")
                    target = args.get("text_or_path")
                    if action == "hash":
                        h = hashlib.sha256(target.encode()).hexdigest()
                        result = f"Empreinte SHA-256 générée: {h}"
                    else:
                        result = f"Action {action} nécessite la configuration de Fernet."
                except Exception as e:
                    result = str(e)

            elif name == "manage_processes":
                import psutil
                action = args.get("action")
                pname = args.get("name", "").lower()
                try:
                    if action == "list":
                        procs = [p.info['name'] for p in psutil.process_iter(['name']) if pname in p.info['name'].lower()]
                        result = f"Found {len(procs)} processes matching '{pname}': {', '.join(procs[:20])}" if procs else "No match."
                    elif action == "kill":
                        killed = 0
                        for p in psutil.process_iter(['name']):
                            if pname in p.info['name'].lower():
                                p.kill()
                                killed += 1
                        result = f"Killed {killed} process(es)."
                    elif action == "start":
                        import subprocess
                        subprocess.Popen(pname, shell=True)
                        result = f"Started '{pname}'"
                except Exception as e:
                    result = f"Process Error: {e}"

            elif name == "fetch_webpage":
                try:
                    import requests
                    from bs4 import BeautifulSoup
                    url = args.get("url")
                    extract = args.get("extract", "text")
                    resp = requests.get(url, timeout=10)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.content, "html.parser")
                    if extract == "text":
                        result = soup.get_text(separator='\n', strip=True)[:3000]
                    elif extract == "links":
                        links = [a.get('href') for a in soup.find_all('a', href=True) if a.get('href')]
                        result = f"Links: {', '.join(links[:50])}"
                    elif extract == "images":
                        imgs = [img.get('src') for img in soup.find_all('img', src=True) if img.get('src')]
                        result = f"Images: {', '.join(imgs[:50])}"
                    else:
                        result = soup.get_text(separator='\n', strip=True)[:3000]
                except Exception as e:
                    result = f"Error fetching webpage: {e}"

            elif name == "git_operations":
                import subprocess, os
                action = args.get("action")
                repo_path = args.get("repo_path", ".")
                msg = args.get("message", "Auto-commit")
                url = args.get("url", "")
                try:
                    def git_cmd(cmd_list):
                        return subprocess.check_output(["git"] + cmd_list, cwd=repo_path, stderr=subprocess.STDOUT).decode('utf-8')
                        
                    if action == "clone":
                        out = subprocess.check_output(["git", "clone", url, repo_path], stderr=subprocess.STDOUT).decode('utf-8')
                        result = out
                    elif action == "status":
                        result = git_cmd(["status"])
                    elif action == "commit":
                        git_cmd(["add", "."])
                        result = git_cmd(["commit", "-m", msg])
                    elif action == "push":
                        result = git_cmd(["push"])
                    elif action == "pull":
                        result = git_cmd(["pull"])
                    elif action == "log":
                        result = git_cmd(["log", "-n", "5", "--oneline"])
                    else:
                        result = git_cmd([action])
                except Exception as e:
                    result = f"Git error: {(e.output.decode('utf-8') if hasattr(e, 'output') else str(e))}"

            elif name == "database_query":
                db_type = args.get("db_type")
                conn_str = args.get("connection_string", "database.sqlite")
                query = args.get("query")
                try:
                    if db_type == "sqlite":
                        import sqlite3
                        conn = sqlite3.connect(conn_str)
                        cursor = conn.cursor()
                        cursor.execute(query)
                        if query.strip().upper().startswith("SELECT"):
                            rows = cursor.fetchall()
                            result = f"Results: {rows[:50]} (truncated)" if len(rows)>50 else str(rows)
                        else:
                            conn.commit()
                            result = f"Affected {cursor.rowcount} raw(s)."
                        conn.close()
                    else:
                        result = f"DB Type {db_type} requires 'run_code' fallback or manual installation."
                except Exception as e:
                    result = f"DB Error: {e}"

            elif name == "android_control":
                import subprocess
                action = args.get("action")
                params = args.get("params", {})
                try:
                    if action == "screenshot":
                        subprocess.run(["adb", "shell", "screencap", "-p", "/sdcard/screen.png"])
                        subprocess.run(["adb", "pull", "/sdcard/screen.png", "android_screen.png"])
                        result = "Screenshot saved to android_screen.png"
                    elif action == "tap":
                        subprocess.run(["adb", "shell", "input", "tap", str(params.get("x", 0)), str(params.get("y", 0))])
                        result = "Tapped."
                    elif action == "type":
                        text = params.get("text", "").replace(" ", "%s")
                        subprocess.run(["adb", "shell", "input", "text", text])
                        result = "Text sent."
                    elif action == "open_app":
                        pkg = params.get("package", "")
                        subprocess.run(["adb", "shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"])
                        result = "Launched."
                    else:
                        result = f"Unknown android action: {action}"
                except Exception as e:
                    result = f"ADB Error (Ensure device is connected via USB and ADB is installed): {e}"

            elif name == "control_window":
                try:
                    import pygetwindow as gw
                    action = args.get("action")
                    title = args.get("window_title", "")
                    if action == "list":
                        result = "Fenêtres:" + ", ".join([w.title for w in gw.getAllWindows() if w.title])
                    else:
                        windows = gw.getWindowsWithTitle(title)
                        if not windows:
                            result = f"Window '{title}' not found."
                        else:
                            win = windows[0]
                            if action == "minimize": win.minimize(); result = "Minimized."
                            elif action == "maximize": win.maximize(); result = "Maximized."
                            elif action == "close": win.close(); result = "Closed."
                            elif action == "focus": win.activate(); result = "Focused."
                except Exception as e:
                    result = f"Window control error: {e}"

            elif name == "send_notification":
                try:
                    from plyer import notification
                    notification.notify(
                        title=args.get("title", "JARVIS Alert"),
                        message=args.get("message", ""),
                        timeout=10,
                    )
                    result = "Notification displayed."
                except Exception as e:
                    result = f"Notification error: {e}"

            elif name == "data_analysis":
                try:
                    import pandas as pd
                    path = args.get("file_path", "")
                    action = args.get("action", "")
                    df = pd.read_csv(path) if path.endswith('.csv') else pd.read_excel(path)
                    if action == "stats":
                        result = str(df.describe().to_dict())
                    elif action == "clean":
                        df = df.dropna()
                        res_path = "cleaned_" + os.path.basename(path)
                        df.to_csv(res_path, index=False)
                        result = f"Cleaned data saved to {res_path}."
                    else:
                        result = f"Data columns: {list(df.columns)}, Shape: {df.shape}"
                except Exception as e:
                    result = f"Data Analysis Error: {e}"

            elif name == "run_crewai_tool":
                tool_name = args.get("tool_name", "")
                query = args.get("query", "")
                try:
                    if tool_name == "youtube_search":
                        result = f"[CrewAI YouTube Search] Simulated result for {query}. Import 'youtube_search' module in run_code for real search."
                    elif tool_name == "website_search":
                        import requests
                        from bs4 import BeautifulSoup
                        if query.startswith("http"):
                            r = requests.get(query, timeout=10)
                            soup = BeautifulSoup(r.text, 'html.parser')
                            result = f"Website Search: {soup.text[:2000]}"
                        else:
                            result = "[CrewAI] Invalid URL for WebsiteSearchTool."
                    else:
                        result = f"CrewAI tool '{tool_name}' acknowledged. Install crewai-tools via run_code if full integration needed."
                except Exception as e:
                    result = f"CrewAI Tool error: {e}"

            elif name == "run_mcp_action":
                server_type = args.get("server_type")
                action = args.get("action")
                params = args.get("params", "")
                try:
                    if server_type == "filesystem":
                        result = f"MCP Filesystem: Use 'manage_files' tool instead for local ops."
                    elif server_type == "google-maps":
                        result = f"MCP Google Maps: Execute run_code with 'geopy' or 'requests' to Maps API for {action}. Params: {params}"
                    elif server_type == "brave-search":
                        result = f"MCP Brave Search: Please use 'web_search' tool which defaults to DuckDuckGo/Google for queries."
                    else:
                        result = f"MCP Server '{server_type}' action '{action}' queued. Full MCP JS/Python bridge needed."
                except Exception as e:
                    result = f"MCP Error: {e}"

            elif name == "social_media_action":
                platform = args.get("platform")
                action = args.get("action")
                content = args.get("content", "")
                result = f"AutoGPT Plugin [{platform}]: Action '{action}' recorded with content: {content}. Native API keys required in .env mapping to execute real payload."

            elif name == "open_interpreter":
                task = args.get("task", "")
                try:
                    from interpreter import interpreter
                    interpreter.auto_run = True
                    interpreter.llm.model = "gemini/gemini-1.5-pro-latest" # Ou le modele de base supporte par LiteLLM
                    
                    api_key = os.environ.get("GEMINI_API_KEY", "")
                    if api_key:
                        interpreter.llm.api_key = api_key
                        
                    messages = interpreter.chat(task, display=False)
                    if messages and isinstance(messages, list):
                        last_message = messages[-1]
                        content = last_message.get('content', '') if isinstance(last_message, dict) else str(last_message)
                        result = f"Open Interpreter task concluded: {content}"
                    else:
                        result = "Open Interpreter task concluded successfully."
                except Exception as e:
                    result = f"Open Interpreter Error: {e}. (Verify 'open-interpreter' package is installed and LiteLLM can handle Gemini keys)."

            elif name == "osint_toolkit":
                target = args.get("target", "")
                action = args.get("action", "")
                try:
                    if action == "whois":
                        import whois
                        w = whois.whois(target)
                        result = str(w)
                    elif action == "ip_info":
                        import requests
                        r = requests.get(f"https://ipinfo.io/{target}/json")
                        result = r.text
                    elif action == "dns_lookup":
                        import socket
                        result = f"IP(s) found: {socket.gethostbyname_ex(target)}"
                    elif action == "username_search":
                        result = f"OSINT: Recheche username pour '{target}'. Outils recommandés: Emora-Project, Sherlock, DaProfiler. Vérifiez manuellement: https://github.com/{target} ou employez subprocess pour 'sherlock {target}'."
                    elif action == "email_search":
                        import subprocess
                        # Using holehe for email OSINT
                        try:
                            # It is typically installed as a CLI tool if 'holehe' is in Pip
                            out = subprocess.check_output(["holehe", target, "--only-used", "--no-color"], stderr=subprocess.STDOUT, text=True)
                            result = f"Holehe scan results for {target}:\n{out[:2000]}"
                        except FileNotFoundError:
                            result = "Holehe n'est pas installé ou n'est pas dans le PATH. Veuillez exécuter 'pip install holehe'."
                        except subprocess.CalledProcessError as e:
                            result = f"Holehe a retourné une erreur: {e.output}"
                    elif action == "advanced_search":
                        result = f"OSINT tools (xurlfind3r, pryingdeep, ominis-osint, seekr, ohshint, osint_stuff_tool_collection, user-scanner) requested for {target}. This acts as a proxy for these advanced modules. Integrate them via CLI execution module if locally available."
                    elif action == "darkweb_search":
                        result = f"OSINT Darkweb: Recherche de '{target}' via OnionSearch, pryingdeep ou d'autres outils darkweb. (Nécessite une configuration proxy/Tor locale appropriée)."
                    elif action == "instagram_search":
                        result = f"OSINT Instagram pour '{target}'. Outils recommandés : 'toutatis' ou 'yesitsme'. Utilisez subprocess pour exécuter 'toutatis -u {target}' si installé."
                    elif action == "comprehensive_profile":
                        result = f"OSINT Profil Global : Recherche exhaustive pour '{target}'. Outils consolidés recommandés : DaProfiler, Mr.Holmes, Tookie-OSINT ou user-scanner."
                    else:
                        result = f"Action OSINT {action} non reconnue."
                except Exception as e:
                    result = f"OSINT Erreur: {e} (Vérifiez que les dépendances python-whois/holehe sont installées)"

            elif name == "self_inspector":
                try:
                    from actions.jarvis_self_inspector import inspect_jarvis_skills
                    result = inspect_jarvis_skills()
                except Exception as e:
                    result = f"Self-Inspector Error: {e}"

            else:
                # Catch-all
                result = f"L'outil {name} n'a pas d'implémentation directe. Contournez cette limitation en utilisant 'run_code' pour écrire un script Python accomplissant la tâche."

        except Exception as e:
            result = f"Tool '{name}' failed: {e}"
            traceback.print_exc()
            self.speak_error(name, e)

        if not getattr(self.ui, 'muted', False):
            self.ui.set_state("LISTENING")

        print(f"[JARVIS] 📤 {name} → {str(result)[:80]}")
        return types.FunctionResponse(
            id=fc.id, name=name,
            response={"result": result}
        )

    async def _send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            await self.session.send_realtime_input(media=msg)

    async def _listen_audio(self):
        print("[JARVIS] 🎤 Mic started")
        loop = asyncio.get_event_loop()

        def callback(indata, frames, time_info, status):
            with self._speaking_lock:
                jarvis_speaking = self._is_speaking
            if not jarvis_speaking and not getattr(self.ui, 'muted', False):
                data = indata.tobytes()
                loop.call_soon_threadsafe(
                    self.out_queue.put_nowait,
                    {"data": data, "mime_type": "audio/pcm"}
                )

        try:
            with sd.InputStream(
                samplerate=SEND_SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
                blocksize=CHUNK_SIZE,
                callback=callback,
            ):
                print("[JARVIS] 🎤 Mic stream open")
                while True:
                    await asyncio.sleep(0.1)
        except Exception as e:
            print(f"[JARVIS] ❌ Mic: {e}")
            raise

    async def _receive_audio(self):
        print("[JARVIS] 👂 Recv started")
        out_buf, in_buf = [], []

        try:
            while True:
                async for response in self.session.receive():

                    if response.data:
                        if self._turn_done_event and self._turn_done_event.is_set():
                            self._turn_done_event.clear()
                        self.audio_in_queue.put_nowait(response.data)

                    if response.server_content:
                        sc = response.server_content

                        if hasattr(sc, "output_transcription") and sc.output_transcription and sc.output_transcription.text:
                            txt = _clean_transcript(sc.output_transcription.text)
                            if txt:
                                out_buf.append(txt)

                        if hasattr(sc, "input_transcription") and sc.input_transcription and sc.input_transcription.text:
                            txt = _clean_transcript(sc.input_transcription.text)
                            if txt:
                                in_buf.append(txt)

                        if sc.turn_complete:
                            if self._turn_done_event:
                                self._turn_done_event.set()

                            full_in = " ".join(in_buf).strip()
                            if full_in:
                                self.ui.write_log(f"You: {full_in}")
                                _push_event("user", full_in)
                            in_buf = []

                            full_out = " ".join(out_buf).strip()
                            if full_out:
                                self.ui.write_log(f"Jarvis: {full_out}")
                                _push_event("jarvis", full_out)
                                # Trigger background thread-safe async memory processing using OpenRouter
                                if full_in and full_out:
                                    asyncio.create_task(self._update_memory_async(full_in, full_out))
                            out_buf = []

                    if response.tool_call:
                        fn_responses = []
                        for fc in response.tool_call.function_calls:
                            print(f"[JARVIS] 📞 {fc.name}")
                            fr = await self._execute_tool(fc)
                            fn_responses.append(fr)
                        await self.session.send_tool_response(
                            function_responses=fn_responses
                        )
        except Exception as e:
            print(f"[JARVIS] ❌ Recv: {e}")
            traceback.print_exc()
            raise

    async def _play_audio(self):
        print("[JARVIS] 🔊 Play started")

        stream = sd.RawOutputStream(
            samplerate=RECEIVE_SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=CHUNK_SIZE,
        )
        stream.start()

        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(
                        self.audio_in_queue.get(),
                        timeout=0.1
                    )
                except asyncio.TimeoutError:
                    if (
                        self._turn_done_event
                        and self._turn_done_event.is_set()
                        and self.audio_in_queue.empty()
                    ):
                        self.set_speaking(False)
                        self._turn_done_event.clear()
                    continue
                self.set_speaking(True)
                await asyncio.to_thread(stream.write, chunk)
        except Exception as e:
            print(f"[JARVIS] ❌ Play: {e}")
            raise
        finally:
            self.set_speaking(False)
            stream.stop()
            stream.close()

    async def run(self):
        client = genai.Client(
            api_key=_get_api_key(),
            http_options={"api_version": "v1beta"}
        )

        while True:
            try:
                print("[JARVIS] 🔌 Connecting...")
                self.ui.set_state("THINKING")
                config = self._build_config()

                async with (
                    client.aio.live.connect(model=LIVE_MODEL, config=config) as session,
                    asyncio.TaskGroup() as tg,
                ):
                    self.session        = session
                    self._loop          = asyncio.get_event_loop()
                    self.audio_in_queue = asyncio.Queue()
                    self.out_queue      = asyncio.Queue(maxsize=10)
                    self._turn_done_event = asyncio.Event()

                    print("[JARVIS] ✅ Connected.")
                    self.ui.set_state("LISTENING")
                    self.ui.write_log("SYS: JARVIS online.")

                    tg.create_task(self._send_realtime())
                    tg.create_task(self._listen_audio())
                    tg.create_task(self._receive_audio())
                    tg.create_task(self._play_audio())

            except Exception as e:
                print(f"[JARVIS] ⚠️ {e}")
                traceback.print_exc()
            self.set_speaking(False)
            self.ui.set_state("THINKING")
            print("[JARVIS] 🔄 Reconnecting in 3s...")
            await asyncio.sleep(3)


class HardwareWatcher:
    def __init__(self, jarvis_instance):
        self.jarvis = jarvis_instance
        self.known_devices = set()
        
    def watch(self):
        import time, cv2
        try:
            import serial.tools.list_ports
        except ImportError:
            serial = None

        while True:
            current = set()
            
            if serial:
                try:
                    for p in serial.tools.list_ports.comports():
                        current.add(f"serial:{p.device}:{p.description}")
                except Exception: pass
            
            for i in range(4):
                try:
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        current.add(f"camera:{i}")
                        cap.release()
                except Exception: pass
            
            new = current - self.known_devices
            removed = self.known_devices - current
            
            if new:
                for d in new:
                    print(f"[HARDWARE] Nouveau: {d}")
                    _push_event("system", f"Nouvel appareil détecté : {d}")
            
            self.known_devices = current
            time.sleep(3)


def main():
    global _jarvis_instance
    print("====== MARK XXXIX : FLASK BACKEND ======")
    threading.Thread(target=start_flask, daemon=True).start()
    
    hw_watcher = HardwareWatcher(None)
    threading.Thread(target=hw_watcher.watch, daemon=True).start()

    ui = DummyPlayer()
    jarvis = JarvisLive(ui)
    _jarvis_instance = jarvis

    def runner():
        try:
            asyncio.run(jarvis.run())
        except KeyboardInterrupt:
            print("\n🔴 Shutting down...")

    runner()

if __name__ == "__main__":
    main()
