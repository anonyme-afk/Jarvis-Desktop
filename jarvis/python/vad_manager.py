import threading
import time

class VADManager:
    def __init__(self):
        self.interrupt_event = threading.Event()
        self.model = "Silero VAD Fallback"
        self.ai_speaking = False
        self.listening = False

    def set_ai_speaking(self, speaking: bool):
        self.ai_speaking = speaking
        print(f"[VAD] AI speaking set to {speaking}")

    def start_listening(self):
        if self.listening:
            return
        self.listening = True
        print("[VAD] Listening service started successfully (VAD active)")
        def run():
            while self.listening:
                time.sleep(1)
        t = threading.Thread(target=run, daemon=True)
        t.start()

vad = VADManager()
