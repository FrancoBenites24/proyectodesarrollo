"""Análisis temporal de somnolencia usando PERCLOS."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import IntEnum

from src.utils.logger import get_logger

logger = get_logger(__name__)


class AlertLevel(IntEnum):
    """Nivel de alerta basado en PERCLOS."""

    NONE = 0
    LOW = 1  # PERCLOS > 20%
    HIGH = 2  # PERCLOS > 40%
    CRITICAL = 3  # PERCLOS > 60%


@dataclass(frozen=True)
class TemporalState:
    """Estado temporal del conductor."""

    perclos: float
    alert_level: AlertLevel
    frames_in_window: int
    closed_frames: int


class TemporalAnalyzer:
    """Ventana deslizante para cálculo de PERCLOS.

    Ejemplo de uso:
        analyzer = TemporalAnalyzer(window_seconds=3, fps=30)
        state = analyzer.update(eye_open=False)
        print(state.alert_level)  # AlertLevel.NONE o LOW/HIGH/CRITICAL
    """

    # (threshold, alert_level) — evaluados de mayor a menor
    _THRESHOLDS = [
        (0.60, AlertLevel.CRITICAL),
        (0.40, AlertLevel.HIGH),
        (0.20, AlertLevel.LOW),
    ]

    def __init__(self, window_seconds: int = 3, fps: int = 30) -> None:
        self._window_size = window_seconds * fps
        self._buffer: deque[bool] = deque(maxlen=self._window_size)
        logger.info(
            f"TemporalAnalyzer | ventana={window_seconds}s | fps={fps} | "
            f"tamaño_buffer={self._window_size}"
        )

    def update(self, eye_open: bool) -> TemporalState:
        """Agrega un frame a la ventana y retorna el estado actual.

        Args:
            eye_open: True si el ojo está abierto en el frame actual.

        Returns:
            TemporalState con PERCLOS y nivel de alerta.
        """
        self._buffer.append(eye_open)
        return self.state

    @property
    def state(self) -> TemporalState:
        """Calcula y retorna el estado temporal actual."""
        n = len(self._buffer)
        if n == 0:
            return TemporalState(0.0, AlertLevel.NONE, 0, 0)

        closed = sum(1 for v in self._buffer if not v)
        perclos = closed / n

        level = AlertLevel.NONE
        for threshold, alert in self._THRESHOLDS:
            if perclos >= threshold:
                level = alert
                break

        return TemporalState(
            perclos=round(perclos, 3),
            alert_level=level,
            frames_in_window=n,
            closed_frames=closed,
        )

    def reset(self) -> None:
        """Limpia el buffer (por ejemplo al inicio de un viaje nuevo)."""
        self._buffer.clear()
        logger.debug("TemporalAnalyzer buffer reiniciado")
