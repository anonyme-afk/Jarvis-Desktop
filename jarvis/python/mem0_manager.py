"""
Mémoire long terme avec Mem0.
Source : github.com/mem0ai/mem0
pip install mem0ai
Fallback sur ChromaDB si Mem0 non dispo.
"""
import os
import json

class AdvancedMemory:
    def __init__(self):
        self.backend = None
        self.user_id = "jarvis_owner"
        self._init_backend()

    def _init_backend(self):
        # Essayer Mem0 en premier
        try:
            from mem0 import Memory
            config = {
                "llm": {
                    "provider": "gemini",
                    "config": {"model": "gemini-1.5-flash",
                               "api_key": os.environ.get("GEMINI_API_KEY")}
                },
                "embedder": {
                    "provider": "gemini",
                    "config": {"model": "models/text-embedding-004",
                               "api_key": os.environ.get("GEMINI_API_KEY")}
                }
            }
            self.client = Memory.from_config(config)
            self.backend = "mem0"
            print("[MEM0] Mem0 initialisé")
            return
        except ImportError:
            pass

        # Fallback : ChromaDB local
        try:
            import chromadb
            client = chromadb.PersistentClient(path="./jarvis_chroma_db")
            self.collection = client.get_or_create_collection("jarvis_memory")
            self.backend = "chromadb"
            print("[MEM0] ChromaDB initialisé (fallback)")
            return
        except ImportError:
            pass

        # Fallback final : JSON simple
        self.backend = "json"
        self.json_file = os.path.join(os.path.dirname(__file__), "simple_memory.json")
        print("[MEM0] Mémoire JSON simple (fallback)")

    def add(self, text: str, metadata: dict = None):
        if self.backend == "mem0":
            self.client.add(text, user_id=self.user_id, metadata=metadata or {})
        elif self.backend == "chromadb":
            import uuid
            self.collection.add(
                documents=[text],
                ids=[str(uuid.uuid4())],
                metadatas=[metadata or {}]
            )
        elif self.backend == "json":
            data = self._load_json()
            data.append({"text": text, "meta": metadata or {}})
            self._save_json(data)

    def search(self, query: str, limit: int = 5) -> list:
        if self.backend == "mem0":
            results = self.client.search(query, user_id=self.user_id, limit=limit)
            return [r.get("memory", "") for r in results.get("results", [])]
        elif self.backend == "chromadb":
            results = self.collection.query(query_texts=[query], n_results=limit)
            return results.get("documents", [[]])[0]
        elif self.backend == "json":
            data = self._load_json()
            return [d["text"] for d in data[-limit:]]
        return []

    def get_context_for_prompt(self, query: str) -> str:
        memories = self.search(query, limit=5)
        if not memories:
            return ""
        return "Mémoire contextuelle:\n" + "\n".join(f"- {m}" for m in memories)

    def _load_json(self):
        if os.path.exists(self.json_file):
            with open(self.json_file, 'r') as f:
                return json.load(f)
        return []

    def _save_json(self, data):
        with open(self.json_file, 'w') as f:
            json.dump(data[-500:], f)  # Garder les 500 derniers

advanced_memory = AdvancedMemory()
