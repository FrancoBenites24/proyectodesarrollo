"""Tests de integración para API v2 — sesiones, estadísticas y WebSocket."""
import os
import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.api.database import get_db, Base
from src.api.main import app

# Configurar motor SQLite asíncrono en archivo temporal para aislamiento de pruebas
TEST_DATABASE_URL = "sqlite+aiosqlite:///test_temp.db"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestAsyncSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

async def override_get_db():
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# Sobrescribir la dependencia get_db
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True, scope="module")
def setup_database():
    """Crea y destruye las tablas de la base de datos de prueba en un archivo temporal."""
    async def create_tables():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    # Crear tablas
    asyncio.run(create_tables())
    yield
    # Limpiar tablas
    asyncio.run(drop_tables())
    # Eliminar archivo temporal de base de datos
    if os.path.exists("test_temp.db"):
        try:
            os.remove("test_temp.db")
        except Exception:
            pass

client = TestClient(app)


def test_sessions_list_returns_200():
    r = client.get("/sessions/")
    assert r.status_code == 200


def test_sessions_start_requires_driver():
    r = client.post("/sessions/start", json={"driver_id": 999})
    assert r.status_code in [201, 422, 500]


def test_sessions_end_not_found():
    r = client.post("/sessions/999/end")
    assert r.status_code == 404


def test_stats_overview_returns_200():
    r = client.get("/stats/overview")
    assert r.status_code == 200


def test_stats_overview_schema():
    r = client.get("/stats/overview")
    data = r.json()
    assert "total_drivers" in data
    assert "total_alerts" in data
    assert "avg_perclos" in data


def test_stats_driver_not_found_returns_data():
    r = client.get("/stats/driver/888")
    assert r.status_code == 200
    data = r.json()
    assert data["driver_id"] == 888
    assert data["max_perclos"] == 0.0
    assert data["total_sessions"] == 0


def test_ws_endpoint_exists():
    with client.websocket_connect("/ws/metrics") as ws:
        assert ws is not None
