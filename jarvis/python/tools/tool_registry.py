"""
Registre de tous les outils disponibles pour JARVIS.
L'IA choisit automatiquement le bon outil selon la question.

Sources utilisées :
- duckduckgo-search : https://github.com/deedy5/duckduckgo_search
- wikipedia-api    : https://github.com/martin-majlis/Wikipedia-API
- speedtest-cli    : https://github.com/sivel/speedtest-cli
- psutil           : https://github.com/giampaolo/psutil
- pyautogui        : https://github.com/asweigart/pyautogui
"""

import os
import json
import subprocess
import platform
import datetime
import webbrowser
from typing import Any, Dict

# ===== DÉFINITION DES OUTILS =====
# Format compatible avec le tool calling OpenAI/Anthropic/Gemini

TOOLS_SCHEMA = [
    {
        "name": "web_search",
        "description": "Chercher des informations récentes sur internet. Utiliser quand la question porte sur l'actualité, des données récentes, ou des infos que tu n'as pas en mémoire.",
        "parameters": {
            "query": "La requête de recherche en français ou anglais",
            "type": "str (actualité|web|image)"  # actualité, web, ou image
        }
    },
    {
        "name": "get_wikipedia",
        "description": "Obtenir des infos détaillées sur un sujet, une personne, un lieu depuis Wikipedia.",
        "parameters": {
            "topic": "Le sujet à rechercher sur Wikipedia"
        }
    },
    {
        "name": "get_system_info",
        "description": "Obtenir les infos système : RAM, CPU, stockage, batterie, processus en cours.",
        "parameters": {}
    },
    {
        "name": "check_internet_speed",
        "description": "Tester la vitesse de connexion internet (download, upload, ping).",
        "parameters": {}
    },
    {
        "name": "take_screenshot",
        "description": "Prendre une capture d'écran de l'ordinateur.",
        "parameters": {
            "region": "optionnel: 'full' pour tout l'écran (défaut)"
        }
    },
    {
        "name": "control_mouse",
        "description": "Déplacer la souris et cliquer sur l'écran.",
        "parameters": {
            "action": "move|click|double_click|right_click|scroll",
            "x": "coordonnée X (optionnel)",
            "y": "coordonnée Y (optionnel)"
        }
    },
    {
        "name": "type_text",
        "description": "Taper du texte comme si c'était clavier.",
        "parameters": {
            "text": "Le texte à taper",
            "press_enter": "bool (défaut False)"
        }
    },
    {
        "name": "open_application",
        "description": "Ouvrir une application installée sur le PC.",
        "parameters": {
            "app_name": "Nom de l'application (ex: notepad, calculator, vscode)"
        }
    },
    {
        "name": "get_weather",
        "description": "Obtenir la météo actuelle d'une ville.",
        "parameters": {
            "city": "Nom de la ville"
        }
    },
    {
        "name": "calculate",
        "description": "Effectuer un calcul mathématique complexe.",
        "parameters": {
            "expression": "L'expression mathématique à calculer"
        }
    },
    {
        "name": "read_clipboard",
        "description": "Lire le contenu du presse-papier.",
        "parameters": {}
    },
    {
        "name": "write_file",
        "description": "Créer ou écrire dans un fichier texte.",
        "parameters": {
            "filename": "Nom du fichier",
            "content": "Contenu à écrire"
        }
    },
    {
        "name": "get_time_date",
        "description": "Obtenir la date et l'heure actuelles.",
        "parameters": {}
    },
    {
        "name": "youtube_search",
        "description": "Chercher et ouvrir une vidéo YouTube.",
        "parameters": {
            "query": "Ce qu'on cherche sur YouTube"
        }
    },
    {
        "name": "set_reminder",
        "description": "Créer un rappel dans X minutes.",
        "parameters": {
            "message": "Le message du rappel",
            "minutes": "Dans combien de minutes"
        }
    }
]


# ===== IMPLÉMENTATION DES OUTILS =====

class ToolExecutor:

    def execute(self, tool_name: str, params: dict) -> Dict[str, Any]:
        """Exécute un outil et retourne le résultat"""
        fn = getattr(self, f"_tool_{tool_name}", None)
        if not fn:
            return {"error": f"Outil '{tool_name}' non trouvé"}
        try:
            return fn(**params)
        except Exception as e:
            return {"error": str(e)}

    def _tool_web_search(self, query: str, type: str = "web"):
        from tools.search_tool import web_search, news_search, format_results_for_ai
        if type == "actualité" or type == "news":
            results = news_search(query)
        else:
            results = web_search(query)
        return {
            "results": results,
            "summary": format_results_for_ai(results),
            "action": {"type": "open_url", "url": f"https://duckduckgo.com/?q={query.replace(' ','+')}"}
        }

    def _tool_get_wikipedia(self, topic: str):
        try:
            import wikipediaapi
            wiki = wikipediaapi.Wikipedia('JARVIS/1.0', 'fr')
            page = wiki.page(topic)
            if not page.exists():
                wiki_en = wikipediaapi.Wikipedia('JARVIS/1.0', 'en')
                page = wiki_en.page(topic)
            if page.exists():
                summary = page.summary[:800]
                return {"title": page.title, "summary": summary, "url": page.fullurl}
            return {"error": "Page non trouvée"}
        except ImportError:
            # Fallback via l'API REST Wikipedia sans librairie
            import requests
            r = requests.get(
                f"https://fr.wikipedia.org/api/rest_v1/page/summary/{topic.replace(' ','_')}",
                timeout=5
            )
            if r.status_code == 200:
                data = r.json()
                return {"title": data.get("title"), "summary": data.get("extract","")[:800],
                        "url": data.get("content_urls",{}).get("desktop",{}).get("page","")}
            return {"error": "Wikipedia inaccessible"}

    def _tool_get_system_info(self):
        import psutil
        cpu    = psutil.cpu_percent(interval=1)
        ram    = psutil.virtual_memory()
        disk   = psutil.disk_usage('/')
        bat    = psutil.sensors_battery()
        return {
            "cpu_percent":  cpu,
            "ram_used_gb":  round(ram.used / 1e9, 1),
            "ram_total_gb": round(ram.total / 1e9, 1),
            "ram_percent":  ram.percent,
            "disk_free_gb": round(disk.free / 1e9, 1),
            "disk_total_gb":round(disk.total / 1e9, 1),
            "battery":      f"{bat.percent:.0f}% {'(en charge)' if bat.power_plugged else ''}" if bat else "N/A",
            "platform":     platform.system(),
            "summary": f"CPU: {cpu}% | RAM: {ram.percent}% ({round(ram.used/1e9,1)}/{round(ram.total/1e9,1)}GB) | Disque: {round(disk.free/1e9,1)}GB libre"
        }

    def _tool_check_internet_speed(self):
        try:
            import speedtest
            st = speedtest.Speedtest()
            st.get_best_server()
            down = round(st.download() / 1e6, 1)
            up   = round(st.upload()   / 1e6, 1)
            ping = round(st.results.ping, 1)
            return {"download_mbps": down, "upload_mbps": up, "ping_ms": ping,
                    "summary": f"↓ {down} Mbps  ↑ {up} Mbps  ping: {ping}ms"}
        except:
            return {"error": "speedtest-cli non installé. Faire: pip install speedtest-cli"}

    def _tool_take_screenshot(self, region: str = "full"):
        import pyautogui
        path = os.path.join(os.path.expanduser("~"), "jarvis_screenshot.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(path)
        return {"path": path, "summary": f"Screenshot sauvegardé: {path}"}

    def _tool_control_mouse(self, action: str, x: int = None, y: int = None):
        import pyautogui
        pyautogui.FAILSAFE = True
        if action == "move" and x and y:
            pyautogui.moveTo(x, y, duration=0.3)
        elif action == "click":
            if x and y: pyautogui.click(x, y)
            else: pyautogui.click()
        elif action == "double_click":
            if x and y: pyautogui.doubleClick(x, y)
            else: pyautogui.doubleClick()
        elif action == "right_click":
            if x and y: pyautogui.rightClick(x, y)
            else: pyautogui.rightClick()
        elif action == "scroll":
            pyautogui.scroll(3 if not y else y)
        return {"done": True, "summary": f"Souris: {action} en ({x},{y})"}

    def _tool_type_text(self, text: str, press_enter: bool = False):
        import pyautogui
        pyautogui.write(text, interval=0.03)
        if press_enter:
            pyautogui.press('enter')
        return {"done": True, "summary": f"Texte tapé: {text[:50]}..."}

    def _tool_open_application(self, app_name: str):
        apps_windows = {
            "notepad":     "notepad.exe",
            "calculator":  "calc.exe",
            "paint":       "mspaint.exe",
            "explorer":    "explorer.exe",
            "cmd":         "cmd.exe",
            "powershell":  "powershell.exe",
            "vscode":      "code",
            "chrome":      "chrome",
            "firefox":     "firefox",
            "edge":        "msedge",
            "spotify":     "spotify",
            "discord":     "discord"
        }
        name = app_name.lower()
        cmd = apps_windows.get(name, app_name)
        if platform.system() == "Windows":
            os.startfile(cmd) if os.path.exists(cmd) else subprocess.Popen([cmd])
        elif platform.system() == "Darwin":  # Mac
            subprocess.Popen(["open", "-a", app_name])
        else:  # Linux
            subprocess.Popen([cmd])
        return {"done": True, "summary": f"Application '{app_name}' lancée"}

    def _tool_get_weather(self, city: str):
        import requests
        # wttr.in : API météo 100% gratuite, aucune clé
        r = requests.get(f"https://wttr.in/{city.replace(' ','+')}?format=j1", timeout=5)
        if r.status_code == 200:
            data = r.json()
            current = data['current_condition'][0]
            desc = current['weatherDesc'][0]['value']
            temp = current['temp_C']
            feels = current['FeelsLikeC']
            wind = current['windspeedKmph']
            return {
                "city": city, "description": desc,
                "temp_c": temp, "feels_like_c": feels, "wind_kmh": wind,
                "summary": f"{city}: {desc}, {temp}°C (ressenti {feels}°C), vent {wind}km/h"
            }
        return {"error": "Météo indisponible"}

    def _tool_calculate(self, expression: str):
        # Sécurisé : seulement les opérations math
        import math
        allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith('_')}
        allowed.update({'abs': abs, 'round': round, 'min': min, 'max': max})
        try:
            result = eval(expression, {"__builtins__": {}}, allowed)
            return {"result": result, "expression": expression,
                    "summary": f"{expression} = {result}"}
        except Exception as e:
            return {"error": str(e)}

    def _tool_read_clipboard(self):
        try:
            import pyperclip
            content = pyperclip.paste()
            return {"content": content[:500], "summary": f"Presse-papier: {content[:100]}..."}
        except:
            return {"error": "pyperclip non installé"}

    def _tool_write_file(self, filename: str, content: str):
        path = os.path.join(os.path.expanduser("~/Desktop"), filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"path": path, "summary": f"Fichier créé: {path}"}

    def _tool_get_time_date(self):
        now = datetime.datetime.now()
        return {
            "time": now.strftime("%H:%M:%S"),
            "date": now.strftime("%A %d %B %Y"),
            "iso":  now.isoformat(),
            "summary": f"{now.strftime('%H:%M')} — {now.strftime('%d/%m/%Y')}"
        }

    def _tool_youtube_search(self, query: str):
        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        return {
            "url": url,
            "summary": f"Recherche YouTube: {query}",
            "action": {"type": "open_url", "url": url}
        }

    def _tool_set_reminder(self, message: str, minutes: int):
        import threading
        def remind():
            import time
            time.sleep(minutes * 60)
            # Notification via pyttsx3 ou notification système
            try:
                import pyttsx3
                e = pyttsx3.init()
                e.say(f"Rappel : {message}")
                e.runAndWait()
            except:
                pass
        threading.Thread(target=remind, daemon=True).start()
        return {"set": True, "summary": f"Rappel dans {minutes} min: {message}"}


executor = ToolExecutor()
