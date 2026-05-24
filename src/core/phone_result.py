"""Resultado de la detección de celular."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhoneResult:
    """Resultado de la detección de uso de celular.

    Attributes:
        phone_detected: True si se detecta posible uso de celular.
        hand_detected: True si se detectó al menos una mano.
        hand_position: Posición normalizada (x, y) del centro de la mano, o None.
        confidence: Nivel de confianza de la detección (0.0 a 1.0).
    """

    phone_detected: bool = False
    hand_detected: bool = False
    hand_position: tuple[float, float] | None = None
    confidence: float = 0.0