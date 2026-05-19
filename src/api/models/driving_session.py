"""Modelo DrivingSession para la base de datos."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from src.api.database import Base


class DrivingSession(Base):
    __tablename__ = "driving_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    driver_id: Mapped[int] = mapped_column(Integer, ForeignKey("drivers.id"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_alerts: Mapped[int] = mapped_column(Integer, default=0)
    max_perclos: Mapped[float] = mapped_column(Float, default=0.0)
