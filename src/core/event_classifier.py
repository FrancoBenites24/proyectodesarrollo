"""Clasificación de eventos detectados."""

from __future__ import annotations

from src.core.temporal import AlertLevel


def classify_event(result, state) -> list[str]:
    """
    Clasifica los eventos activos en el frame actual.
    """

    events: list[str] = []

    if state.alert_level != AlertLevel.NONE:
        events.append("drowsiness")

    if result.phone_detected:
        events.append("phone")

    if result.yawning:
        events.append("yawn")

    if result.is_distracted:
        events.append("distraction")

    return events