"""
Notifications sur Discord, Telegram, WhatsApp, etc.
Source : github.com/caronc/apprise
pip install apprise
"""
import os

class JARVISNotifier:
    def __init__(self):
        self.services = []
        self._load_services()

    def _load_services(self):
        try:
            import apprise
            self.ap = apprise.Apprise()
            # Discord
            if os.environ.get('DISCORD_WEBHOOK'):
                self.ap.add(f"discord://{os.environ['DISCORD_WEBHOOK']}")
                print("[NOTIF] Discord configuré")
            # Telegram
            if os.environ.get('TELEGRAM_TOKEN') and os.environ.get('TELEGRAM_CHAT_ID'):
                self.ap.add(f"tgram://{os.environ['TELEGRAM_TOKEN']}/{os.environ['TELEGRAM_CHAT_ID']}")
                print("[NOTIF] Telegram configuré")
            # Gotify (auto-hébergé, gratuit)
            if os.environ.get('GOTIFY_URL') and os.environ.get('GOTIFY_TOKEN'):
                self.ap.add(f"gotify://{os.environ['GOTIFY_URL']}/{os.environ['GOTIFY_TOKEN']}")
        except ImportError:
            self.ap = None
            print("[NOTIF] apprise non installé")

    def notify(self, title: str, body: str, urgent: bool = False):
        """Envoie une notification sur tous les services configurés"""
        if self.ap:
            import apprise
            notify_type = apprise.NotifyType.FAILURE if urgent else apprise.NotifyType.INFO
            self.ap.notify(title=title, body=body, notify_type=notify_type)

notifier = JARVISNotifier()
