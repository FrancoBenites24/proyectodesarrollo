"""Aplicación FastAPI principal."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.api.database import engine, Base
from src.api.routes import health, metrics, stream
from src.api.routes import drivers, alerts
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

app.mount("/static", StaticFiles(directory="src/static"), name="static")
templates = Jinja2Templates(directory="src/templates")


@app.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
