"""
Registre d'outils JARVIS — tous les imports sont protégés
"""
import os, json, subprocess, platform, datetime

TOOLS_SCHEMA = [
    {"name": "web_search",      "description": "Chercher sur internet. Utiliser pour actualités, prix, météo, infos récentes.", "parameters": {"query": "str", "type": "str: web|news|image"}},
    {"name": "get_weather",     "description": "Météo actuelle d'une ville.", "parameters": {"city": "str"}},
    {"name": "get_system_info", "description": "Infos système: CPU, RAM, disque, batterie.", "parameters": {}},
    {"name": "check_internet_speed", "description": "Tester la vitesse internet.", "parameters": {}},
    {"name": "take_screenshot", "description": "Prendre une capture d'écran.", "parameters": {}},
    {"name": "control_mouse",   "description": "Contrôler la souris.", "parameters": {"action": "str: click|move|scroll", "x": "int", "y": "int"}},
    {"name": "type_text",       "description": "Taper du texte au clavier.", "parameters": {"text": "str", "press_enter": "bool"}},
    {"name": "open_application","description": "Ouvrir une application PC.", "parameters": {"app_name": "str"}},
    {"name": "calculate",       "description": "Calcul mathématique.", "parameters": {"expression": "str"}},
    {"name": "read_clipboard",  "description": "Lire le presse-papier.", "parameters": {}},
    {"name": "write_file",      "description": "Créer un fichier texte.", "parameters": {"filename": "str", "content": "str"}},
    {"name": "get_time_date",   "description": "Heure et date actuelles.", "parameters": {}},
    {"name": "youtube_search",  "description": "Ouvrir YouTube avec une recherche.", "parameters": {"query": "str"}},
    {"name": "set_reminder",    "description": "Créer un rappel vocal.", "parameters": {"message": "str", "minutes": "int"}},
    {"name": "get_wikipedia",   "description": "Infos Wikipedia sur un sujet.", "parameters": {"topic": "str"}},
]

class ToolExecutor:
    def execute(self, tool_name: str, params: dict) -> dict:
        fn = getattr(self, f"_tool_{tool_name}", None)
        if not fn:
            return {"error": f"Outil '{tool_name}' inconnu"}
        try:
            return fn(**{k: v for k, v in params.items() if v is not None})
        except Exception as e:
            return {"error": str(e)}

    def _tool_web_search(self, query: str, type: str = "web"):
        try:
            from search_tool import web_search, news_search, format_results_for_ai
            results = news_search(query) if type == "news" else web_search(query)
            return {"results": results, "summary": format_results_for_ai(results),
                    "action": {"type": "open_url", "url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}"}}
        except ImportError:
            return {"error": "duckduckgo-search non installé", "summary": f"pip install duckduckgo-search"}

    def _tool_get_weather(self, city: str):
        try:
            import requests
            r = requests.get(f"https://wttr.in/{city.replace(' ', '+')}?format=j1", timeout=5)
            d = r.json()
            c = d['current_condition'][0]
            return {"city": city, "temp_c": c['temp_C'],
                    "description": c['weatherDesc'][0]['value'], "wind": c['windspeedKmph'],
                    "summary": f"{city}: {c['weatherDesc'][0]['value']}, {c['temp_C']}°C, vent {c['windspeedKmph']}km/h"}
        except Exception as e:
            return {"error": str(e)}

    def _tool_get_system_info(self):
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            bat = psutil.sensors_battery()
            return {
                "cpu_percent": cpu, "ram_percent": ram.percent,
                "ram_used_gb": round(ram.used/1e9,1), "ram_total_gb": round(ram.total/1e9,1),
                "disk_free_gb": round(disk.free/1e9,1),
                "battery": f"{bat.percent:.0f}%" if bat else "N/A",
                "summary": f"CPU: {cpu}% | RAM: {ram.percent}% ({round(ram.used/1e9,1)}/{round(ram.total/1e9,1)}GB) | Disque: {round(disk.free/1e9,1)}GB libre"
            }
        except ImportError:
            return {"error": "psutil non installé"}

    def _tool_check_internet_speed(self):
        try:
            import speedtest
            st = speedtest.Speedtest()
            st.get_best_server()
            down = round(st.download()/1e6,1)
            up   = round(st.upload()/1e6,1)
            ping = round(st.results.ping,1)
            return {"download_mbps": down, "upload_mbps": up, "ping_ms": ping,
                    "summary": f"↓{down} Mbps  ↑{up} Mbps  ping:{ping}ms"}
        except ImportError:
            return {"error": "speedtest-cli non installé"}

    def _tool_take_screenshot(self):
        try:
            import pyautogui, os
            path = os.path.join(os.path.expanduser("~"), "Desktop", "jarvis_screenshot.png")
            pyautogui.screenshot().save(path)
            return {"path": path, "summary": f"Screenshot sauvegardé: {path}"}
        except ImportError:
            return {"error": "pyautogui non installé"}

    def _tool_control_mouse(self, action: str, x: int = None, y: int = None):
        try:
            import pyautogui
            if action == "click":
                if x and y: pyautogui.click(x, y)
                else: pyautogui.click()
            elif action == "move" and x and y:
                pyautogui.moveTo(x, y, duration=0.3)
            elif action == "scroll":
                pyautogui.scroll(y or 3)
            return {"done": True, "summary": f"Souris: {action}"}
        except ImportError:
            return {"error": "pyautogui non installé"}

    def _tool_type_text(self, text: str, press_enter: bool = False):
        try:
            import pyautogui
            pyautogui.write(text, interval=0.03)
            if press_enter: pyautogui.press('enter')
            return {"done": True, "summary": f"Texte tapé: {text[:50]}"}
        except ImportError:
            return {"error": "pyautogui non installé"}

    def _tool_open_application(self, app_name: str):
        apps = {"notepad":"notepad.exe","calculator":"calc.exe","paint":"mspaint.exe",
                "explorer":"explorer.exe","cmd":"cmd.exe","chrome":"chrome","firefox":"firefox",
                "spotify":"spotify","discord":"discord","vscode":"code"}
        cmd = apps.get(app_name.lower(), app_name)
        try:
            if platform.system() == "Windows":
                subprocess.Popen([cmd], shell=True)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", "-a", app_name])
            else:
                subprocess.Popen([cmd])
            return {"done": True, "summary": f"'{app_name}' lancé"}
        except Exception as e:
            return {"error": str(e)}

    def _tool_calculate(self, expression: str):
        import math
        allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith('_')}
        allowed.update({'abs': abs, 'round': round, 'min': min, 'max': max})
        try:
            result = eval(expression, {"__builtins__": {}}, allowed)
            return {"result": result, "summary": f"{expression} = {result}"}
        except Exception as e:
            return {"error": str(e)}

    def _tool_read_clipboard(self):
        try:
            import pyperclip
            content = pyperclip.paste()
            return {"content": content[:400], "summary": f"Presse-papier: {content[:80]}"}
        except ImportError:
            return {"error": "pyperclip non installé"}

    def _tool_write_file(self, filename: str, content: str):
        path = os.path.join(os.path.expanduser("~/Desktop"), filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"path": path, "summary": f"Fichier créé: {path}"}

    def _tool_get_time_date(self):
        now = datetime.datetime.now()
        return {"time": now.strftime("%H:%M:%S"), "date": now.strftime("%A %d %B %Y"),
                "summary": f"{now.strftime('%H:%M')} — {now.strftime('%d/%m/%Y')}"}

    def _tool_youtube_search(self, query: str):
        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        return {"url": url, "summary": f"YouTube: {query}",
                "action": {"type": "open_url", "url": url}}

    def _tool_set_reminder(self, message: str, minutes: int):
        import threading, time
        def remind():
            time.sleep(minutes * 60)
            try:
                import pyttsx3
                e = pyttsx3.init(); e.say(f"Rappel: {message}"); e.runAndWait()
            except: pass
        threading.Thread(target=remind, daemon=True).start()
        return {"set": True, "summary": f"Rappel dans {minutes}min: {message}"}

    def _tool_get_wikipedia(self, topic: str):
        try:
            import requests
            r = requests.get(
                f"https://fr.wikipedia.org/api/rest_v1/page/summary/{topic.replace(' ','_')}",
                timeout=5)
            if r.status_code == 200:
                d = r.json()
                return {"title": d.get("title"), "summary": d.get("extract","")[:600],
                        "url": d.get("content_urls",{}).get("desktop",{}).get("page","")}
            return {"error": "Page introuvable"}
        except Exception as e:
            return {"error": str(e)}

executor = ToolExecutor()
