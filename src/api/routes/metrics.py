"""Endpoint de métricas en tiempo real."""

from fastapi import APIRouter

from src.api.schemas import DrowsinessMetrics
from src.api.state import app_state

router = APIRouter()


@router.get("/", response_model=DrowsinessMetrics)
async def get_metrics() -> DrowsinessMetrics:
    return app_state.last_metrics
