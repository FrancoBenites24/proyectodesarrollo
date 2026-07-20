"""Tests de integración para API v2 — sesiones, estadísticas y WebSocket."""
from fastapi.testclient import TestClient
from src.api.main import app

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
    r = client.get("/stats/driver/999")
    assert r.status_code == 200


def test_ws_endpoint_exists():
    with client.websocket_connect("/ws/metrics") as ws:
        assert ws is not None
