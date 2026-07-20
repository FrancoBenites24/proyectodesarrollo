"""Endpoints para sesiones de conducción."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from src.api.database import get_db
from src.api.models.driving_session import DrivingSession
from src.api.models.alert_event import AlertEvent

router = APIRouter()


class SessionStart(BaseModel):
    driver_id: int


@router.post("/start", status_code=201)
async def start_session(body: SessionStart, db: AsyncSession = Depends(get_db)):
    """Inicia una sesión para un conductor."""
    session = DrivingSession(
        driver_id=body.driver_id,
        start_time=datetime.now(),
    )
    db.add(session)
    await db.flush()
    return {"id": session.id, "driver_id": session.driver_id, "start_time": session.start_time}


@router.post("/{session_id}/end", status_code=200)
async def end_session(session_id: int, db: AsyncSession = Depends(get_db)):
    """Finaliza una sesión."""
    session = await db.get(DrivingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    session.end_time = datetime.now()
    return {"id": session.id, "end_time": session.end_time}


@router.get("/")
async def list_sessions(
    driver_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Lista sesiones con filtro opcional por conductor."""
    query = select(DrivingSession).limit(limit).offset(offset)
    if driver_id:
        query = query.where(DrivingSession.driver_id == driver_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{session_id}")
async def get_session(session_id: int, db: AsyncSession = Depends(get_db)):
    """Detalle de una sesión con sus alertas."""
    session = await db.get(DrivingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    alerts = await db.execute(
        select(AlertEvent).where(AlertEvent.driver_id == session.driver_id)
    )
    return {"session": session, "alerts": alerts.scalars().all()}
