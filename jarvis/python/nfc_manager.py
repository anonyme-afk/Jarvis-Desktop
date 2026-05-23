"""
Gestion des cartes NFC pour JARVIS.
Librairie : github.com/nfcpy/nfcpy
Lecteur USB NFC requis (~10€ sur Amazon : ACR122U)
"""
import os
import json
import threading
import subprocess
import platform

PROFILES_FILE = os.path.join(os.path.dirname(__file__), 'nfc_profiles.json')

DEFAULT_PROFILES = {
    "default_profile": {
        "name": "Mode Défaut",
        "color": "#00BFFF",
        "actions": ["greeting"]
    }
}

class NFCManager:
    def __init__(self, on_card_detected=None):
        self.on_card_detected = on_card_detected
        self.profiles = self._load_profiles()
        self.running = False

    def _load_profiles(self) -> dict:
        if os.path.exists(PROFILES_FILE):
            with open(PROFILES_FILE, 'r') as f:
                return json.load(f)
        with open(PROFILES_FILE, 'w') as f:
            json.dump(DEFAULT_PROFILES, f, indent=2)
        return DEFAULT_PROFILES

    def save_profiles(self):
        with open(PROFILES_FILE, 'w') as f:
            json.dump(self.profiles, f, indent=2, ensure_ascii=False)

    def add_profile(self, card_uid: str, profile: dict):
        self.profiles[card_uid] = profile
        self.save_profiles()

    def start_listening(self):
        self.running = True
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def _listen_loop(self):
        try:
            import nfc
            def on_connect(tag):
                uid = tag.identifier.hex()
                profile = self.profiles.get(uid, self.profiles.get("default_profile"))
                if self.on_card_detected:
                    self.on_card_detected(uid, profile)
                return True

            with nfc.ContactlessFrontend('usb') as clf:
                while self.running:
                    clf.connect(rdwr={'on-connect': on_connect})
        except ImportError:
            print("[NFC] nfcpy non installé. pip install nfcpy")
        except Exception as e:
            print(f"[NFC] Lecteur non détecté ou erreur: {e}")

    def execute_profile_actions(self, profile: dict):
        actions = profile.get("actions", [])
        for action in actions:
            if action == "open_vscode":
                subprocess.Popen(["code"])
            elif action == "open_discord":
                subprocess.Popen(["discord"])
            elif action == "optimize_ram":
                self._optimize_ram()
            elif action == "dark_mode":
                self._set_windows_dark_mode()
            elif action == "greeting":
                pass  # Géré par le serveur principal

    def _optimize_ram(self):
        if platform.system() == "Windows":
            subprocess.run(["powershell", "-Command",
                "Clear-RecycleBin -Force; [System.GC]::Collect()"],
                capture_output=True)

    def _set_windows_dark_mode(self):
        if platform.system() == "Windows":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)

nfc_manager = NFCManager()
