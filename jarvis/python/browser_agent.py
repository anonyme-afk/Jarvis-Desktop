"""
Agent de navigation web autonome.
Source : github.com/browser-use/browser-use
pip install browser-use playwright
playwright install chromium
"""
import asyncio
import threading
from typing import Optional

class BrowserAgent:
    def __init__(self):
        self.available = False
        self._check_availability()

    def _check_availability(self):
        try:
            import browser_use
            self.available = True
            print("[BROWSER] browser-use disponible")
        except ImportError:
            print("[BROWSER] browser-use non installé. pip install browser-use")

    def run_task(self, task: str, ai_provider_name: str = "gemini") -> str:
        """
        Lance une tâche de navigation autonome.
        Exemple : "Va sur LinkedIn et lis les notifications non lues"
        """
        if not self.available:
            return "browser-use non installé. Faire : pip install browser-use"
        try:
            result = asyncio.run(self._async_task(task, ai_provider_name))
            return result
        except Exception as e:
            return f"Erreur navigation: {str(e)}"

    async def _async_task(self, task: str, provider: str) -> str:
        from browser_use import Agent
        import os
        if provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=os.environ.get("GEMINI_API_KEY")
            )
        elif provider == "openai":
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model="gpt-4o", api_key=os.environ.get("OPENAI_API_KEY"))
        else:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash",
                google_api_key=os.environ.get("GEMINI_API_KEY"))

        agent = Agent(task=task, llm=llm)
        result = await agent.run()
        return str(result)

browser_agent = BrowserAgent()
