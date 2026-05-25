"""Endpoints para historial de alertas."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_db
from src.api.models.alert_event import AlertEvent

router = APIRouter()


@router.get("/")
async def list_alerts(
    driver_id: int | None = None, limit: int = 50, db: AsyncSession = Depends(get_db)
):
    """Listar alertas con filtro opcional por conductor."""
    query = select(AlertEvent).limit(limit)
    if driver_id:
        query = query.where(AlertEvent.driver_id == driver_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats")
async def alert_stats(db: AsyncSession = Depends(get_db)):
    """Estadísticas de alertas por tipo y conductor."""
    result = await db.execute(
        select(
            AlertEvent.alert_level,
            AlertEvent.event_type,
            func.count(AlertEvent.id).label("total"),
        ).group_by(AlertEvent.alert_level, AlertEvent.event_type)
    )
    rows = result.all()
    return [{"alert_level": r[0], "event_type": r[1], "total": r[2]} for r in rows]
