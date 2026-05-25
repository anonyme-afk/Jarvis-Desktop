# openrouter_client.py
import json
import os
import sys
from pathlib import Path
import requests

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
CONFIG_FILE = BASE_DIR / "config" / "api_keys.json"

class OpenRouterClient:
    def __init__(self):
        self.api_key = self._load_key()
        self.base_url = "https://openrouter.ai/api/v1"

    def _load_key(self) -> str:
        # 1. Try to load from api_keys.json
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                key = data.get("openrouter_api_key")
                if key and key.strip():
                    return key.strip()
            except Exception as e:
                print(f"[OpenRouter] Exception reading api_keys.json: {e}")
        
        # 2. Try environment variables
        env_key = os.getenv("OPENROUTER_API_KEY")
        if env_key and env_key.strip():
            return env_key.strip()
            
        print("[OpenRouter] WARNING: No openrouter_api_key found in api_keys.json or environment!")
        return ""

    def generate_chat_completion(self, model: str, messages: list, system_prompt: str = None, temperature: float = 0.7, max_tokens: int = 2500) -> str:
        """
        Calls OpenRouter Chat Completions endpoint.
        """
        if not self.api_key:
            raise ValueError("OpenRouter API key is missing.")
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ai.studio/build",
            "X-Title": "JARVIS WebHUD",
        }
        
        payload = {
            "model": model,
            "messages": [],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if system_prompt:
            payload["messages"].append({"role": "system", "content": system_prompt})
            
        payload["messages"].extend(messages)
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            res_data = response.json()
            if "choices" in res_data and len(res_data["choices"]) > 0:
                reply = res_data["choices"][0]["message"]["content"]
                return reply.strip()
            else:
                raise ValueError(f"Unexpected response format from OpenRouter: {res_data}")
        except Exception as e:
            print(f"[OpenRouter] API Error calling {model}: {e}")
            raise e

def _gemini_fallback(prompt: str, system_instruction: str = None) -> str:
    print("[Fallback] Falling back to standard Gemini...")
    gemini_key = ""
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            gemini_key = data.get("gemini_api_key", "")
        except Exception:
            pass
    if not gemini_key:
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        
    if not gemini_key:
        raise ValueError("Cannot fall back to Gemini: No gemini_api_key found in config or environment.")
        
    # Standard modern google-genai SDK fallback
    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)
        config_dict = {}
        if system_instruction:
            config_dict["system_instruction"] = system_instruction
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config_dict if config_dict else None
        )
        return response.text.strip()
    except Exception as e:
        print(f"[Fallback] Modern Google GenAI SDK fallback failed: {e}. Trying legacy...")
        try:
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=gemini_key)
            # In legacy, system_instruction can be passed in constructor
            if system_instruction:
                model = genai_legacy.GenerativeModel(
                    "gemini-1.5-flash",
                    system_instruction=system_instruction
                )
            else:
                model = genai_legacy.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e2:
            print(f"[Fallback] Legacy GenAI SDK fallback failed: {e2}")
            raise e2

FREE_MODELS = [
    "deepseek/deepseek-v4-flash:free",
    "minimax/minimax-m2.5:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "openai/gpt-oss-120b:free"
]

def generate_completion(
    prompt: str,
    system_prompt: str = None,
    model: str = "deepseek/deepseek-v4-flash:free",
    temperature: float = 0.7,
    max_tokens: int = 2500
) -> str:
    """
    Utility function that actions can import to do text/reasoning generation.
    Tries the configured model via OpenRouter first. If it fails, tries other
    pre-configured free OpenRouter models before finally falling back to Gemini
    to prevent exhausting Google AI Studio quota.
    """
    client = OpenRouterClient()
    
    # Identify which models to try. We start with the requested model,
    # and then chain the other free models to maximize successful completion.
    models_to_try = [model]
    for fm in FREE_MODELS:
        if fm not in models_to_try:
            models_to_try.append(fm)
            
    # If the client cannot find an API key, we skip OpenRouter completely and fallback
    if not client.api_key:
        print("[OpenRouter client] No OpenRouter API key found. Falling back to Gemini.")
        full_prompt = f"System prompt: {system_prompt}\n\nUser prompt: {prompt}" if system_prompt else prompt
        return _gemini_fallback(full_prompt, system_prompt)

    messages = [{"role": "user", "content": prompt}]
    
    last_err = None
    for attempt_model in models_to_try:
        try:
            print(f"[OpenRouter client] Attempting generation with model: {attempt_model}")
            return client.generate_chat_completion(
                model=attempt_model,
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except Exception as e:
            last_err = e
            print(f"[OpenRouter client] Model {attempt_model} failed: {e}. Trying next free model...")
            continue
            
    print(f"[OpenRouter client] All OpenRouter free models failed. Last error: {last_err}. Initiating fallback to Gemini.")
    full_prompt = f"System prompt: {system_prompt}\n\nUser prompt: {prompt}" if system_prompt else prompt
    return _gemini_fallback(full_prompt, system_prompt)

