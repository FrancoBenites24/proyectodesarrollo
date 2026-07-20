"""WebSocket para métricas en tiempo real."""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

active_connections: list[WebSocket] = []


@router.websocket("/ws/metrics")
async def metrics_ws(websocket: WebSocket):
    """WebSocket que envía métricas en tiempo real a clientes conectados."""
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)


async def broadcast_metrics(metrics: dict) -> None:
    """Envía métricas a todos los clientes WebSocket conectados."""
    disconnected = []
    for ws in active_connections:
        try:
            await ws.send_json(metrics)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        active_connections.remove(ws)
