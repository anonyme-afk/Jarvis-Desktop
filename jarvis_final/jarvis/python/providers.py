"""
Gestionnaire universel de fournisseurs IA.
"""
import os
import json
import requests

# ===== REGISTRE DES PROVIDERS PAR GROUPES ET CATÉGORIES =====
PROVIDERS = {
    # ---- GOOGLE GEMINI ----
    "gemini-3.5-flash": {
        "name": "Gemini 3.5 Flash (Défaut)",
        "model": "gemini-3.5-flash",
        "type": "gemini",
        "env_key": "GEMINI_API_KEY",
        "or_model": "google/gemini-2.5-flash",
        "category": "Google (Gemini)",
        "free": True,
        "vision": True,
    },
    "gemini-3.1-pro-preview": {
        "name": "Gemini 3.1 Pro (Preview)",
        "model": "gemini-3.1-pro-preview",
        "type": "gemini",
        "env_key": "GEMINI_API_KEY",
        "or_model": "google/gemini-2.5-pro",
        "category": "Google (Gemini)",
        "free": False,
        "vision": True,
    },
    "gemini-3.1-flash-lite": {
        "name": "Gemini 3.1 Flash Lite",
        "model": "gemini-1.5-flash-lite",
        "type": "gemini",
        "env_key": "GEMINI_API_KEY",
        "or_model": "google/gemini-2.5-flash:free",
        "category": "Google (Gemini)",
        "free": True,
        "vision": True,
    },
    "gemini-3-flash-preview": {
        "name": "Gemini 3 Flash Preview",
        "model": "gemini-3-flash-preview",
        "type": "gemini",
        "env_key": "GEMINI_API_KEY",
        "or_model": "google/gemini-2.5-flash",
        "category": "Google (Gemini)",
        "free": True,
        "vision": True,
    },
    "gemini-pro-latest": {
        "name": "Gemini Pro Latest",
        "model": "gemini-1.5-pro",
        "type": "gemini",
        "env_key": "GEMINI_API_KEY",
        "or_model": "google/gemini-2.5-pro",
        "category": "Google (Gemini)",
        "free": False,
        "vision": True,
    },
    "gemini-flash-latest": {
        "name": "Gemini Flash Latest",
        "model": "gemini-1.5-flash",
        "type": "gemini",
        "env_key": "GEMINI_API_KEY",
        "or_model": "google/gemini-2.5-flash",
        "category": "Google (Gemini)",
        "free": True,
        "vision": True,
    },
    "gemini-3-flash": {
        "name": "Gemini 3 Flash",
        "model": "gemini-3-flash",
        "type": "gemini",
        "env_key": "GEMINI_API_KEY",
        "or_model": "google/gemini-2.5-flash",
        "category": "Google (Gemini)",
        "free": True,
        "vision": True,
    },
    "gemini-2.5-pro": {
        "name": "Gemini 2.5 Pro",
        "model": "gemini-2.5-pro",
        "type": "gemini",
        "env_key": "GEMINI_API_KEY",
        "or_model": "google/gemini-2.5-pro",
        "category": "Google (Gemini)",
        "free": False,
        "vision": True,
    },
    "gemini-2.5-flash": {
        "name": "Gemini 2.5 Flash",
        "model": "gemini-2.5-flash",
        "type": "gemini",
        "env_key": "GEMINI_API_KEY",
        "or_model": "google/gemini-2.5-flash",
        "category": "Google (Gemini)",
        "free": True,
        "vision": True,
    },

    # ---- OPENAI GPT ----
    "gpt-5.5": {
        "name": "GPT-5.5 (Prochainement / Auto-OR)",
        "model": "gpt-5.5",
        "type": "openai_compat",
        "env_key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "or_model": "openai/gpt-4o",  # Fallback
        "category": "OpenAI (GPT)",
        "free": False,
        "vision": True,
    },
    "gpt-5.4-pro": {
        "name": "GPT-5.4 Pro (Auto-OR)",
        "model": "gpt-5.4-pro",
        "type": "openai_compat",
        "env_key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "or_model": "openai/gpt-4o",
        "category": "OpenAI (GPT)",
        "free": False,
        "vision": True,
    },
    "gpt-5.2": {
        "name": "GPT-5.2 (Auto-OR)",
        "model": "gpt-5.2",
        "type": "openai_compat",
        "env_key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "or_model": "openai/gpt-4o",
        "category": "OpenAI (GPT)",
        "free": False,
        "vision": True,
    },
    "gpt-4.5": {
        "name": "GPT-4.5",
        "model": "gpt-4.5-preview",
        "type": "openai_compat",
        "env_key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "or_model": "openai/gpt-4.5-preview",
        "category": "OpenAI (GPT)",
        "free": False,
        "vision": True,
    },
    "gpt-o3": {
        "name": "GPT-o3 Reasoning",
        "model": "o3-mini",
        "type": "openai_compat",
        "env_key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "or_model": "openai/o3-mini",
        "category": "OpenAI (GPT)",
        "free": False,
        "vision": True,
    },
    "gpt-o3-mini": {
        "name": "GPT-o3-mini",
        "model": "o3-mini",
        "type": "openai_compat",
        "env_key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "or_model": "openai/o3-mini",
        "category": "OpenAI (GPT)",
        "free": False,
        "vision": True,
    },
    "gpt-o1": {
        "name": "GPT-o1",
        "model": "o1",
        "type": "openai_compat",
        "env_key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "or_model": "openai/o1",
        "category": "OpenAI (GPT)",
        "free": False,
        "vision": True,
    },
    "gpt-4.1-mini": {
        "name": "GPT-4.1-mini",
        "model": "gpt-4o-mini",
        "type": "openai_compat",
        "env_key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "or_model": "openai/gpt-4o-mini",
        "category": "OpenAI (GPT)",
        "free": False,
        "vision": True,
    },
    "gpt-4.1-nano": {
        "name": "GPT-4.1-nano (Auto-OR)",
        "model": "gpt-4o-mini",
        "type": "openai_compat",
        "env_key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "or_model": "openai/gpt-4o-mini",
        "category": "OpenAI (GPT)",
        "free": False,
        "vision": True,
    },

    # ---- ANTHROPIC CLAUDE ----
    "claude-4.6-opus": {
        "name": "Claude 4.6 Opus (Auto-OR)",
        "model": "claude-3-opus-20240229",
        "type": "anthropic",
        "env_key": "ANTHROPIC_API_KEY",
        "or_model": "anthropic/claude-3-opus",
        "category": "Anthropic (Claude)",
        "free": False,
        "vision": True,
    },
    "claude-4.6-sonnet": {
        "name": "Claude 4.6 Sonnet (Auto-OR)",
        "model": "claude-3-7-sonnet-20250219",
        "type": "anthropic",
        "env_key": "ANTHROPIC_API_KEY",
        "or_model": "anthropic/claude-3.7-sonnet",
        "category": "Anthropic (Claude)",
        "free": False,
        "vision": True,
    },
    "claude-4.5-haiku": {
        "name": "Claude 4.5 Haiku (Auto-OR)",
        "model": "claude-3-5-haiku-20241022",
        "type": "anthropic",
        "env_key": "ANTHROPIC_API_KEY",
        "or_model": "anthropic/claude-3.5-haiku",
        "category": "Anthropic (Claude)",
        "free": False,
        "vision": False,
    },
    "claude-3.7-sonnet": {
        "name": "Claude 3.7 Sonnet",
        "model": "claude-3-7-sonnet-20250219",
        "type": "anthropic",
        "env_key": "ANTHROPIC_API_KEY",
        "or_model": "anthropic/claude-3.7-sonnet",
        "category": "Anthropic (Claude)",
        "free": False,
        "vision": True,
    },

    # ---- META LLAMA ----
    "llama-4-scout": {
        "name": "Llama 4 Scout (Auto-OR)",
        "model": "llama-4-scout",
        "type": "openai_compat",
        "env_key": "META_API_KEY",
        "or_model": "meta-llama/llama-3.3-70b-instruct",
        "category": "Meta (Llama)",
        "free": True,
        "vision": True,
    },
    "llama-4-maverick": {
        "name": "Llama 4 Maverick (Auto-OR)",
        "model": "llama-4-maverick",
        "type": "openai_compat",
        "env_key": "META_API_KEY",
        "or_model": "meta-llama/llama-3.3-70b-instruct",
        "category": "Meta (Llama)",
        "free": True,
        "vision": True,
    },
    "llama-3.2-vision": {
        "name": "Llama 3.2 Vision",
        "model": "llama-3.2-11b-vision-instruct",
        "type": "openai_compat",
        "env_key": "META_API_KEY",
        "or_model": "meta-llama/llama-3.2-11b-vision-instruct",
        "category": "Meta (Llama)",
        "free": True,
        "vision": True,
    },

    # ---- xAI GROK ----
    "grok-4.1-fast-reasoning": {
        "name": "Grok 4.1 Fast Reasoning",
        "model": "grok-2-1212",
        "type": "openai_compat",
        "env_key": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
        "or_model": "x-ai/grok-2",
        "category": "xAI (Grok)",
        "free": False,
        "vision": True,
    },
    "grok-4": {
        "name": "Grok 4 (Auto-OR)",
        "model": "grok-2",
        "type": "openai_compat",
        "env_key": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
        "or_model": "x-ai/grok-2",
        "category": "xAI (Grok)",
        "free": False,
        "vision": True,
    },
    "grok-3": {
        "name": "Grok 3 (Auto-OR)",
        "model": "grok-2",
        "type": "openai_compat",
        "env_key": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
        "or_model": "x-ai/grok-2",
        "category": "xAI (Grok)",
        "free": False,
        "vision": True,
    },

    # ---- ÉCOSYSTÈME OPEN-SOURCE & PORTES D'ASIE ----
    "qwen2.5-vl-32b-instruct": {
        "name": "Qwen2.5-VL-32B-Instruct",
        "model": "qwen2.5-vl-32b-instruct",
        "type": "openai_compat",
        "env_key": "QWEN_API_KEY",
        "or_model": "qwen/qwen-2.5-coder-32b-instruct",
        "category": "Open-Source & Asiatiques",
        "free": True,
        "vision": True,
    },
    "qwen-vl-max": {
        "name": "Qwen-VL Max",
        "model": "qwen-vl-max",
        "type": "openai_compat",
        "env_key": "QWEN_API_KEY",
        "or_model": "qwen/qwen-2.5-72b-instruct",
        "category": "Open-Source & Asiatiques",
        "free": False,
        "vision": True,
    },
    "deepseek-v3.2": {
        "name": "DeepSeek-V3.2",
        "model": "deepseek-chat",
        "type": "openai_compat",
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1",
        "or_model": "deepseek/deepseek-chat",
        "category": "Open-Source & Asiatiques",
        "free": False,
        "vision": False,
    },
    "deepseek-r1": {
        "name": "DeepSeek-R1 (Raisonnement)",
        "model": "deepseek-reasoner",
        "type": "openai_compat",
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1",
        "or_model": "deepseek/deepseek-r1",
        "category": "Open-Source & Asiatiques",
        "free": False,
        "vision": False,
    },
    "deepseek-ocr-2": {
        "name": "DeepSeek-OCR 2 (Auto-OR)",
        "model": "deepseek-chat",
        "type": "openai_compat",
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1",
        "or_model": "deepseek/deepseek-chat",
        "category": "Open-Source & Asiatiques",
        "free": False,
        "vision": False,
    },
    "glm-4.5v": {
        "name": "GLM-4.5V (Auto-OR)",
        "model": "glm-4v",
        "type": "openai_compat",
        "env_key": "ZHIPU_API_KEY",
        "or_model": "google/gemini-2.5-pro",
        "category": "Open-Source & Asiatiques",
        "free": False,
        "vision": True,
    },
    "glm-4.1v-9b-thinking": {
        "name": "GLM-4.1V-9B-Thinking",
        "model": "glm-4v-9b",
        "type": "openai_compat",
        "env_key": "ZHIPU_API_KEY",
        "or_model": "google/gemini-2.5-flash",
        "category": "Open-Source & Asiatiques",
        "free": True,
        "vision": True,
    },
    "kimi-k2-thinking": {
        "name": "Kimi-K2 Thinking (Auto-OR)",
        "model": "kimi-k2.5",
        "type": "openai_compat",
        "env_key": "MOONSHOT_API_KEY",
        "or_model": "deepseek/deepseek-chat",
        "category": "Open-Source & Asiatiques",
        "free": False,
        "vision": False,
    },

    # ---- MICROSOFT ----
    "phi-4-multimodal": {
        "name": "Phi-4 Multimodal",
        "model": "phi-4-multimodal",
        "type": "openai_compat",
        "env_key": "MICROSOFT_API_KEY",
        "or_model": "microsoft/phi-4",
        "category": "Microsoft",
        "free": True,
        "vision": True,
    },

    # ---- CONNECTEURS ET LOCAL ----
    "openrouter-generic": {
        "name": "OpenRouter Auto-Routeur",
        "model": "google/gemini-2.5-flash",
        "type": "openrouter",
        "env_key": "OPENROUTER_API_KEY",
        "or_model": "google/gemini-2.5-flash",
        "category": "OpenRouter Connecteur",
        "free": True,
        "vision": True,
        "url": "https://openrouter.ai"
    },
    "ollama-auto": {
        "name": "Ollama (Modèle Auto)",
        "model": "AUTO",
        "type": "ollama",
        "env_key": None,
        "category": "Ollama (Moteur Local)",
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
        self.response_cache = {}
        self._cache_keys = []
        # Charger le provider actif depuis .env ou défaut
        provider_id = os.environ.get('AI_PROVIDER', 'gemini-3.5-flash')
        self.set_provider(provider_id)

    def _get_cache_key(self, messages, image_b64):
        # On hash de manière basique la requête
        msg_str = json.dumps(messages, sort_keys=True)
        img_prefix = image_b64[:30] if image_b64 else ""
        return f"{self.current['model']}_{msg_str}_{img_prefix}"

    def chat(self, messages: list, image_b64: str = None) -> str:
        cache_key = self._get_cache_key(messages, image_b64)
        if cache_key in self.response_cache:
            return self.response_cache[cache_key]

        err = None
        # Essai 1
        try:
            res = self._do_chat(messages, image_b64)
            self._save_cache(cache_key, res)
            return res
        except Exception as e:
            err = e
            print(f"[JARVIS] Erreur IA (Essai 1): {e}")
        
        # Essai 2 (Retry)
        try:
            res = self._do_chat(messages, image_b64)
            self._save_cache(cache_key, res)
            return res
        except Exception as e:
            print(f"[JARVIS] Erreur IA (Essai 2): {e}")

        # Fallback automatique
        if self.provider_id != "gemini-3.5-flash":
            print("[JARVIS] Bascule automatique sur gemini-3.5-flash suite aux erreurs.")
            self.set_provider("gemini-3.5-flash")
            try:
                res = self._do_chat(messages, image_b64)
                self._save_cache(cache_key, res)
                return res
            except Exception as e:
                return f"Erreur critique IA (Fallback Gemini échoué): {e}"
        return f"Erreur critique IA: {err}"

    def _save_cache(self, key, value):
        self.response_cache[key] = value
        self._cache_keys.append(key)
        if len(self._cache_keys) > 200:
            oldest_key = self._cache_keys.pop(0)
            if oldest_key in self.response_cache:
                del self.response_cache[oldest_key]

    def chat_stream(self, messages: list, image_b64: str = None):
        pass

    def set_provider(self, provider_id: str):
        if provider_id not in PROVIDERS:
            provider_id = 'gemini-3.5-flash'
        self.current = PROVIDERS[provider_id]
        self.provider_id = provider_id
        print(f"[JARVIS] Provider actif: {self.current['name']}")

    def get_available_providers(self):
        """Retourne les providers dont la clé API est configurée (niveaux natif ou OpenRouter)"""
        available = []
        or_key_present = bool(os.environ.get('OPENROUTER_API_KEY'))
        for pid, p in PROVIDERS.items():
            has_key = False
            # Check native key
            if p['env_key'] and os.environ.get(p['env_key']):
                has_key = True
            # Or if OpenRouter key is present and model has an OpenRouter mapping
            elif or_key_present and p.get('or_model'):
                has_key = True
                
            if p['type'] == 'openrouter':
                has_key = or_key_present
                
            if p['type'] == 'ollama':
                try:
                    r = requests.get('http://localhost:11434/api/tags', timeout=1)
                    has_key = r.status_code == 200
                except:
                    has_key = False
                    
            available.append({
                "id": pid,
                "name": p["name"],
                "category": p.get("category", "Autres"),
                "free": p.get("free", False),
                "available": has_key,
                "vision": p.get("vision", False)
            })
        return available

    def get_ollama_models(self):
        try:
            r = requests.get('http://localhost:11434/api/tags', timeout=2)
            models = r.json().get('models', [])
            return [m['name'] for m in models]
        except:
            return []

    def _do_chat(self, messages: list, image_b64: str = None) -> str:
        p = self.current
        ptype = p['type']

        # Routage automatique vers OpenRouter si la clé native est absente mais que OpenRouter est configurée
        native_key_present = bool(os.environ.get(p['env_key'])) if p.get('env_key') else False
        or_key_present = bool(os.environ.get('OPENROUTER_API_KEY'))

        if (not native_key_present and or_key_present and p.get('or_model')) or ptype == 'openrouter':
            return self._chat_openrouter(messages, image_b64)

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

    def _chat_openrouter(self, messages, image_b64=None):
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            return "Veuillez configurer OPENROUTER_API_KEY dans votre fichier .env"
        
        p = self.current
        # Déterminer le modèle à appeler sur OpenRouter
        or_model = p.get('or_model', 'google/gemini-2.5-flash')
        
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
            "HTTP-Referer": "https://github.com/anonyme-afk/Jarvis-Desktop",
            "X-Title": "JARVIS Desktop"
        }
        
        payload = {
            "model": or_model,
            "messages": msgs,
            "max_tokens": 500
        }
        
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        if r.status_code != 200:
            return f"Erreur OpenRouter (Code {r.status_code}) : {r.text}"
            
        res_json = r.json()
        if "choices" in res_json and len(res_json["choices"]) > 0:
            return res_json["choices"][0]["message"]["content"]
        else:
            return f"Réponse inattendue d'OpenRouter : {json.dumps(res_json)}"

    def _chat_gemini(self, messages, image_b64=None):
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return "Configure ta clé API dans .env"
        import google.generativeai as genai
        genai.configure(api_key=api_key)
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
        model = os.environ.get('OLLAMA_MODEL', 'AUTO')
        if model == 'AUTO':
            installed = self.get_ollama_models()
            priority = ['llava','llama3.2','llama3.1','mistral','qwen','gemma','phi3','tinyllama']
            model = 'llama3.2'
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
