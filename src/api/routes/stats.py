"""Endpoints de estadísticas para el panel admin."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_db
from src.api.models.driver import Driver
from src.api.models.alert_event import AlertEvent
from src.api.models.driving_session import DrivingSession

router = APIRouter()


@router.get("/overview")
async def stats_overview(db: AsyncSession = Depends(get_db)):
    """Resumen global del sistema."""
    total_drivers = await db.execute(select(func.count(Driver.id)))
    total_alerts = await db.execute(select(func.count(AlertEvent.id)))
    avg_perclos = await db.execute(select(func.avg(AlertEvent.perclos)))

    return {
        "total_drivers": total_drivers.scalar() or 0,
        "total_alerts": total_alerts.scalar() or 0,
        "avg_perclos": round(avg_perclos.scalar() or 0.0, 3),
    }


@router.get("/driver/{driver_id}")
async def stats_by_driver(driver_id: int, db: AsyncSession = Depends(get_db)):
    """Estadísticas por conductor."""
    alerts_by_type = await db.execute(
        select(AlertEvent.event_type, func.count(AlertEvent.id).label("total"))
        .where(AlertEvent.driver_id == driver_id)
        .group_by(AlertEvent.event_type)
    )
    max_perclos = await db.execute(
        select(func.max(AlertEvent.perclos))
        .where(AlertEvent.driver_id == driver_id)
    )
    total_sessions = await db.execute(
        select(func.count(DrivingSession.id))
        .where(DrivingSession.driver_id == driver_id)
    )

    return {
        "driver_id": driver_id,
        "alerts_by_type": [{"type": r[0], "total": r[1]} for r in alerts_by_type.all()],
        "max_perclos": max_perclos.scalar() or 0.0,
        "total_sessions": total_sessions.scalar() or 0,
    }
