from playwright.async_api import async_playwright
import asyncio
import base64
import os
import threading

class BrowserAgent:
    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None
        self.headless = True
        self.available = False
        self._loop = None
        self._thread = None
        self._start_thread()

    def _start_thread(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._init_browser())
        self._loop.run_forever()

    async def _init_browser(self):
        try:
            if self.playwright is None:
                self.playwright = await async_playwright().start()
            
            user_data = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
            if not os.path.exists(user_data):
                user_data = os.path.expanduser(r"~/.config/google-chrome") # fallback linux
            
            self.browser = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=user_data,
                headless=self.headless,
                channel="chrome",
                args=["--disable-blink-features=AutomationControlled"]
            )
            self.page = self.browser.pages[0] if self.browser.pages else await self.browser.new_page()
            self.available = True
        except Exception as e:
            print(f"[BrowserAgent] Failed to init: {e}")
            self.available = False

    async def _close_browser(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.page = None

    def toggle_view(self, visible: bool):
        new_headless = not visible
        if new_headless == self.headless:
            return {"success": True, "headless": self.headless}
        self.headless = new_headless
        
        async def _relaunch():
            await self._close_browser()
            await self._init_browser()
        
        asyncio.run_coroutine_threadsafe(_relaunch(), self._loop).result(timeout=15)
        return {"success": True, "headless": self.headless}

    async def _do_chat(self, site: str, message: str, mode: str):
        if not self.browser or not self.page:
            await self._init_browser()
            if not self.browser:
                return "Erreur: Impossible de démarrer le navigateur."

        sites = {
            "gemini":  "https://gemini.google.com",
            "chatgpt": "https://chatgpt.com",
            "claude":  "https://claude.ai"
        }
        url = sites.get(site.lower(), f"https://{site}")
        
        if self.page.url != url and not self.page.url.startswith(url):
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            
        if mode == "deep" and site.lower() == "gemini":
            try:
                # Tentative d'activer "Deep Research" 
                deep_btn = await self.page.query_selector('[aria-label*="Deep Research"], [aria-label*="Recherche détaillée"]')
                if deep_btn:
                    await deep_btn.click()
                    await asyncio.sleep(1)
            except: pass

        # Chercher l'input
        selectors = [
            "rich-textarea",
            "textarea",
            "div[contenteditable='true']",
            "#prompt-textarea"
        ]
        
        input_el = None
        for sel in selectors:
            try:
                input_el = await self.page.wait_for_selector(sel, state="visible", timeout=2000)
                if input_el:
                    break
            except: continue
            
        if not input_el:
            return "Erreur: Impossible de trouver la zone de texte."

        await input_el.fill(message)
        await self.page.keyboard.press("Enter")
        
        # Attendre la réponse
        try:
            if site.lower() == "gemini":
                await self.page.wait_for_selector('message-content, .response-container, .model-response-text', state="visible", timeout=30000)
                # Attendre que ça s'arrête d'écrire
                await asyncio.sleep(4)
                text = await self.page.evaluate("""
                    () => {
                        const messages = Array.from(document.querySelectorAll('message-content, .response-container, .model-response-text'));
                        return messages.length > 0 ? messages[messages.length - 1].innerText : "";
                    }
                """)
            else:
                await asyncio.sleep(6)
                text = await self.page.evaluate("""
                    () => {
                        const messages = Array.from(document.querySelectorAll('.markdown, [data-message-author-role="assistant"]'));
                        return messages.length > 0 ? messages[messages.length - 1].innerText : "";
                    }
                """)
            return text if text else "Réponse vide."
        except Exception as e:
            return f"Timeout en attendant la réponse: {e}"

    def run_task(self, site: str, message: str, mode: str = "normal") -> str:
        if not self._loop:
            return "Erreur: thread non démarré"
        future = asyncio.run_coroutine_threadsafe(self._do_chat(site, message, mode), self._loop)
        try:
            return future.result(timeout=45)
        except Exception as e:
            return f"Erreur de tâche navigateur: {e}"

browser_agent = BrowserAgent()
