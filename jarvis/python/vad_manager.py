"""
Voice Activity Detection — permet d'interrompre JARVIS en lui coupant la parole.
Source : github.com/snakers4/silero-vad
"""
import threading
import queue
import time
import os

class VADManager:
    def __init__(self, on_speech_detected=None, on_speech_end=None):
        self.on_speech_detected = on_speech_detected
        self.on_speech_end = on_speech_end
        self.model = None
        self.is_speaking_ai = False
        self.interrupt_event = threading.Event()
        self._load_model()

    def _load_model(self):
        try:
            import torch
            model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                trust_repo=True
            )
            self.model = model
            self.utils = utils
            print("[VAD] Silero VAD chargé")
        except Exception as e:
            print(f"[VAD] Silero non disponible: {e}. Utilisation du mode fallback.")
            self.model = None

    def start_listening(self):
        """Lance la détection en continu dans un thread de fond"""
        threading.Thread(target=self._vad_loop, daemon=True).start()

    def _vad_loop(self):
        if not self.model:
            self._fallback_vad_loop()
            return
        try:
            import pyaudio
            import torch
            pa = pyaudio.PyAudio()
            stream = pa.open(
                rate=16000, channels=1, format=pyaudio.paInt16,
                input=True, frames_per_buffer=512
            )
            get_speech_timestamps = self.utils[0]
            print("[VAD] Écoute permanente active")
            while True:
                data = stream.read(512, exception_on_overflow=False)
                audio_tensor = torch.frombuffer(data, dtype=torch.int16).float() / 32768.0
                speech_prob = self.model(audio_tensor, 16000).item()
                if speech_prob > 0.85:
                    if self.is_speaking_ai:
                        # L'utilisateur parle pendant que JARVIS parle → interruption
                        self.interrupt_event.set()
                        if self.on_speech_detected:
                            self.on_speech_detected()
        except Exception as e:
            print(f"[VAD] Erreur: {e}")

    def _fallback_vad_loop(self):
        """Mode fallback sans Silero : détection basique par volume"""
        try:
            import pyaudio
            import audioop
            pa = pyaudio.PyAudio()
            stream = pa.open(
                rate=16000, channels=1, format=pyaudio.paInt16,
                input=True, frames_per_buffer=1024
            )
            THRESHOLD = 500
            while True:
                data = stream.read(1024, exception_on_overflow=False)
                rms = audioop.rms(data, 2)
                if rms > THRESHOLD and self.is_speaking_ai:
                    self.interrupt_event.set()
                    if self.on_speech_detected:
                        self.on_speech_detected()
                time.sleep(0.05)
        except Exception as e:
            print(f"[VAD Fallback] Erreur: {e}")

    def set_ai_speaking(self, speaking: bool):
        self.is_speaking_ai = speaking
        if not speaking:
            self.interrupt_event.clear()

vad = VADManager()
