"""Schemas Pydantic v2 para request/response de la API."""

from __future__ import annotations

from enum import IntEnum
from typing import Literal

from pydantic import BaseModel, Field


class AlertLevelSchema(IntEnum):
    NONE = 0
    LOW = 1
    HIGH = 2
    CRITICAL = 3


class DrowsinessMetrics(BaseModel):
    ear: float = Field(ge=0.0, le=1.0, description="Eye Aspect Ratio")
    mor: float = Field(ge=0.0, description="Mouth Open Ratio")
    perclos: float = Field(ge=0.0, le=1.0, description="% frames ojos cerrados")
    alert_level: AlertLevelSchema

    phone_detected: bool = False

    face_detected: bool

    fps: float = Field(ge=0.0)

    timestamp: float


class SystemHealth(BaseModel):
    status: Literal["ok", "degraded", "error"]
    camera_connected: bool
    uptime_seconds: float
    version: str = "3.0.0"


class StreamStartRequest(BaseModel):
    source: int | str = Field(
        default=0,
        description="Fuente de cámara: 0 para webcam, o ruta a archivo de video",
    )
