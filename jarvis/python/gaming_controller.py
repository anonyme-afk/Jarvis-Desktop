"""
Contrôle de jeux vidéo via signaux matériels réels.
Source : github.com/learncodebygaming/pydirectinput
pip install pydirectinput
"""
try:
    import pydirectinput
    pydirectinput.FAILSAFE = True
    pydirectinput.PAUSE = 0.02
    PYDIRECTINPUT_AVAILABLE = True
except ImportError:
    PYDIRECTINPUT_AVAILABLE = False
    
import time
import threading
import cv2
import base64
from typing import Optional

class GamingController:

    def press_key(self, key: str, duration: float = 0.05):
        """Appuie sur une touche (traverse les protections DirectX)"""
        if not PYDIRECTINPUT_AVAILABLE: return
        pydirectinput.keyDown(key)
        time.sleep(duration)
        pydirectinput.keyUp(key)

    def move_camera(self, dx: int, dy: int):
        """Déplace la caméra dans un jeu FPS/TPS"""
        if not PYDIRECTINPUT_AVAILABLE: return
        pydirectinput.moveRel(dx, dy, relative=True)

    def walk_forward(self, seconds: float):
        """Marche en avant pendant N secondes"""
        if not PYDIRECTINPUT_AVAILABLE: return
        pydirectinput.keyDown('w')
        time.sleep(seconds)
        pydirectinput.keyUp('w')

    def auto_farm(self, key: str, interval: float, duration: float,
                  on_progress=None):
        """
        Mode farm automatique : appuie sur une touche en boucle.
        Parfait pour Minecraft, Satisfactory, etc.
        """
        end_time = time.time() + duration
        count = 0
        while time.time() < end_time:
            self.press_key(key)
            count += 1
            if on_progress:
                on_progress(count, duration - (time.time() - (end_time - duration)))
            time.sleep(interval)

    def capture_game_screen(self) -> Optional[str]:
        """Capture l'écran du jeu pour analyse par l'IA"""
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            import io
            from PIL import Image
            buf = io.BytesIO()
            screenshot.save(buf, format='JPEG', quality=70)
            return base64.b64encode(buf.getvalue()).decode()
        except:
            return None

    def analyze_game_state(self, ai_client, question: str = None) -> str:
        """Capture l'écran et demande à l'IA d'analyser l'état du jeu"""
        screen_b64 = self.capture_game_screen()
        if not screen_b64:
            return "Impossible de capturer l'écran"
        q = question or "Analyse cet écran de jeu : que vois-tu ? Y a-t-il des dangers ou des actions urgentes ?"
        return ai_client.chat([{"role": "user", "content": q}], image_b64=screen_b64)

gaming = GamingController()
