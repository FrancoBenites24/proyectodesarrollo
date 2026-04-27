"""Endpoint de métricas en tiempo real."""
from fastapi import APIRouter
from src.api.schemas import DrownsinessMetrics
from src.api.state import app_state

router = APIRouter()


@router.get("/", response_model=DrownsinessMetrics)
async def get_metrics() -> DrownsinessMetrics:
    return app_state.last_metrics
