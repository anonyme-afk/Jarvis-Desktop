import json, os
from datetime import datetime

MEMORY_FILE = os.path.join(os.path.dirname(__file__), 'jarvis_memory.json')

class Memory:
    def __init__(self):
        self.data = self._load()

    def _load(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"facts": [], "preferences": {}, "history": [], "created_at": datetime.now().isoformat()}

    def save(self):
        try:
            with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Memory] Erreur sauvegarde: {e}")

    def add_fact(self, fact: str):
        if fact and fact not in self.data['facts']:
            self.data['facts'].append(fact)
            if len(self.data['facts']) > 200:
                self.data['facts'] = self.data['facts'][-200:]
            self.save()

    def set_preference(self, key: str, value):
        self.data['preferences'][key] = value
        self.save()

    def get_preference(self, key: str, default=None):
        return self.data['preferences'].get(key, default)

    def add_to_history(self, summary: str):
        self.data['history'].append({"date": datetime.now().isoformat(), "summary": summary})
        if len(self.data['history']) > 50:
            self.data['history'] = self.data['history'][-50:]
        self.save()

    def get_context_string(self) -> str:
        parts = []
        if self.data['facts']:
            parts.append("Faits: " + "; ".join(self.data['facts'][-8:]))
        if self.data['preferences']:
            parts.append("Préfs: " + ", ".join(f"{k}={v}" for k,v in self.data['preferences'].items()))
        return "\n".join(parts)

    def extract_facts_from_message(self, message: str) -> list:
        triggers = ["je m'appelle ", "mon nom est ", "j'habite ", "souviens-toi ", "mémorise ", "retiens que "]
        facts = []
        msg_lower = message.lower()
        for t in triggers:
            if t in msg_lower:
                idx = msg_lower.index(t)
                facts.append(message[idx:idx+80].strip())
        return facts

memory = Memory()
