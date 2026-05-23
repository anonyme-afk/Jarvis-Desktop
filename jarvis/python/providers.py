"""
Gestionnaire universel de fournisseurs IA — JARVIS v3.0
Modèles réels et vérifiés uniquement.
"""
import os
import json
import requests

PROVIDERS = {
    # ---- GOOGLE GEMINI (modèles réels) ----
    "gemini-2.0-flash": {
        "name": "Gemini 2.0 Flash (Défaut)",
        "model": "gemini-2.0-flash-exp",
        "type": "gemini",
        "env_key": "GEMINI_API_KEY",
        "or_model": "google/gemini-2.0-flash-exp:free",
        "category": "Google (Gemini)",
        "free": True,
        "vision": True,
    },
    "gemini-1.5-flash": {
        "name": "Gemini 1.5 Flash (Gratuit)",
        "model": "gemini-1.5-flash",
        "type": "gemini",
        "env_key": "GEMINI_API_KEY",
        "or_model": "google/gemini-flash-1.5",
        "category": "Google (Gemini)",
        "free": True,
        "vision": True,
    },
    "gemini-1.5-pro": {
        "name": "Gemini 1.5 Pro",
        "model": "gemini-1.5-pro",
        "type": "gemini",
        "env_key": "GEMINI_API_KEY",
        "or_model": "google/gemini-pro-1.5",
        "category": "Google (Gemini)",
        "free": False,
        "vision": True,
    },
    "gemini-2.5-pro": {
        "name": "Gemini 2.5 Pro (Meilleur)",
        "model": "gemini-2.5-pro-preview-06-05",
        "type": "gemini",
        "env_key": "GEMINI_API_KEY",
        "or_model": "google/gemini-2.5-pro-preview",
        "category": "Google (Gemini)",
        "free": False,
        "vision": True,
    },
    "gemini-2.5-flash": {
        "name": "Gemini 2.5 Flash",
        "model": "gemini-2.5-flash-preview-05-20",
        "type": "gemini",
        "env_key": "GEMINI_API_KEY",
        "or_model": "google/gemini-2.5-flash-preview",
        "category": "Google (Gemini)",
        "free": True,
        "vision": True,
    },

    # ---- GROQ (ultra-rapide, gratuit) ----
    "groq-llama4": {
        "name": "Llama 4 Scout via Groq GRATUIT",
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "type": "openai_compat",
        "env_key": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "or_model": "meta-llama/llama-4-scout",
        "category": "Meta (Llama via Groq)",
        "free": True,
        "vision": False,
    },
    "groq-llama3": {
        "name": "Llama 3.1 8B via Groq GRATUIT",
        "model": "llama-3.1-8b-instant",
        "type": "openai_compat",
        "env_key": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "or_model": "meta-llama/llama-3.1-8b-instruct:free",
        "category": "Meta (Llama via Groq)",
        "free": True,
        "vision": False,
    },
    "groq-llama3-70b": {
        "name": "Llama 3.3 70B via Groq GRATUIT",
        "model": "llama-3.3-70b-versatile",
        "type": "openai_compat",
        "env_key": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "or_model": "meta-llama/llama-3.3-70b-instruct",
        "category": "Meta (Llama via Groq)",
        "free": True,
        "vision": False,
    },

    # ---- ANTHROPIC (Claude) ----
    "claude-sonnet": {
        "name": "Claude Sonnet 4.6",
        "model": "claude-sonnet-4-5",
        "type": "anthropic",
        "env_key": "ANTHROPIC_API_KEY",
        "or_model": "anthropic/claude-sonnet-4-5",
        "category": "Anthropic (Claude)",
        "free": False,
        "vision": True,
    },
    "claude-haiku": {
        "name": "Claude Haiku 4.5 (Rapide)",
        "model": "claude-haiku-4-5-20251001",
        "type": "anthropic",
        "env_key": "ANTHROPIC_API_KEY",
        "or_model": "anthropic/claude-haiku-4-5",
        "category": "Anthropic (Claude)",
        "free": False,
        "vision": True,
    },
    "claude-opus": {
        "name": "Claude Opus 4.6 (Meilleur)",
        "model": "claude-opus-4-6",
        "type": "anthropic",
        "env_key": "ANTHROPIC_API_KEY",
        "or_model": "anthropic/claude-opus-4-6",
        "category": "Anthropic (Claude)",
        "free": False,
        "vision": True,
    },

    # ---- OPENAI ----
    "gpt-4o": {
        "name": "GPT-4o",
        "model": "gpt-4o",
        "type": "openai_compat",
        "env_key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "or_model": "openai/gpt-4o",
        "category": "OpenAI (GPT)",
        "free": False,
        "vision": True,
    },
    "gpt-4o-mini": {
        "name": "GPT-4o Mini (Economique)",
        "model": "gpt-4o-mini",
        "type": "openai_compat",
        "env_key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "or_model": "openai/gpt-4o-mini",
        "category": "OpenAI (GPT)",
        "free": False,
        "vision": True,
    },
    "gpt-o3-mini": {
        "name": "GPT o3-mini (Raisonnement)",
        "model": "o3-mini",
        "type": "openai_compat",
        "env_key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "or_model": "openai/o3-mini",
        "category": "OpenAI (GPT)",
        "free": False,
        "vision": False,
    },

    # ---- xAI Grok ----
    "grok-3": {
        "name": "Grok 3",
        "model": "grok-3",
        "type": "openai_compat",
        "env_key": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
        "or_model": "x-ai/grok-3",
        "category": "xAI (Grok)",
        "free": False,
        "vision": True,
    },

    # ---- MISTRAL (gratuit) ----
    "mistral-free": {
        "name": "Mistral Small GRATUIT",
        "model": "mistral-small-latest",
        "type": "openai_compat",
        "env_key": "MISTRAL_API_KEY",
        "base_url": "https://api.mistral.ai/v1",
        "or_model": "mistralai/mistral-small-3.1-24b-instruct:free",
        "category": "Mistral",
        "free": True,
        "vision": False,
    },

    # ---- DEEPSEEK ----
    "deepseek-v3": {
        "name": "DeepSeek V3 (Très bon/prix)",
        "model": "deepseek-chat",
        "type": "openai_compat",
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1",
        "or_model": "deepseek/deepseek-chat-v3-0324",
        "category": "DeepSeek",
        "free": False,
        "vision": False,
    },
    "deepseek-r1": {
        "name": "DeepSeek R1 (Raisonnement)",
        "model": "deepseek-reasoner",
        "type": "openai_compat",
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1",
        "or_model": "deepseek/deepseek-r1",
        "category": "DeepSeek",
        "free": False,
        "vision": False,
    },

    # ---- OPENROUTER (accès universel) ----
    "openrouter-auto": {
        "name": "OpenRouter Auto (Meilleur dispo)",
        "model": "openrouter/auto",
        "type": "openrouter",
        "env_key": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "or_model": "openrouter/auto",
        "category": "OpenRouter",
        "free": False,
        "vision": True,
    },
    "or-llama-free": {
        "name": "Llama 4 Scout via OpenRouter GRATUIT",
        "model": "meta-llama/llama-4-scout:free",
        "type": "openrouter",
        "env_key": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "or_model": "meta-llama/llama-4-scout:free",
        "category": "OpenRouter (Gratuit)",
        "free": True,
        "vision": True,
    },
    "or-deepseek-free": {
        "name": "DeepSeek R1 via OpenRouter GRATUIT",
        "model": "deepseek/deepseek-r1:free",
        "type": "openrouter",
        "env_key": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "or_model": "deepseek/deepseek-r1:free",
        "category": "OpenRouter (Gratuit)",
        "free": True,
        "vision": False,
    },
    "or-qwen-free": {
        "name": "Qwen2.5 VL via OpenRouter GRATUIT",
        "model": "qwen/qwen2.5-vl-32b-instruct:free",
        "type": "openrouter",
        "env_key": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "or_model": "qwen/qwen2.5-vl-32b-instruct:free",
        "category": "OpenRouter (Gratuit)",
        "free": True,
        "vision": True,
    },

    # ---- LOCAL Ollama ----
    "ollama-auto": {
        "name": "Ollama Local (Auto-detect)",
        "model": "AUTO",
        "type": "ollama",
        "env_key": None,
        "category": "Local (Ollama)",
        "free": True,
        "vision": True,
    },
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
        self.response_cache = {}
        provider_id = os.environ.get('AI_PROVIDER', 'gemini-2.0-flash')
        self.set_provider(provider_id)

    def set_provider(self, provider_id: str):
        if provider_id not in PROVIDERS:
            provider_id = 'gemini-2.0-flash'
        self.current = PROVIDERS[provider_id]
        self.provider_id = provider_id
        print(f"[JARVIS] Provider: {self.current['name']}")

    def get_available_providers(self):
        available = []
        for pid, p in PROVIDERS.items():
            has_key = True
            if p['env_key']:
                has_key = bool(os.environ.get(p['env_key']))
            if p['type'] == 'ollama':
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
                "vision": p.get("vision", False),
                "category": p.get("category", "Autre")
            })
        return available

    def get_ollama_models(self):
        try:
            r = requests.get('http://localhost:11434/api/tags', timeout=3)
            models = r.json().get('models', [])
            return [m['name'] for m in models]
        except:
            return []

    def _get_cache_key(self, messages, image_b64):
        if not messages:
            return None
        last = messages[-1].get('content', '')
        if image_b64:
            return None  # Pas de cache pour les images
        return f"{self.provider_id}:{last[:100]}"

    def chat(self, messages: list, image_b64: str = None) -> str:
        cache_key = self._get_cache_key(messages, image_b64)
        if cache_key and cache_key in self.response_cache:
            return self.response_cache[cache_key]

        p = self.current
        ptype = p['type']
        result = None
        try:
            if ptype == 'gemini':
                result = self._chat_gemini(messages, image_b64)
            elif ptype in ('openai_compat', 'openrouter'):
                result = self._chat_openai_compat(messages, image_b64)
            elif ptype == 'anthropic':
                result = self._chat_anthropic(messages, image_b64)
            elif ptype == 'ollama':
                result = self._chat_ollama(messages, image_b64)
            else:
                result = self._chat_gemini(messages, image_b64)
        except Exception as e:
            print(f"[Provider] Erreur {ptype}: {e}")
            # Fallback automatique sur gemini-1.5-flash
            try:
                print("[Provider] Fallback sur gemini-1.5-flash...")
                old = self.provider_id
                self.set_provider('gemini-1.5-flash')
                result = self._chat_gemini(messages, image_b64)
                self.set_provider(old)
            except Exception as e2:
                result = f"Erreur IA: {str(e2)}"

        if result and cache_key:
            self.response_cache[cache_key] = result
            if len(self.response_cache) > 100:
                oldest = list(self.response_cache.keys())[0]
                del self.response_cache[oldest]

        return result or "Je n'ai pas pu générer de réponse."

    def _chat_gemini(self, messages, image_b64=None):
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return "Configure ta clé GEMINI_API_KEY dans .env (gratuit sur aistudio.google.com)"
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        # Utilise toujours gemini-1.5-flash comme fallback sûr
        model_name = self.current.get('model', 'gemini-1.5-flash')
        try:
            model = genai.GenerativeModel(model_name)
        except Exception:
            model = genai.GenerativeModel('gemini-1.5-flash')

        parts = [SYSTEM_PROMPT]
        for m in messages:
            parts.append(f"{'User' if m['role']=='user' else 'JARVIS'}: {m['content']}")
        if image_b64:
            parts.append({"mime_type": "image/jpeg", "data": image_b64})
        try:
            r = model.generate_content(parts)
            return r.text
        except Exception as e:
            # Si le modèle n'existe pas, retry avec gemini-1.5-flash
            if 'not found' in str(e).lower() or '404' in str(e):
                model = genai.GenerativeModel('gemini-1.5-flash')
                r = model.generate_content(parts)
                return r.text
            raise

    def _chat_openai_compat(self, messages, image_b64=None):
        p = self.current
        api_key = os.environ.get(p['env_key'], '') if p['env_key'] else ''

        # Fallback OpenRouter si pas de clé native
        if not api_key and os.environ.get('OPENROUTER_API_KEY') and p.get('or_model'):
            base_url = "https://openrouter.ai/api/v1"
            api_key = os.environ['OPENROUTER_API_KEY']
            model = p['or_model']
            extra_headers = {
                "HTTP-Referer": "https://github.com/anonyme-afk/Jarvis-Desktop",
                "X-Title": "JARVIS Desktop"
            }
        else:
            base_url = p.get('base_url', 'https://api.openai.com/v1')
            model = p['model']
            extra_headers = {}

        if not api_key:
            return f"Clé API manquante pour {p['name']}. Configure dans .env"

        msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
        for m in messages[:-1]:
            msgs.append({"role": m['role'], "content": m['content']})

        last = messages[-1]
        if image_b64 and p.get('vision'):
            content = [
                {"type": "text", "text": last['content']},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        else:
            content = last['content']
        msgs.append({"role": "user", "content": content})

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            **extra_headers
        }
        r = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={"model": model, "messages": msgs, "max_tokens": 500},
            timeout=30
        )
        r.raise_for_status()
        return r.json()['choices'][0]['message']['content']

    def _chat_anthropic(self, messages, image_b64=None):
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            # Fallback OpenRouter
            if os.environ.get('OPENROUTER_API_KEY') and self.current.get('or_model'):
                old_type = self.current['type']
                self.current['type'] = 'openrouter'
                self.current['base_url'] = 'https://openrouter.ai/api/v1'
                self.current['env_key'] = 'OPENROUTER_API_KEY'
                result = self._chat_openai_compat(messages, image_b64)
                self.current['type'] = old_type
                return result
            return "Clé ANTHROPIC_API_KEY manquante dans .env"
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            msgs = []
            for m in messages:
                if image_b64 and m == messages[-1] and self.current.get('vision'):
                    msgs.append({"role": "user", "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}},
                        {"type": "text", "text": m['content']}
                    ]})
                else:
                    msgs.append({"role": m['role'], "content": m['content']})
            r = client.messages.create(
                model=self.current['model'],
                max_tokens=500,
                system=SYSTEM_PROMPT,
                messages=msgs
            )
            return r.content[0].text
        except ImportError:
            return "pip install anthropic requis"

    def _chat_ollama(self, messages, image_b64=None):
        model = os.environ.get('OLLAMA_MODEL', 'AUTO')
        if model == 'AUTO':
            installed = self.get_ollama_models()
            priority = ['llama4', 'llava', 'llama3.2', 'llama3.1', 'mistral', 'qwen', 'gemma', 'phi3', 'tinyllama']
            model = 'llama3.2'
            for p in priority:
                found = next((m for m in installed if p in m.lower()), None)
                if found:
                    model = found
                    break
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + \
               [{"role": m['role'], "content": m['content']} for m in messages]
        payload = {"model": model, "messages": msgs, "stream": False}
        if image_b64 and 'llava' in model.lower():
            payload['images'] = [image_b64]
        r = requests.post('http://localhost:11434/api/chat', json=payload, timeout=60)
        return r.json()['message']['content']


ai = AIProvider()
