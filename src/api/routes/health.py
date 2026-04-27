"""Endpoint de salud."""

import time

from fastapi import APIRouter

from src.api.schemas import SystemHealth
from src.api.state import app_state

router = APIRouter()


@router.get("/health", response_model=SystemHealth)
async def health_check() -> SystemHealth:
    return SystemHealth(
        status="ok" if app_state.camera_connected else "degraded",
        camera_connected=app_state.camera_connected,
        uptime_seconds=round(time.time() - app_state.start_time, 1),
    )
