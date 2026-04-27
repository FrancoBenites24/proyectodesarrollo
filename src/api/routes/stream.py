"""Control del stream de video."""

from fastapi import APIRouter, HTTPException

from src.api.schemas import StreamStartRequest
from src.api.state import app_state

router = APIRouter()


@router.post("/start", status_code=200)
async def start_stream(body: StreamStartRequest):
    if app_state.is_running:
        raise HTTPException(
            status_code=409, detail="El stream ya está corriendo"
        )
    await app_state.start(source=body.source)
    return {"status": "started", "source": body.source}


@router.post("/stop", status_code=200)
async def stop_stream():
    if not app_state.is_running:
        raise HTTPException(
            status_code=409, detail="El stream no está corriendo"
        )
    await app_state.stop()
    return {"status": "stopped"}
