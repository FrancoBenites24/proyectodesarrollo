"""Estado global compartido entre endpoints (singleton)."""

from __future__ import annotations

import asyncio
import time
from typing import Optional

import cv2

from src.alarm.alert_system import AlertSystem
from src.api.schemas import AlertLevelSchema, DrowsinessMetrics
from src.core.detector import DrowsinessDetector
from src.core.temporal import TemporalAnalyzer
from src.core.video_stream import VideoStream
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AppState:
    def __init__(self) -> None:
        self.start_time = time.time()
        self.is_running = False
        self.camera_connected = False
        self.last_metrics = DrowsinessMetrics(
            ear=0.0,
            mor=0.0,
            perclos=0.0,
            alert_level=AlertLevelSchema.NONE,
            face_detected=False,
            fps=0.0,
            timestamp=time.time(),
        )
        self.last_frame: Optional[bytes] = None
        self._task: Optional[asyncio.Task] = None
        self._stream: Optional[VideoStream] = None

    async def start(self, source: int | str = 0) -> None:
        try:
            self._stream = VideoStream(source=source).start()
            self.camera_connected = True
            self.is_running = True
            self._task = asyncio.create_task(self._detection_loop())
            logger.info(f"Detección iniciada | source={source}")
        except RuntimeError:
            logger.exception("No se pudo iniciar el stream de video")
            raise

    async def stop(self) -> None:
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._stream:
            self._stream.stop()
        self.camera_connected = False
        logger.info("Detección detenida")

    async def _detection_loop(self) -> None:
        detector = DrowsinessDetector()
        analyzer = TemporalAnalyzer()
        alert_system = AlertSystem()

        frame_count = 0
        t0 = time.time()

        while self.is_running:
            frame = self._stream.read(timeout=0.1)
            if frame is None:
                await asyncio.sleep(0.01)
                continue

            result = detector.process(frame)
            state = analyzer.update(result.eye_open)
            alert_system.process(state)

            frame_count += 1
            fps = frame_count / max(time.time() - t0, 1e-6)

            # Guardar el frame anotado para el stream de video
            out_frame = (
                result.annotated_frame if result.annotated_frame is not None else frame
            )
            _, buffer = cv2.imencode(".jpg", out_frame)
            self.last_frame = buffer.tobytes()

            self.last_metrics = DrowsinessMetrics(
                ear=result.ear,
                mor=result.mor,
                perclos=state.perclos,
                alert_level=AlertLevelSchema(int(state.alert_level)),
                face_detected=result.face_detected,
                fps=round(fps, 1),
                timestamp=result.timestamp,
            )
            await asyncio.sleep(0)


app_state = AppState()
