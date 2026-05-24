import os
import json
import threading
from datetime import datetime

MEM0_FILE = os.path.join(os.path.dirname(__file__), 'jarvis_mem0.json')

class AdvancedMemory:
    def __init__(self):
        self.backend = "local"
        self._lock = threading.Lock()
        self.data = self._load()

    def _load(self):
        if os.path.exists(MEM0_FILE):
            try:
                with open(MEM0_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"items": []}

    def _save(self):
        try:
            with open(MEM0_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Mem0] Erreur sauvegarde: {e}")

    def add(self, text: str):
        with self._lock:
            clean_text = text.strip()
            if not clean_text:
                return
            
            for item in self.data["items"]:
                if item["text"].lower() == clean_text.lower():
                    item["updated_at"] = datetime.now().isoformat()
                    self._save()
                    return

            self.data["items"].append({
                "text": clean_text,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
            if len(self.data["items"]) > 500:
                self.data["items"] = self.data["items"][-500:]
            self._save()
            print(f"[Mem0] Memorized fact: {clean_text}")

    def get_context_for_prompt(self, message: str) -> str:
        with self._lock:
            if not self.data["items"]:
                return ""
            
            msg_words = set(message.lower().split())
            if not msg_words:
                recent = [item["text"] for item in self.data["items"][-10:]]
                return "\n".join(recent)

            scored_items = []
            for item in self.data["items"]:
                item_words = set(item["text"].lower().split())
                common = msg_words.intersection(item_words)
                if common:
                    score = len(common)
                    scored_items.append((score, item["text"]))

            scored_items.sort(key=lambda x: x[0], reverse=True)
            matches = [text for score, text in scored_items[:10]]
            
            if not matches:
                matches = [item["text"] for item in self.data["items"][-5:]]

            return "Contextes memorises:\n" + "\n".join(f"- {m}" for m in matches)

advanced_memory = AdvancedMemory()
