"""
Gestionnaire universel de fournisseurs IA.
Ajouter un nouveau provider = ajouter un bloc dans PROVIDERS.
"""
import os
import json
import requests

# ===== REGISTRE DES PROVIDERS =====
PROVIDERS = {

    # ---- GRATUITS (tier gratuit disponible) ----
    "gemini-free": {
        "name": "Gemini 1.5 Flash (Gratuit)",
        "model": "gemini-1.5-flash",
        "type": "gemini",
        "env_key": "GEMINI_API_KEY",
        "free": True,
        "vision": True,
        "url": "https://aistudio.google.com"
    },
    "groq-free": {
        "name": "Groq Llama3 (Gratuit ultra-rapide)",
        "model": "llama-3.1-8b-instant",
        "type": "openai_compat",
        "env_key": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "free": True,
        "vision": False,
        "url": "https://console.groq.com"
    },
    "mistral-free": {
        "name": "Mistral Small (Gratuit)",
        "model": "mistral-small-latest",
        "type": "openai_compat",
        "env_key": "MISTRAL_API_KEY",
        "base_url": "https://api.mistral.ai/v1",
        "free": True,
        "vision": False,
        "url": "https://console.mistral.ai"
    },
    "cohere-free": {
        "name": "Cohere Command R (Gratuit)",
        "model": "command-r",
        "type": "cohere",
        "env_key": "COHERE_API_KEY",
        "free": True,
        "vision": False,
        "url": "https://dashboard.cohere.com"
    },

    # ---- PAYANTS (qualité supérieure) ----
    "gemini-pro": {
        "name": "Gemini 1.5 Pro (Payant)",
        "model": "gemini-1.5-pro",
        "type": "gemini",
        "env_key": "GEMINI_API_KEY",
        "free": False,
        "vision": True
    },
    "claude-sonnet": {
        "name": "Claude Sonnet 4 (Payant)",
        "model": "claude-sonnet-4-5",
        "type": "anthropic",
        "env_key": "ANTHROPIC_API_KEY",
        "free": False,
        "vision": True,
        "url": "https://console.anthropic.com"
    },
    "gpt4o": {
        "name": "GPT-4o (Payant)",
        "model": "gpt-4o",
        "type": "openai_compat",
        "env_key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "free": False,
        "vision": True,
        "url": "https://platform.openai.com"
    },
    "grok": {
        "name": "Grok 2 (xAI)",
        "model": "grok-2-latest",
        "type": "openai_compat",
        "env_key": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
        "free": False,
        "vision": True,
        "url": "https://console.x.ai"
    },
    "deepseek": {
        "name": "DeepSeek V3 (Très bon rapport qualité/prix)",
        "model": "deepseek-chat",
        "type": "openai_compat",
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1",
        "free": False,
        "vision": False,
        "url": "https://platform.deepseek.com"
    },

    # ---- LOCAL via Ollama ----
    "ollama-auto": {
        "name": "Ollama (Local - modèle auto-détecté)",
        "model": "AUTO",
        "type": "ollama",
        "env_key": None,
        "free": True,
        "vision": True
    }
}

SYSTEM_PROMPT = """Tu es JARVIS, l'assistant IA personnel de l'utilisateur.
Tu es calme, précis, légèrement formel mais jamais condescendant.
Tu parles comme l'IA dans Iron Man : concis, factuel, avec parfois de l'humour sec.
Réponds en 1-3 phrases max sauf si plus demandé.
Pour ouvrir un site : réponds UNIQUEMENT avec {"action":"open_url","url":"..."}
Pour une action système : {"action":"system","command":"..."}
Pour afficher une carte : {"action":"show_map","query":"..."}
"""

class AIProvider:
    def __init__(self):
        # Charger le provider actif depuis .env ou défaut
        provider_id = os.environ.get('AI_PROVIDER', 'gemini-free')
        self.set_provider(provider_id)

    def set_provider(self, provider_id: str):
        if provider_id not in PROVIDERS:
            provider_id = 'gemini-free'
        self.current = PROVIDERS[provider_id]
        self.provider_id = provider_id
        print(f"[JARVIS] Provider: {self.current['name']}")

    def get_available_providers(self):
        """Retourne les providers dont la clé API est configurée"""
        available = []
        for pid, p in PROVIDERS.items():
            has_key = True
            if p['env_key']:
                has_key = bool(os.environ.get(p['env_key']))
            if p['type'] == 'ollama':
                # Vérifier si Ollama tourne
                try:
                    r = requests.get('http://localhost:11434/api/tags', timeout=2)
                    has_key = r.status_code == 200
                except:
                    has_key = False
            available.append({
                "id": pid,
                "name": p["name"],
                "free": p["free"],
                "available": has_key,
                "vision": p["vision"]
            })
        return available

    def get_ollama_models(self):
        """Liste tous les modèles Ollama installés"""
        try:
            r = requests.get('http://localhost:11434/api/tags', timeout=3)
            models = r.json().get('models', [])
            return [m['name'] for m in models]
        except:
            return []

    def chat(self, messages: list, image_b64: str = None) -> str:
        p = self.current
        ptype = p['type']

        if ptype == 'gemini':
            return self._chat_gemini(messages, image_b64)
        elif ptype == 'openai_compat':
            return self._chat_openai_compat(messages, image_b64)
        elif ptype == 'anthropic':
            return self._chat_anthropic(messages, image_b64)
        elif ptype == 'cohere':
            return self._chat_cohere(messages)
        elif ptype == 'ollama':
            return self._chat_ollama(messages, image_b64)
        else:
            return "Provider non supporté."

    def _chat_gemini(self, messages, image_b64=None):
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        model = genai.GenerativeModel(self.current['model'])
        parts = [SYSTEM_PROMPT]
        for m in messages:
            parts.append(f"{'User' if m['role']=='user' else 'JARVIS'}: {m['content']}")
        if image_b64:
            import base64
            parts.append({"mime_type":"image/jpeg","data":image_b64})
        r = model.generate_content(parts)
        return r.text

    def _chat_openai_compat(self, messages, image_b64=None):
        api_key = os.environ.get(self.current['env_key'], '')
        base_url = self.current.get('base_url', 'https://api.openai.com/v1')
        msgs = [{"role":"system","content":SYSTEM_PROMPT}]
        for m in messages[:-1]:
            msgs.append({"role":m['role'],"content":m['content']})
        last = messages[-1]
        if image_b64 and self.current.get('vision'):
            content = [
                {"type":"text","text":last['content']},
                {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{image_b64}"}}
            ]
        else:
            content = last['content']
        msgs.append({"role":"user","content":content})
        r = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
            json={"model":self.current['model'],"messages":msgs,"max_tokens":500},
            timeout=30
        )
        return r.json()['choices'][0]['message']['content']

    def _chat_anthropic(self, messages, image_b64=None):
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        msgs = []
        for m in messages:
            if image_b64 and m == messages[-1] and self.current.get('vision'):
                msgs.append({"role":"user","content":[
                    {"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":image_b64}},
                    {"type":"text","text":m['content']}
                ]})
            else:
                msgs.append({"role":m['role'],"content":m['content']})
        r = client.messages.create(
            model=self.current['model'],
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=msgs
        )
        return r.content[0].text

    def _chat_cohere(self, messages):
        import cohere
        client = cohere.Client(os.environ.get('COHERE_API_KEY'))
        history = [{"role":"CHATBOT" if m['role']=='assistant' else "USER","message":m['content']} for m in messages[:-1]]
        r = client.chat(
            model=self.current['model'],
            preamble=SYSTEM_PROMPT,
            chat_history=history,
            message=messages[-1]['content']
        )
        return r.text

    def _chat_ollama(self, messages, image_b64=None):
        # Auto-détecter le meilleur modèle installé
        model = os.environ.get('OLLAMA_MODEL', 'AUTO')
        if model == 'AUTO':
            installed = self.get_ollama_models()
            # Priorité : modèles vision > gros modèles > petits modèles
            priority = ['llava','llama3.2','llama3.1','mistral','qwen','gemma','phi3','tinyllama']
            model = 'llama3.2'  # défaut
            for p in priority:
                found = next((m for m in installed if p in m.lower()), None)
                if found:
                    model = found
                    break

        msgs = [{"role":"system","content":SYSTEM_PROMPT}] + \
               [{"role":m['role'],"content":m['content']} for m in messages]

        payload = {"model":model,"messages":msgs,"stream":False}
        if image_b64 and 'llava' in model.lower():
            payload['images'] = [image_b64]

        r = requests.post('http://localhost:11434/api/chat', json=payload, timeout=60)
        return r.json()['message']['content']

# Instance globale
ai = AIProvider()
