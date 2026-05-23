"""
Plugin contrôle navigateur avancé.
Ouvre des URLs, fait des recherches, prend des screenshots.
"""
import webbrowser
import subprocess
import platform
from .base_plugin import BasePlugin

class BrowserPlugin(BasePlugin):
    name = "browser"
    description = "Contrôle le navigateur, ouvre des sites, fait des recherches"

    TRIGGERS = ["ouvre", "va sur", "cherche", "recherche", "google", "youtube",
                "montre", "navigue", "browse", "search"]

    def can_handle(self, message: str) -> bool:
        return any(t in message.lower() for t in self.TRIGGERS)

    def handle(self, message: str, context: dict) -> dict:
        msg = message.lower()

        # Recherche Google
        if 'cherche' in msg or 'recherche' in msg or 'google' in msg:
            query = message
            for trigger in ['cherche', 'recherche', 'google']:
                query = query.lower().replace(trigger, '').strip()
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            return {"reply": f"Je recherche '{query}'.",
                    "action": {"type": "open_url", "url": url}}

        # YouTube
        if 'youtube' in msg:
            query = msg.replace('youtube', '').replace('ouvre', '').strip()
            if query:
                url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            else:
                url = "https://www.youtube.com"
            return {"reply": "J'ouvre YouTube.", "action": {"type": "open_url", "url": url}}

        # Carte / localisation
        if 'carte' in msg or 'maps' in msg or 'montre' in msg:
            location = msg.replace('montre', '').replace('carte', '').replace('maps', '').strip()
            url = f"https://www.google.com/maps/search/{location.replace(' ', '+')}"
            return {"reply": f"J'affiche {location} sur la carte.",
                    "action": {"type": "open_url", "url": url, "show_map": True}}

        return {"reply": None, "action": None}  # Laisser l'IA principale gérer
