"""Captura de video en hilo separado para evitar bloqueos de procesamiento.

Sin threading el pipeline se ve así:
    Frame 1 → [Mediapipe 80ms] → Frame 2 → [Mediapipe 80ms] → ...

Con threading la captura corre siempre y el detector toma el frame más reciente:
    Hilo captura:    Frame 1 → Frame 2 → Frame 3 → Frame 4 ...
    Hilo detección:          [  80ms  ]           [  80ms  ]
"""

from __future__ import annotations

import threading
import time
from queue import Empty, Full, Queue

import cv2
import numpy as np

from src.utils.logger import get_logger

logger = get_logger(__name__)


class VideoStream:
    """Captura frames de webcam en un hilo dedicado.

    Uso básico:
        stream = VideoStream(source=0).start()
        frame = stream.read()
        stream.stop()

    Uso como context manager:
        with VideoStream(source=0) as stream:
            frame = stream.read()
    """

    def __init__(
        self,
        source: int | str = 0,
        buffer_size: int = 5,
    ) -> None:
        """Inicializa la captura de video.

        Args:
            source: Índice de cámara (int) o ruta de video (str).
            buffer_size: Tamaño máximo del buffer de frames.

        Raises:
            RuntimeError: Si la fuente de video no puede abrirse.
        """
        self._cap = cv2.VideoCapture(source)
        if not self._cap.isOpened():
            raise RuntimeError(
                f"No se puede abrir la fuente de video: {source}. "
                "Verifica que la webcam esté conectada."
            )

        self._queue: Queue[np.ndarray] = Queue(maxsize=buffer_size)
        self._thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
            name="VideoStream-capture",
        )
        self._running = False
        self._fps_counter = 0
        self._fps_start = time.time()

        logger.info(
            f"VideoStream inicializado | source={source} | buffer={buffer_size}"
        )

    def start(self) -> "VideoStream":
        """Inicia el hilo de captura.

        Returns:
            La misma instancia para permitir encadenamiento: VideoStream().start()
        """
        self._running = True
        self._thread.start()
        logger.info("Hilo de captura de video iniciado")
        return self

    def read(self, timeout: float = 1.0) -> np.ndarray | None:
        """Lee el frame más reciente disponible.

        Args:
            timeout: Segundos a esperar si no hay frames en el buffer.

        Returns:
            Frame como np.ndarray, o None si el buffer está vacío.
        """
        try:
            return self._queue.get(timeout=timeout)
        except Empty:
            logger.warning("VideoStream: sin frames disponibles (queue vacía)")
            return None

    def stop(self) -> None:
        """Detiene el hilo de captura y libera la cámara."""
        self._running = False
        self._thread.join(timeout=3.0)
        self._cap.release()
        logger.info("VideoStream detenido y cámara liberada")

    @property
    def is_running(self) -> bool:
        """True si el hilo de captura está activo."""
        return self._running and self._thread.is_alive()

    def _capture_loop(self) -> None:
        """Loop interno del hilo de captura (daemon thread).

        Descarta el frame más viejo si el buffer está lleno para garantizar
        que siempre se procese el frame más reciente (baja latencia).
        """
        while self._running:
            ret, frame = self._cap.read()

            if not ret:
                logger.error("VideoStream: fallo al leer frame de la fuente")
                self._running = False
                break

            # Si el buffer está lleno, descartar el frame más viejo
            if self._queue.full():
                try:
                    self._queue.get_nowait()
                except Empty:
                    pass

            try:
                self._queue.put_nowait(frame)
            except Full:
                pass  # El buffer se llenó de nuevo entre las dos llamadas — OK

            # Log de FPS cada 10 segundos
            self._fps_counter += 1
            elapsed = time.time() - self._fps_start
            if elapsed >= 10.0:
                fps = self._fps_counter / elapsed
                logger.debug(f"Captura FPS: {fps:.1f}")
                self._fps_counter = 0
                self._fps_start = time.time()

    def __enter__(self) -> "VideoStream":
        return self.start()

    def __exit__(self, *_) -> None:
        self.stop()
