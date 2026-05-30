"""Temporizador de conducción continua."""

from __future__ import annotations

import time
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DrivingTimer:
    """Alerta cuando el conductor lleva mucho tiempo sin descansar."""

    MAX_HOURS = 4.0
    WARNING_MINUTES_BEFORE = 30

    def __init__(self) -> None:
        self._start_time: Optional[float] = None
        self._paused = False
        logger.info(
            f"DrivingTimer inicializado | "
            f"max_hours={self.MAX_HOURS} | "
            f"warning_before={self.WARNING_MINUTES_BEFORE}min"
        )

    def start(self) -> None:
        """Inicia el temporizador de conducción."""
        self._start_time = time.time()
        self._paused = False
        logger.info("Temporizador de conducción iniciado")

    def stop(self) -> None:
        """Detiene y reinicia el temporizador."""
        self._start_time = None
        self._paused = False
        logger.info("Temporizador de conducción detenido")

    @property
    def elapsed_minutes(self) -> float:
        """Minutos transcurridos desde el inicio."""
        if self._start_time is None:
            return 0.0
        return (time.time() - self._start_time) / 60.0

    def check(self) -> Optional[str]:
        """Verifica si el conductor debe descansar."""
        if self._start_time is None:
            return None

        elapsed_min = self.elapsed_minutes
        max_min = self.MAX_HOURS * 60
        warning_min = max_min - self.WARNING_MINUTES_BEFORE

        if elapsed_min >= max_min:
            return (
                f"Llevas {elapsed_min:.0f} minutos conduciendo. "
                f"Por seguridad, detente y descansa al menos 15 minutos."
            )
        elif elapsed_min >= warning_min:
            remaining = max_min - elapsed_min
            return (
                f"Llevas {elapsed_min:.0f} minutos conduciendo. "
                f"Te quedan {remaining:.0f} minutos antes del "
                f"descanso recomendado."
            )
        return None