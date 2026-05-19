"""Motor de voz Thread-safe para alertas habladas."""

from __future__ import annotations

import threading
from typing import Optional

import pyttsx3

from src.utils.logger import get_logger

logger = get_logger(__name__)


class VoiceEngine:
    _instance: Optional[VoiceEngine] = None
    _lock = threading.Lock()

    def __new__(cls) -> VoiceEngine:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", 150)
            self._engine.setProperty("volume", 0.9)

            voices = self._engine.getProperty("voices")
            for voice in voices:
                if "spanish" in voice.name.lower() or "español" in voice.name.lower():
                    self._engine.setProperty("voice", voice.id)
                    logger.info(f"Voz seleccionada: {voice.name}")
                    break

            self._speak_lock = threading.Lock()
            self._initialized = True
            logger.info("VoiceEngine inicializado correctamente")
        except Exception:
            logger.exception("Error al inicializar VoiceEngine")
            self._initialized = False

    def speak(self, text: str) -> None:
        if not self._initialized:
            logger.warning("VoiceEngine no inicializado — omitiendo voz")
            return

        with self._speak_lock:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception:
                logger.exception(f"Error al hablar: {text}")