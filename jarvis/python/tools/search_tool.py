"""
Recherche web via DuckDuckGo (gratuit, sans clé API)
+ résumé automatique des résultats par l'IA
Basé sur : https://github.com/deedy5/duckduckgo_search
"""
from duckduckgo_search import DDGS
from typing import List, Dict

def web_search(query: str, max_results: int = 5) -> List[Dict]:
    """
    Recherche sur le web. Retourne les N premiers résultats.
    Gratuit, pas de clé API.
    """
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title": r.get("title", ""),
                "url":   r.get("href", ""),
                "body":  r.get("body", "")[:300]  # 300 chars max
            })
    return results

def news_search(query: str, max_results: int = 5) -> List[Dict]:
    """Recherche dans les actualités récentes"""
    results = []
    with DDGS() as ddgs:
        for r in ddgs.news(query, max_results=max_results):
            results.append({
                "title": r.get("title", ""),
                "url":   r.get("url", ""),
                "body":  r.get("body", "")[:300],
                "date":  r.get("date", "")
            })
    return results

def image_search(query: str, max_results: int = 3) -> List[str]:
    """Retourne des URLs d'images"""
    urls = []
    with DDGS() as ddgs:
        for r in ddgs.images(query, max_results=max_results):
            urls.append(r.get("image", ""))
    return urls

def format_results_for_ai(results: List[Dict]) -> str:
    """Formatte les résultats pour les injecter dans le prompt IA"""
    if not results:
        return "Aucun résultat trouvé."
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}\n   {r['body']}\n   Source: {r['url']}")
    return "\n\n".join(lines)
