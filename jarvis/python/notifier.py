import sys

class Notifier:
    def __init__(self):
        self.apprise_obj = None
        try:
            import apprise
            self.apprise_obj = apprise.Apprise()
        except Exception as e:
            print(f"[Notifier] Apprise unavailable, using print-only fallback. Error: {e}")

    def notify(self, title: str, message: str, urgent: bool = False):
        print(f"[Notifier] NOTIFICATION ({'URGENT' if urgent else 'INFO'}): {title} - {message}")
        try:
            if self.apprise_obj:
                # Apprise notification can be sent if configured
                pass
        except Exception as e:
            print(f"[Notifier] Apprise notify error: {e}")

notifier = Notifier()
