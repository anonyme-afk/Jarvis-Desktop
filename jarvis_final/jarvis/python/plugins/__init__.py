from .base_plugin import BasePlugin

class BrowserPlugin(BasePlugin):
    name = "browser"
    TRIGGERS = ["ouvre", "va sur", "cherche", "youtube", "google", "maps"]
    def can_handle(self, message: str) -> bool:
        return any(t in message.lower() for t in self.TRIGGERS)
    def handle(self, message: str, context: dict) -> dict:
        msg = message.lower()
        if 'youtube' in msg:
            q = msg.replace('youtube','').replace('ouvre','').replace('cherche','').strip()
            url = f"https://www.youtube.com/results?search_query={q.replace(' ','+')}'" if q else "https://youtube.com"
            return {"reply": f"J'ouvre YouTube.", "action": {"type": "open_url", "url": url}}
        if 'maps' in msg or 'carte' in msg:
            q = msg.replace('maps','').replace('carte','').replace('montre','').strip()
            url = f"https://www.google.com/maps/search/{q.replace(' ', '+')}"
            return {"reply": f"J'affiche la carte.", "action": {"type": "open_url", "url": url}}
        return {"reply": None, "action": None}

ALL_PLUGINS = [BrowserPlugin()]

def find_plugin(message: str):
    for p in ALL_PLUGINS:
        if p.enabled and p.can_handle(message):
            return p
    return None
