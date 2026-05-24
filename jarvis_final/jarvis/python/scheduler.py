import threading, datetime

class JARVISScheduler:
    def __init__(self, callback):
        self.callback = callback
        self._reminders = []

    def start(self):
        print("[Scheduler] Démarré")

    def add_reminder(self, message: str, minutes: int):
        def remind():
            import time
            time.sleep(minutes * 60)
            self.callback(f"Rappel : {message}", "normal")
        threading.Thread(target=remind, daemon=True).start()
        print(f"[Scheduler] Rappel dans {minutes}min: {message}")

jarvis_scheduler = JARVISScheduler(lambda m, p: print(f"[Reminder] {m}"))
