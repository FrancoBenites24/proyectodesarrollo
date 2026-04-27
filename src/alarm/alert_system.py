"""Sistema de alertas multi-canal con anti-rebote."""

from __future__ import annotations

import os
import threading
import time
from typing import Optional

import numpy as np

from src.core.temporal import AlertLevel, TemporalState
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AlertSystem:
    COOLDOWN_SECONDS = float(os.getenv("ALARM_COOLDOWN_SECONDS", "5"))

    _FREQUENCIES = {
        AlertLevel.LOW: 440,
        AlertLevel.HIGH: 880,
        AlertLevel.CRITICAL: 1200,
    }

    _DURATIONS = {
        AlertLevel.LOW: 0.5,
        AlertLevel.HIGH: 1.0,
        AlertLevel.CRITICAL: 2.0,
    }

    def __init__(self, webhook_url: Optional[str] = None) -> None:
        self._webhook_url = webhook_url or os.getenv("ALARM_WEBHOOK_URL", "")
        self._last_alert_times: dict[AlertLevel, float] = {}
        self._lock = threading.Lock()
        logger.info(
            f"AlertSystem inicializado | "
            f"cooldown={self.COOLDOWN_SECONDS}s | "
            f"webhook={'configurado' if self._webhook_url else 'deshabilitado'}"
        )

    def process(self, state: TemporalState) -> None:
        if state.alert_level == AlertLevel.NONE:
            return

        with self._lock:
            last = self._last_alert_times.get(state.alert_level, 0.0)
            now = time.time()
            if now - last < self.COOLDOWN_SECONDS:
                return
            self._last_alert_times[state.alert_level] = now

        logger.warning(
            f"ALERTA SOMNOLENCIA | nivel={state.alert_level.name} | "
            f"PERCLOS={state.perclos:.1%} | "
            f"frames_cerrados={state.closed_frames}/{state.frames_in_window}"
        )

        self._play_sound_async(state.alert_level)

        if self._webhook_url:
            self._send_webhook_async(state)

    def _play_sound_async(self, level: AlertLevel) -> None:
        threading.Thread(
            target=self._play_sound,
            args=(level,),
            daemon=True,
            name=f"Alert-sound-{level.name}",
        ).start()

    def _play_sound(self, level: AlertLevel) -> None:
        try:
            import sounddevice as sd

            freq = self._FREQUENCIES.get(level, 440)
            duration = self._DURATIONS.get(level, 0.5)
            sample_rate = 44100

            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            tone = 0.4 * np.sin(2 * np.pi * freq * t)
            fade = int(sample_rate * 0.05)
            tone[:fade] *= np.linspace(0, 1, fade)
            tone[-fade:] *= np.linspace(1, 0, fade)

            sd.play(tone.astype(np.float32), samplerate=sample_rate)
            sd.wait()
        except Exception:
            logger.exception("Error al reproducir alarma sonora")

    def _send_webhook_async(self, state: TemporalState) -> None:
        threading.Thread(
            target=self._send_webhook,
            args=(state,),
            daemon=True,
            name="Alert-webhook",
        ).start()

    def _send_webhook(self, state: TemporalState) -> None:
        try:
            import httpx

            payload = {
                "alert_level": state.alert_level.name,
                "perclos": state.perclos,
                "closed_frames": state.closed_frames,
                "total_frames": state.frames_in_window,
                "timestamp": time.time(),
            }
            response = httpx.post(self._webhook_url, json=payload, timeout=5.0)
            logger.info(
                f"Webhook enviado | nivel={state.alert_level.name} | "
                f"status={response.status_code}"
            )
        except Exception:
            logger.exception("Error al enviar webhook de alerta")
