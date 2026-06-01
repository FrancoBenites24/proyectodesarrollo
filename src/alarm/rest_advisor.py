"""Asesor simulado de paradas de descanso."""

from __future__ import annotations

import random
from dataclasses import dataclass

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class RestStop:
    """Lugar sugerido para descansar."""

    name: str
    type: str
    distance_km: float


class RestAdvisor:
    """Sugiere paradas de descanso simuladas al conductor."""

    _SIMULATED_STOPS = [
        RestStop("Grifo Repsol - Km 45", "gasolinera", 2.5),
        RestStop("Restaurant El Viajero", "restaurante", 4.0),
        RestStop("Área de Descanso Norte", "area_descanso", 6.5),
        RestStop("Grifo Pecsa - Salida 12", "gasolinera", 8.0),
        RestStop("Paradero Los Pinos", "area_descanso", 3.2),
    ]

    def suggest(self, count: int = 3) -> list[RestStop]:
        """Retorna sugerencias simuladas de paradas cercanas."""
        stops = random.sample(
            self._SIMULATED_STOPS, min(count, len(self._SIMULATED_STOPS))
        )
        return sorted(stops, key=lambda s: s.distance_km)

    def format_suggestion(self) -> str:
        """Genera un mensaje de voz con la sugerencia más cercana."""
        stops = self.suggest(count=1)
        if stops:
            stop = stops[0]
            return (
                f"Puedes descansar en {stop.name}, "
                f"a {stop.distance_km} kilómetros de distancia."
            )
        return "Busca un lugar seguro para detenerte y descansar."
