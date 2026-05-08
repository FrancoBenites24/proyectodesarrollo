"""Análisis temporal de somnolencia usando PERCLOS.

PERCLOS (PERcentage of eye CLOSure) representa el porcentaje
de tiempo en que los ojos permanecen cerrados dentro de una
ventana temporal.

Es uno de los indicadores más utilizados por la industria y
la NHTSA para detección de fatiga en conductores.

Niveles:
- >20%  -> Somnolencia leve
- >40%  -> Somnolencia alta
- >60%  -> Riesgo crítico
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import IntEnum

from src.utils.logger import get_logger

logger = get_logger(__name__)


class AlertLevel(IntEnum):
    """Nivel de alerta basado en PERCLOS."""

    NONE = 0
    LOW = 1
    HIGH = 2
    CRITICAL = 3


@dataclass(frozen=True)
class TemporalState:
    """Estado temporal del conductor."""

    perclos: float
    alert_level: AlertLevel
    frames_in_window: int
    closed_frames: int


class TemporalAnalyzer:
    """Ventana deslizante para cálculo de PERCLOS.

    Ejemplo:
        analyzer = TemporalAnalyzer(window_seconds=3, fps=30)

        state = analyzer.update(eye_open=False)

        print(state.perclos)
        print(state.alert_level)
    """

    # (threshold, alert_level)
    _THRESHOLDS = [
        (0.60, AlertLevel.CRITICAL),
        (0.40, AlertLevel.HIGH),
        (0.20, AlertLevel.LOW),
    ]

    def __init__(
        self,
        window_seconds: int = 3,
        fps: int = 30,
    ) -> None:
        """Inicializa el analizador temporal.

        Args:
            window_seconds: tamaño de ventana temporal.
            fps: frames por segundo esperados.
        """
        if window_seconds <= 0:
            raise ValueError("window_seconds debe ser > 0")

        if fps <= 0:
            raise ValueError("fps debe ser > 0")

        self._window_size = window_seconds * fps

        self._buffer: deque[bool] = deque(maxlen=self._window_size)

        # contador incremental de frames cerrados
        self._closed_count = 0

        logger.info(
            "TemporalAnalyzer inicializado | "
            f"ventana={window_seconds}s | "
            f"fps={fps} | "
            f"buffer={self._window_size}"
        )

    def update(self, eye_open: bool) -> TemporalState:
        """Agrega un frame y retorna el estado actual.

        Args:
            eye_open:
                True si el ojo está abierto.
                False si el ojo está cerrado.

        Returns:
            TemporalState actualizado.
        """

        # Si el buffer está lleno, verificar qué valor saldrá
        if len(self._buffer) == self._window_size:
            oldest = self._buffer[0]

            # si el frame viejo estaba cerrado
            if not oldest:
                self._closed_count -= 1

        # agregar nuevo frame
        self._buffer.append(eye_open)

        # actualizar contador
        if not eye_open:
            self._closed_count += 1

        return self.state

    @property
    def state(self) -> TemporalState:
        """Retorna el estado actual del análisis temporal."""
        n = len(self._buffer)

        if n == 0:
            return TemporalState(
                perclos=0.0,
                alert_level=AlertLevel.NONE,
                frames_in_window=0,
                closed_frames=0,
            )

        perclos = self._closed_count / n

        level = AlertLevel.NONE

        for threshold, alert in self._THRESHOLDS:
            if perclos >= threshold:
                level = alert
                break

        return TemporalState(
            perclos=round(perclos, 3),
            alert_level=level,
            frames_in_window=n,
            closed_frames=self._closed_count,
        )

    @property
    def is_drowsy(self) -> bool:
        """Indica si existe somnolencia."""
        return self.state.alert_level != AlertLevel.NONE

    @property
    def perclos_percentage(self) -> float:
        """Retorna PERCLOS en porcentaje."""
        return round(self.state.perclos * 100, 1)

    @property
    def description(self) -> str:
        """Descripción textual del estado."""
        descriptions = {
            AlertLevel.NONE: "Conductor atento",
            AlertLevel.LOW: "Somnolencia leve",
            AlertLevel.HIGH: "Somnolencia alta",
            AlertLevel.CRITICAL: "PELIGRO CRÍTICO",
        }

        return descriptions[self.state.alert_level]

    def should_trigger_alarm(self) -> bool:
        """Determina si debe activarse una alarma."""
        return self.state.alert_level >= AlertLevel.HIGH

    def summary(self) -> str:
        """Resumen legible del estado actual."""
        state = self.state

        return (
            f"PERCLOS={state.perclos * 100:.1f}% | "
            f"Nivel={state.alert_level.name} | "
            f"Cerrados={state.closed_frames}/"
            f"{state.frames_in_window}"
        )

    def reset(self) -> None:
        """Reinicia el estado temporal."""
        self._buffer.clear()
        self._closed_count = 0

        logger.debug("TemporalAnalyzer reiniciado")