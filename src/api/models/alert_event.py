"""Modelo AlertEvent para la base de datos."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.api.database import Base


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    driver_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("drivers.id"), nullable=False
    )
    alert_level: Mapped[str] = mapped_column(String(20), nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    perclos: Mapped[float] = mapped_column(Float, nullable=False)
    ear: Mapped[float] = mapped_column(Float, nullable=False)
    mor: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now())
