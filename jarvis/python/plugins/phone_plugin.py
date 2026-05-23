"""
Plugin contrôle téléphone Android via ADB (USB ou WiFi).
Prérequis : adb installé sur le PC + débogage USB activé sur le téléphone.
"""
import subprocess
import os
from .base_plugin import BasePlugin

class PhonePlugin(BasePlugin):
    name = "phone"
    description = "Contrôle le téléphone Android branché en USB"

    TRIGGERS = [
        "téléphone", "phone", "android",
        "appelle", "appel", "sms", "message sur mon tel",
        "volume", "screenshot tel", "capture tel"
    ]

    def can_handle(self, message: str) -> bool:
        msg = message.lower()
        return any(t in msg for t in self.TRIGGERS) and self._is_device_connected()

    def _is_device_connected(self) -> bool:
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=3)
            lines = result.stdout.strip().split('\n')
            return len(lines) > 1 and 'device' in lines[1]
        except:
            return False

    def _adb(self, *args) -> str:
        try:
            result = subprocess.run(['adb', *args], capture_output=True, text=True, timeout=10)
            return result.stdout.strip()
        except Exception as e:
            return f"Erreur ADB: {e}"

    def handle(self, message: str, context: dict) -> dict:
        msg = message.lower()

        if 'screenshot' in msg or 'capture' in msg:
            self._adb('shell', 'screencap', '-p', '/sdcard/jarvis_screenshot.png')
            self._adb('pull', '/sdcard/jarvis_screenshot.png', '/tmp/phone_screenshot.png')
            return {"reply": "Screenshot du téléphone pris. Je l'analyse...",
                    "action": {"type": "analyze_image", "path": "/tmp/phone_screenshot.png"}}

        if 'volume' in msg:
            if 'monte' in msg or 'augmente' in msg:
                self._adb('shell', 'input', 'keyevent', 'KEYCODE_VOLUME_UP')
                return {"reply": "Volume augmenté.", "action": None}
            elif 'baisse' in msg or 'diminue' in msg:
                self._adb('shell', 'input', 'keyevent', 'KEYCODE_VOLUME_DOWN')
                return {"reply": "Volume baissé.", "action": None}

        if 'lumière' in msg or 'luminosité' in msg:
            level = '200' if 'monte' in msg else '50'
            self._adb('shell', 'settings', 'put', 'system', 'screen_brightness', level)
            return {"reply": f"Luminosité ajustée.", "action": None}

        if 'ouvre' in msg:
            # Extraire l'app à ouvrir
            apps = {
                'youtube': 'com.google.android.youtube',
                'maps': 'com.google.android.apps.maps',
                'chrome': 'com.android.chrome',
                'spotify': 'com.spotify.music',
                'whatsapp': 'com.whatsapp',
                'instagram': 'com.instagram.android'
            }
            for app_name, package in apps.items():
                if app_name in msg:
                    self._adb('shell', 'monkey', '-p', package, '-c', 'android.intent.category.LAUNCHER', '1')
                    return {"reply": f"J'ouvre {app_name} sur ton téléphone.", "action": None}

        return {"reply": "Téléphone connecté. Que voulez-vous faire ?", "action": None}
