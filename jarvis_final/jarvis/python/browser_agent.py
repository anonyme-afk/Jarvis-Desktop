from playwright.async_api import async_playwright
import asyncio
import base64
import os

class BrowserAgent:
    def __init__(self):
        self.browser = None
        self.page = None

    async def _launch(self):
        playwright = await async_playwright().start()
        # Utilise le profil Chrome existant de l'utilisateur
        user_data = os.path.expandvars(
            r"%LOCALAPPDATA%\Google\Chrome\User Data"
        )
        self.browser = await playwright.chromium.launch_persistent_context(
            user_data_dir=user_data,
            headless=False,
            channel="chrome"
        )
        self.page = self.browser.pages[0] if self.browser.pages else await self.browser.new_page()

    async def _go_and_chat(self, site: str, message: str) -> str:
        await self._launch()

        sites = {
            "gemini":  "https://gemini.google.com",
            "chatgpt": "https://chat.openai.com",
            "claude":  "https://claude.ai",
            "perplexity": "https://perplexity.ai",
            "copilot": "https://copilot.microsoft.com"
        }

        url = sites.get(site.lower(), f"https://{site}")
        await self.page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)

        # Trouver la zone de texte et envoyer le message
        selectors = [
            "textarea",
            "div[contenteditable='true']",
            "input[type='text']",
            "[role='textbox']",
            ".message-input",
            "#prompt-textarea"
        ]
        for sel in selectors:
            try:
                el = await self.page.wait_for_selector(sel, timeout=5000)
                if el:
                    await el.click()
                    await el.fill(message)
                    await self.page.keyboard.press("Enter")
                    await asyncio.sleep(4)
                    break
            except:
                continue

        # Prendre un screenshot et lire le contenu
        screenshot = await self.page.screenshot(full_page=False)
        b64 = base64.b64encode(screenshot).decode()

        # Extraire le texte de la page
        text = await self.page.evaluate("""
            () => {
                const els = document.querySelectorAll(
                    'p, [data-message-author-role="assistant"], .response-text, .markdown'
                );
                return Array.from(els).slice(-5).map(e => e.innerText).join(' ');
            }
        """)

        await self.browser.close()
        return text[:1000] if text else f"[screenshot disponible]"

    def run(self, site: str, message: str) -> dict:
        try:
            result = asyncio.run(self._go_and_chat(site, message))
            return {"reply": result, "success": True}
        except Exception as e:
            return {"reply": f"Erreur navigation: {str(e)}", "success": False}

browser_agent = BrowserAgent()
