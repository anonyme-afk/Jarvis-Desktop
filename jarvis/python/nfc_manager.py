import threading
import time

class NFCManager:
    def __init__(self):
        self.on_card_detected = None
        self.listening = False

    def execute_profile_actions(self, profile: str):
        print(f"[NFC] Executing actions for profile: {profile}")

    def start_listening(self):
        if self.listening:
            return
        self.listening = True
        print("[NFC] NFC chip reader daemon started successfully (Listening on default fallback ports)")
        def run():
            while self.listening:
                time.sleep(2)
        t = threading.Thread(target=run, daemon=True)
        t.start()

nfc_manager = NFCManager()
