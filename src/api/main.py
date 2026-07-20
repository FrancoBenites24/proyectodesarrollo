"""Aplicación FastAPI principal."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.database import engine, Base
from src.api.routes import health, metrics, stream, drivers, alerts
from src.api.routes import sessions, stats, ws
from src.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("DrowsyGuard API iniciando")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    logger.info("DrowsyGuard API deteniendo")


app = FastAPI(
    title="DrowsyGuard API",
    description="Sistema de detección de somnolencia en tiempo real",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(stream.router, prefix="/stream", tags=["Stream"])
app.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])
app.include_router(drivers.router, prefix="/drivers", tags=["Drivers"])
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
app.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
app.include_router(stats.router, prefix="/stats", tags=["Stats"])
app.include_router(ws.router, tags=["WebSocket"])
