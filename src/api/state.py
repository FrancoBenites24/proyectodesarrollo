"""Estado global compartido entre endpoints (singleton)."""

from __future__ import annotations

import asyncio
import os
import time

import cv2

from src.alarm.driving_timer import DrivingTimer
from src.api.database import AsyncSessionLocal
from src.api.models.alert_event import AlertEvent
from src.api.schemas import AlertLevelSchema, DrowsinessMetrics
from src.core.detector import DrowsinessDetector
from src.core.event_classifier import classify_event
from src.core.temporal import TemporalAnalyzer, TemporalState
from src.core.video_stream import VideoStream
from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_alert_system():
    """Retorna el sistema de alerta configurado (voz o básico)."""

    use_voice = os.getenv("ALERT_MODE", "voice") == "voice"

    if use_voice:
        from src.alarm.voice_alert import VoiceAlertSystem

        return VoiceAlertSystem()

    from src.alarm.alert_system import AlertSystem

    return AlertSystem()


class AppState:
    def __init__(self) -> None:
        self.start_time = time.time()
        self.is_running = False
        self.camera_connected = False
        self.driving_timer = DrivingTimer()
        self.last_metrics = DrowsinessMetrics(
            ear=0.0,
            mor=0.0,
            perclos=0.0,
            alert_level=AlertLevelSchema.NONE,
            phone_detected=False,
            is_distracted=False,
            head_yaw=0.0,
            head_pitch=0.0,
            yawning=False,
            driving_minutes=0.0,
            face_detected=False,
            fps=0.0,
            timestamp=time.time(),
        )

        self.last_frame: bytes | None = None
        self._task: asyncio.Task | None = None
        self._stream: VideoStream | None = None

    async def start(self, source: int | str = 0) -> None:
        try:
            self._stream = VideoStream(source=source).start()
            self.driving_timer.start()
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
            except Exception as e:
                logger.error(f"Error esperando a la tarea de detección al detener: {e}")

        if self._stream:
            try:
                self._stream.stop()
            except Exception as e:
                logger.error(f"Error liberando el VideoStream: {e}")
            self._stream = None
        self.driving_timer.stop()
        self.camera_connected = False

        logger.info("Detección detenida")

    async def _save_alert(
        self,
        event_type: str,
        state: TemporalState,
        result,
    ) -> None:
        """
        Guarda una alerta en la base de datos.
        """

        try:
            async with AsyncSessionLocal() as session:

                alert = AlertEvent(
                    driver_id=1,
                    alert_level=state.alert_level.name,
                    event_type=event_type,
                    perclos=state.perclos,
                    ear=result.ear,
                    mor=result.mor,
                )

                session.add(alert)

                await session.commit()

        except Exception:
            logger.exception("Error guardando alerta")

    async def _detection_loop(self) -> None:

        detector = DrowsinessDetector()

        analyzer = TemporalAnalyzer()

        alert_system = get_alert_system()

        frame_count = 0
        t0 = time.time()

        while self.is_running:

            frame = self._stream.read(timeout=0.1)

            if frame is None:
                await asyncio.sleep(0.01)
                continue

            # --------------------------------------------------
            # 1. Detector
            # --------------------------------------------------

            result = detector.process(frame)

            # --------------------------------------------------
            # 2. Temporal
            # --------------------------------------------------

            temporal_state = analyzer.update(result.eye_open)

            # --------------------------------------------------
            # 3. Clasificación de eventos
            # --------------------------------------------------

            events = classify_event(
                result,
                temporal_state,
            )

            state = TemporalState(
                perclos=temporal_state.perclos,
                alert_level=temporal_state.alert_level,
                frames_in_window=temporal_state.frames_in_window,
                closed_frames=temporal_state.closed_frames,
                event_types=tuple(events),
            )

            # --------------------------------------------------
            # 4. Alertas
            # --------------------------------------------------

            if hasattr(alert_system, "process_extended"):
                alert_system.process_extended(
                    state,
                    result,
                    self.driving_timer,
                )
            else:
                alert_system.process(state)

            # --------------------------------------------------
            # 5. Persistencia BD
            # --------------------------------------------------

            for event in events:
                await self._save_alert(
                    event,
                    state,
                    result,
                )

            # --------------------------------------------------
            # 6. FPS
            # --------------------------------------------------

            frame_count += 1

            fps = frame_count / max(
                time.time() - t0,
                1e-6,
            )

            # --------------------------------------------------
            # 7. Frame para streaming
            # --------------------------------------------------

            out_frame = (
                result.annotated_frame if result.annotated_frame is not None else frame
            )

            _, buffer = cv2.imencode(
                ".jpg",
                out_frame,
            )

            self.last_frame = buffer.tobytes()

            # --------------------------------------------------
            # 8. Métricas API
            # --------------------------------------------------

            self.last_metrics = DrowsinessMetrics(
                ear=result.ear,
                mor=result.mor,
                perclos=state.perclos,
                alert_level=AlertLevelSchema(int(state.alert_level)),
                phone_detected=result.phone_detected,
                is_distracted=result.is_distracted,
                head_yaw=result.head_yaw,
                head_pitch=result.head_pitch,
                yawning=result.yawning,
                driving_minutes=round(
                    self.driving_timer.elapsed_minutes,
                    1,
                ),
                face_detected=result.face_detected,
                fps=round(fps, 1),
                timestamp=result.timestamp,
            )

            await asyncio.sleep(0)


app_state = AppState()
