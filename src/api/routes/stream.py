"""Control del stream de video."""

import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from src.api.schemas import StreamStartRequest
from src.api.state import app_state

router = APIRouter()


@router.get("/video")
async def video_feed():
    async def frame_generator():
        while True:
            if app_state.last_frame:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + app_state.last_frame + b"\r\n"
                )
            await asyncio.sleep(0.03)  # ~30 FPS

    return StreamingResponse(
        frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.post("/start", status_code=200)
async def start_stream(body: StreamStartRequest):
    if app_state.is_running:
        raise HTTPException(status_code=409, detail="El stream ya está corriendo")
    await app_state.start(source=body.source)
    return {"status": "started", "source": body.source}


@router.post("/stop", status_code=200)
async def stop_stream():
    if not app_state.is_running:
        raise HTTPException(status_code=409, detail="El stream no está corriendo")
    await app_state.stop()
    return {"status": "stopped"}
