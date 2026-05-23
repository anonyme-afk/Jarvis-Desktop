"""
Mémoire persistante de JARVIS.
Stocke les faits importants, les préférences et l'historique.
Fichier JSON local, jamais envoyé sur le cloud.
"""
import json
import os
from datetime import datetime

MEMORY_FILE = os.path.join(os.path.dirname(__file__), 'jarvis_memory.json')

class Memory:
    def __init__(self):
        self.data = self._load()

    def _load(self):
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "facts": [],           # Faits mémorisés ("je m'appelle X", "j'habite à Y")
            "preferences": {},     # Préférences ("provider": "groq", "langue": "fr")
            "history": [],         # Historique résumé des conversations
            "created_at": datetime.now().isoformat()
        }

    def save(self):
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_fact(self, fact: str):
        """Ajouter un fait mémorisé"""
        if fact not in self.data['facts']:
            self.data['facts'].append(fact)
            self.save()

    def set_preference(self, key: str, value):
        self.data['preferences'][key] = value
        self.save()

    def get_preference(self, key: str, default=None):
        return self.data['preferences'].get(key, default)

    def add_to_history(self, summary: str):
        """Ajouter un résumé de conversation"""
        self.data['history'].append({
            "date": datetime.now().isoformat(),
            "summary": summary
        })
        # Garder seulement les 50 dernières entrées
        if len(self.data['history']) > 50:
            self.data['history'] = self.data['history'][-50:]
        self.save()

    def get_context_string(self) -> str:
        """Génère un résumé de la mémoire pour le contexte du prompt"""
        parts = []
        if self.data['facts']:
            parts.append("Faits mémorisés: " + "; ".join(self.data['facts'][-10:]))
        if self.data['preferences']:
            prefs = ", ".join(f"{k}={v}" for k,v in self.data['preferences'].items())
            parts.append(f"Préférences: {prefs}")
        if self.data['history']:
            last = self.data['history'][-3:]
            parts.append("Dernières interactions: " + "; ".join(h['summary'] for h in last))
        return "\n".join(parts) if parts else ""

    def extract_facts_from_message(self, message: str) -> list:
        """Détecte les faits à mémoriser dans un message"""
        triggers = [
            ("je m'appelle ", "prénom"),
            ("mon nom est ", "nom"),
            ("j'habite ", "lieu"),
            ("j'ai ", "info"),
            ("souviens-toi ", "mémoire"),
            ("mémorise ", "mémoire"),
            ("retiens que ", "mémoire"),
            ("remember ", "mémoire")
        ]
        facts = []
        msg_lower = message.lower()
        for trigger, _ in triggers:
            if trigger in msg_lower:
                idx = msg_lower.index(trigger)
                fact = message[idx:idx+100].strip()
                facts.append(fact)
        return facts

memory = Memory()
