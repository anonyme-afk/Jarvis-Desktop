import json
from datetime import datetime
from threading import Lock
from pathlib import Path
import sys


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR         = get_base_dir()
MEMORY_PATH      = BASE_DIR / "memory" / "long_term.json"
_lock            = Lock()
MAX_VALUE_LENGTH = 380
MEMORY_MAX_CHARS = 2200

def _empty_memory() -> dict:
    return {
        "identity":      {},
        "preferences":   {},
        "projects":      {},
        "relationships": {},
        "wishes":        {},
        "notes":         {},
    }

def load_memory() -> dict:
    if not MEMORY_PATH.exists():
        return _empty_memory()
    with _lock:
        try:
            data = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                base = _empty_memory()
                for key in base:
                    if key not in data:
                        data[key] = {}
                return data
            return _empty_memory()
        except Exception as e:
            print(f"[Memory] ⚠️ Load error: {e}")
            return _empty_memory()

def _all_entries(memory: dict) -> list[tuple]:
    entries = []
    for cat, items in memory.items():
        if not isinstance(items, dict):
            continue
        for key, entry in items.items():
            if isinstance(entry, dict) and "value" in entry:
                entries.append((cat, key, entry))
    return entries


def _trim_to_limit(memory: dict) -> dict:
    if len(json.dumps(memory, ensure_ascii=False)) <= MEMORY_MAX_CHARS:
        return memory
    entries = _all_entries(memory)
    entries.sort(key=lambda t: t[2].get("updated", "0000-00-00"))
    for cat, key, _ in entries:
        if len(json.dumps(memory, ensure_ascii=False)) <= MEMORY_MAX_CHARS:
            break
        del memory[cat][key]
        print(f"[Memory] 🗑️  Trimmed {cat}/{key}")
    return memory

def save_memory(memory: dict) -> None:
    if not isinstance(memory, dict):
        return
    memory = _trim_to_limit(memory)
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        MEMORY_PATH.write_text(
            json.dumps(memory, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def _truncate_value(val: str) -> str:
    if isinstance(val, str) and len(val) > MAX_VALUE_LENGTH:
        return val[:MAX_VALUE_LENGTH].rstrip() + "…"
    return val


def _recursive_update(target: dict, updates: dict) -> bool:
    changed = False
    for key, value in updates.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, dict) and "value" not in value:
            if key not in target or not isinstance(target[key], dict):
                target[key] = {}
                changed = True
            if _recursive_update(target[key], value):
                changed = True
        else:
            new_val  = _truncate_value(str(value["value"] if isinstance(value, dict) else value))
            entry    = {"value": new_val, "updated": datetime.now().strftime("%Y-%m-%d")}
            existing = target.get(key, {})
            if not isinstance(existing, dict) or existing.get("value") != new_val:
                target[key] = entry
                changed = True
    return changed


def update_memory(memory_update: dict) -> dict:
    if not isinstance(memory_update, dict) or not memory_update:
        return load_memory()
    memory = load_memory()
    if _recursive_update(memory, memory_update):
        save_memory(memory)
        print(f"[Memory] 💾 Saved: {list(memory_update.keys())}")
    return memory

def format_memory_for_prompt(memory: dict | None) -> str:
    if not memory:
        return ""

    lines = []

    identity  = memory.get("identity", {})
    id_fields = ["name", "age", "birthday", "city", "job", "language", "school", "nationality"]
    for field in id_fields:
        entry = identity.get(field)
        if entry:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                lines.append(f"{field.title()}: {val}")
    for key, entry in identity.items():
        if key in id_fields:
            continue
        val = entry.get("value") if isinstance(entry, dict) else entry
        if val:
            lines.append(f"{key.replace('_', ' ').title()}: {val}")

    prefs = memory.get("preferences", {})
    if prefs:
        lines.append("")
        lines.append("Preferences:")
        for key, entry in list(prefs.items())[:15]:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                lines.append(f"  - {key.replace('_', ' ').title()}: {val}")

    projects = memory.get("projects", {})
    if projects:
        lines.append("")
        lines.append("Active Projects / Goals:")
        for key, entry in list(projects.items())[:8]:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                lines.append(f"  - {key.replace('_', ' ').title()}: {val}")

    rels = memory.get("relationships", {})
    if rels:
        lines.append("")
        lines.append("People in their life:")
        for key, entry in list(rels.items())[:10]:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                lines.append(f"  - {key.replace('_', ' ').title()}: {val}")

    wishes = memory.get("wishes", {})
    if wishes:
        lines.append("")
        lines.append("Wishes / Plans / Wants:")
        for key, entry in list(wishes.items())[:8]:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                lines.append(f"  - {key.replace('_', ' ').title()}: {val}")

    notes = memory.get("notes", {})
    if notes:
        lines.append("")
        lines.append("Other notes:")
        for key, entry in list(notes.items())[:8]:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                lines.append(f"  - {key}: {val}")

    if not lines:
        return ""

    header = "[WHAT YOU KNOW ABOUT THIS PERSON — use naturally, never recite like a list]\n"
    result = header + "\n".join(lines)
    if len(result) > 2000:
        result = result[:1997] + "…"

    return result + "\n"

def remember(key: str, value: str, category: str = "notes") -> str:
    valid = {"identity", "preferences", "projects", "relationships", "wishes", "notes"}
    if category not in valid:
        category = "notes"
    update_memory({category: {key: {"value": value}}})
    return f"Remembered: {category}/{key} = {value}"


def forget(key: str, category: str = "notes") -> str:
    memory = load_memory()
    cat    = memory.get(category, {})
    if key in cat:
        del cat[key]
        memory[category] = cat
        save_memory(memory)
        return f"Forgotten: {category}/{key}"
    return f"Not found: {category}/{key}"


forget_memory = forget


def should_extract_memory(user_input: str, assistant_response: str) -> bool:
    """
    Uses OpenRouter Free to decide if dialogue yields new user factual insights.
    """
    prompt = (
        "Tu es un module de décision de mémoire pour JARVIS (Tony Stark's AI assistant).\n"
        "Analyse le court dialogue ci-dessous : des faits personnels stables sur l'utilisateur "
        "(ex: préférences, nom de proches, projets de vie, anniversaire, souhaits précis) y sont-ils appris ou modifiés ?\n"
        "Réponds strictement par OUI ou NON, sans explication.\n\n"
        f"Utilisateur: {user_input}\n"
        f"JARVIS: {assistant_response}\n"
    )
    try:
        from core.openrouter_client import generate_completion
        reply = generate_completion(prompt, max_tokens=10, temperature=0.0)
        return "oui" in reply.lower()
    except Exception as e:
        print(f"[Memory Decision] Error or quota limit in memory extraction decision: {e}")
        return False


def extract_memory(user_input: str, assistant_response: str) -> dict:
    """
    Extracts structured long term facts from interaction using OpenRouter.
    """
    prompt = (
        "Tu es le système d'extraction de mémoire structurée de JARVIS.\n"
        "Analyse de manière concise le dialogue suivant et extrais les nouveaux faits personnels de l'utilisateur.\n\n"
        f"Utilisateur: {user_input}\n"
        f"JARVIS: {assistant_response}\n\n"
        "Retourne UNIQUEMENT une chaîne JSON valide représentant l'extraction complète. Ne mets PAS de balise markdown ```json ou ```.\n"
        "La structure JSON doit correspondre strictement à un ou plusieurs de ces groupes :\n"
        "{\n"
        "  \"identity\": {\"name\": \"...\", \"birthday\": \"...\", \"city\": \"...\"},\n"
        "  \"preferences\": {\"cle_pref\": \"valeur\"},\n"
        "  \"projects\": {\"titre_projet\": \"valeur\"},\n"
        "  \"relationships\": {\"prenom_parent\": \"Lien de relation, ex: épouse/ami\"},\n"
        "  \"wishes\": {\"cle_souhait\": \"valeur\"},\n"
        "  \"notes\": {\"titre_note\": \"valeur\"}\n"
        "}\n\n"
        "Si aucune information substantielle ou pérenne n'est détectée, retourne {}."
    )
    try:
        from core.openrouter_client import generate_completion
        reply = generate_completion(prompt, temperature=0.1, max_tokens=1000)
        reply_clean = reply.strip()
        if reply_clean.startswith("```"):
            reply_clean = reply_clean.split("\n", 1)[-1]
            if reply_clean.endswith("```"):
                reply_clean = reply_clean.rsplit("\n", 1)[0]
            reply_clean = reply_clean.strip()
            if reply_clean.lower().startswith("json"):
                reply_clean = reply_clean[4:].strip()
        if not reply_clean or reply_clean == "{}":
            return {}
        return json.loads(reply_clean)
    except Exception as e:
        print(f"[Memory Extractor] Error extracting memory facts: {e}")
        return {}
