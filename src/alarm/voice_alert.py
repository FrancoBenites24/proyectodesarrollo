"""Sistema de alertas con voz usando pyttsx3."""

from __future__ import annotations

import threading
import time
from typing import Optional

from src.alarm.alert_system import AlertSystem
from src.alarm.voice_engine import VoiceEngine
from src.core.temporal import AlertLevel
from src.utils.logger import get_logger

logger = get_logger(__name__)

_KEY_PHONE = "phone"
_KEY_DISTRACTION = "distraction"
_KEY_YAWN = "yawn"
_KEY_TIMER = "timer"


class VoiceAlertSystem(AlertSystem):
    """AlertSystem que usa voz en lugar de tonos sinusoidales."""

    _DROWSINESS_MESSAGES = {
        AlertLevel.LOW: "Atención, mantén los ojos abiertos.",
        AlertLevel.HIGH: (
            "Cuidado, estás mostrando signos de fatiga. "
            "Considera detenerte y descansar."
        ),
        AlertLevel.CRITICAL: (
            "Alerta crítica. Detente en un lugar seguro " "y descansa inmediatamente."
        ),
    }

    _PHONE_MESSAGE = "Por favor, deja el celular y concéntrate en la carretera."

    _DISTRACTION_MESSAGE = "Atención, mantén la vista en el camino."

    _YAWN_MESSAGE = "Has bostezado varias veces. " "Considera detenerte a descansar."

    def __init__(self, webhook_url: Optional[str] = None) -> None:
        super().__init__(webhook_url=webhook_url)
        self._voice = VoiceEngine()
        self._extended_last_times: dict[str, float] = {}
        self._extended_lock = threading.Lock()
        logger.info("VoiceAlertSystem inicializado")

    def _play_sound(self, level: AlertLevel) -> None:
        """Reemplaza el tono sinusoidal por un mensaje de voz."""
        message = self._DROWSINESS_MESSAGES.get(level)
        if message:
            self._voice.speak(message)

    def _speak_async(self, message: str) -> None:
        """Habla un mensaje en un hilo separado."""
        threading.Thread(
            target=self._voice.speak,
            args=(message,),
            daemon=True,
            name="VoiceAlert-speak",
        ).start()

    def _can_alert(self, key: str) -> bool:
        """Verifica y actualiza el cooldown para un tipo de alerta."""
        now = time.time()
        with self._extended_lock:
            last = self._extended_last_times.get(key, 0.0)
            if now - last < self.COOLDOWN_SECONDS:
                return False
            self._extended_last_times[key] = now
            return True

    def process_extended(self, state, frame_result, timer) -> None:
        """Procesa alertas extendidas: celular, distracción, bostezo y timer."""
        # 1. Somnolencia normal (con su propio cooldown heredado)
        self.process(state)

        # 2. Celular
        if frame_result.phone_detected and self._can_alert(_KEY_PHONE):
            logger.warning("Alerta: celular detectado")
            self._speak_async(self._PHONE_MESSAGE)

        # 3. Distracción
        if frame_result.is_distracted and self._can_alert(_KEY_DISTRACTION):
            logger.warning("Alerta: conductor distraído")
            self._speak_async(self._DISTRACTION_MESSAGE)

        # 4. Bostezo
        if frame_result.yawning and self._can_alert(_KEY_YAWN):
            logger.warning("Alerta: bostezo detectado")
            self._speak_async(self._YAWN_MESSAGE)

        # 5. Temporizador de conducción
        timer_msg = timer.check()
        if timer_msg and self._can_alert(_KEY_TIMER):
            logger.warning(f"Alerta temporizador: {timer_msg}")
            self._speak_async(timer_msg)
