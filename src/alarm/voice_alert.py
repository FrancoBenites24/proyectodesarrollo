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

    _CUSTOM_COOLDOWNS = {
        _KEY_PHONE: 15.0,
        _KEY_DISTRACTION: 15.0,
        _KEY_YAWN: 15.0,
        "somnolencia_global": 12.0,
    }

    def __init__(self, webhook_url: Optional[str] = None) -> None:
        super().__init__(webhook_url=webhook_url)
        self._voice = VoiceEngine()
        self._extended_last_times: dict[str, float] = {}
        self._extended_lock = threading.Lock()
        self._phone_consecutive_frames = 0
        self._distraction_consecutive_frames = 0
        logger.info("VoiceAlertSystem inicializado con persistencia y cooldowns extendidos")

    def _play_sound(self, level: AlertLevel) -> None:
        """Reemplaza el tono sinusoidal por un mensaje de voz con cooldown global de somnolencia."""
        now = time.time()
        with self._extended_lock:
            last_somn = self._extended_last_times.get("somnolencia_global", 0.0)
            cooldown = self._CUSTOM_COOLDOWNS.get("somnolencia_global", 12.0)
            if now - last_somn < cooldown:
                return
            self._extended_last_times["somnolencia_global"] = now

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
        cooldown = self._CUSTOM_COOLDOWNS.get(key, self.COOLDOWN_SECONDS)
        with self._extended_lock:
            last = self._extended_last_times.get(key, 0.0)
            if now - last < cooldown:
                return False
            self._extended_last_times[key] = now
            return True

    def process_extended(self, state, frame_result, timer) -> None:
        """Procesa alertas extendidas con persistencia y filtrado de ruido."""
        # 1. Somnolencia normal (solo si el buffer temporal de PERCLOS tiene al menos 80 frames)
        # Esto evita falsas alarmas instantáneas en los primeros 2.5 segundos tras iniciar
        if state.frames_in_window >= 80:
            self.process(state)

        # 2. Celular (requiere persistencia de 30 frames consecutivos ~ 1.0 segundo a 30fps)
        if frame_result.phone_detected:
            self._phone_consecutive_frames += 1
        else:
            self._phone_consecutive_frames = 0

        if self._phone_consecutive_frames >= 30:
            if self._can_alert(_KEY_PHONE):
                logger.warning("Alerta: celular detectado (persistente)")
                self._speak_async(self._PHONE_MESSAGE)
            self._phone_consecutive_frames = 30  # tope para no desbordar

        # 3. Distracción (requiere persistencia de 45 frames consecutivos ~ 1.5 segundos a 30fps)
        if frame_result.is_distracted:
            self._distraction_consecutive_frames += 1
        else:
            self._distraction_consecutive_frames = 0

        if self._distraction_consecutive_frames >= 45:
            if self._can_alert(_KEY_DISTRACTION):
                logger.warning("Alerta: conductor distraído (persistente)")
                self._speak_async(self._DISTRACTION_MESSAGE)
            self._distraction_consecutive_frames = 45  # tope para no desbordar

        # 4. Bostezo
        if frame_result.yawning and self._can_alert(_KEY_YAWN):
            logger.warning("Alerta: bostezo detectado")
            self._speak_async(self._YAWN_MESSAGE)

        # 5. Temporizador de conducción
        timer_msg = timer.check()
        if timer_msg and self._can_alert(_KEY_TIMER):
            logger.warning(f"Alerta temporizador: {timer_msg}")
            self._speak_async(timer_msg)
