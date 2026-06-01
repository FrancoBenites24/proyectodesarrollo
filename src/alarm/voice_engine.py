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
            temp_engine = pyttsx3.init()
            self._rate = 150
            self._volume = 0.9
            self._voice_id = None

            voices = temp_engine.getProperty("voices")
            for voice in voices:
                if "spanish" in voice.name.lower() or "español" in voice.name.lower():
                    self._voice_id = voice.id
                    logger.info(f"Voz seleccionada para guardar: {voice.name}")
                    break

            del temp_engine
            self._speak_lock = threading.Lock()
            self._initialized = True
            logger.info("VoiceEngine configurado correctamente")
        except Exception:
            logger.exception("Error al configurar VoiceEngine")
            self._initialized = False

    def speak(self, text: str) -> None:
        if not self._initialized:
            logger.warning("VoiceEngine no inicializado — omitiendo voz")
            return

        with self._speak_lock:
            co_init = False
            try:
                import pythoncom
                pythoncom.CoInitialize()
                co_init = True
            except (ImportError, Exception):
                pass

            try:
                engine = pyttsx3.init()
                engine.setProperty("rate", self._rate)
                engine.setProperty("volume", self._volume)
                if self._voice_id:
                    engine.setProperty("voice", self._voice_id)

                engine.say(text)
                engine.runAndWait()
                del engine
            except Exception:
                logger.exception(f"Error al hablar: {text}")
            finally:
                if co_init:
                    try:
                        import pythoncom
                        pythoncom.CoUninitialize()
                    except:
                        pass
