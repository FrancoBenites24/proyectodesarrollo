"""Tests de integración para la API FastAPI."""
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_health_returns_200():
    assert client.get("/health").status_code == 200

def test_health_schema():
    data = client.get("/health").json()
    assert "status" in data
    assert "camera_connected" in data
    assert "uptime_seconds" in data

def test_metrics_returns_200():
    assert client.get("/metrics/").status_code == 200

def test_metrics_schema():
    data = client.get("/metrics/").json()
    for field in ["ear", "mor", "perclos", "alert_level", "fps"]:
        assert field in data

def test_stop_without_start_returns_409():
    assert client.post("/stream/stop").status_code == 409

def test_docs_available():
    assert client.get("/docs").status_code == 200
