"""Sistema de alertas con voz usando pyttsx3."""

from __future__ import annotations

import threading
from typing import Optional

from src.alarm.alert_system import AlertSystem
from src.alarm.voice_engine import VoiceEngine
from src.core.temporal import AlertLevel, TemporalState
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VoiceAlertSystem(AlertSystem):
    """AlertSystem que usa voz en lugar de tonos sinusoidales.

    Hereda el anti-rebote y webhook del AlertSystem base,
    pero reemplaza _play_sound por mensajes de voz.
    """

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

    _YAWN_MESSAGE = "Has bostezado varias veces. Busca un lugar para descansar."

    def __init__(self, webhook_url: Optional[str] = None) -> None:
        super().__init__(webhook_url=webhook_url)
        self._voice = VoiceEngine()
        logger.info("VoiceAlertSystem inicializado")

    def _play_sound(self, level: AlertLevel) -> None:
        """Reemplaza el tono sinusoidal por un mensaje de voz."""
        message = self._DROWSINESS_MESSAGES.get(level)
        if message:
            self._voice.speak(message)
