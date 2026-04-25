"""Tests para VideoStream.

Todos los tests usan mocks de cv2.VideoCapture para no depender
de una webcam física. Se verifica el contrato de la interfaz:
  - RuntimeError si la fuente no puede abrirse.
  - start() retorna self (fluent interface).
  - read() retorna None (nunca lanza excepción) si no hay frames.
  - El context manager llama a stop() al salir.
  - stop() siempre libera la cámara.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


def _make_mock_cap(opened: bool = True, frame: np.ndarray = None):
    """Crea un mock de cv2.VideoCapture."""
    mock = MagicMock()
    mock.isOpened.return_value = opened
    if frame is None:
        frame = np.zeros((480, 480, 3), dtype=np.uint8)
    mock.read.return_value = (True, frame)
    return mock


# ── Inicialización ─────────────────────────────────────────────────────────────


def test_raises_runtime_error_on_invalid_source():
    """Debe lanzar RuntimeError si la fuente de video no puede abrirse."""
    with patch("src.core.video_stream.cv2.VideoCapture") as MockCap:
        MockCap.return_value = _make_mock_cap(opened=False)
        from src.core.video_stream import VideoStream

        with pytest.raises(RuntimeError, match="No se puede abrir"):
            VideoStream(source=99)


def test_no_error_on_valid_source():
    """No debe lanzar excepción si la fuente es válida."""
    with patch("src.core.video_stream.cv2.VideoCapture") as MockCap:
        MockCap.return_value = _make_mock_cap(opened=True)
        from src.core.video_stream import VideoStream

        vs = VideoStream(source=0)
        assert vs is not None


# ── start / stop ──────────────────────────────────────────────────────────────


def test_start_returns_self():
    """start() debe retornar la misma instancia (fluent interface)."""
    with patch("src.core.video_stream.cv2.VideoCapture") as MockCap:
        MockCap.return_value = _make_mock_cap()
        from src.core.video_stream import VideoStream

        vs = VideoStream(source=0)
        result = vs.start()
        assert result is vs
        vs.stop()


def test_is_running_true_after_start():
    """is_running debe ser True después de start()."""
    with patch("src.core.video_stream.cv2.VideoCapture") as MockCap:
        MockCap.return_value = _make_mock_cap()
        from src.core.video_stream import VideoStream

        vs = VideoStream(source=0).start()
        time.sleep(0.05)
        assert vs.is_running is True
        vs.stop()


def test_is_running_false_after_stop():
    """is_running debe ser False después de stop()."""
    with patch("src.core.video_stream.cv2.VideoCapture") as MockCap:
        MockCap.return_value = _make_mock_cap()
        from src.core.video_stream import VideoStream

        vs = VideoStream(source=0).start()
        vs.stop()
        assert vs.is_running is False


def test_stop_releases_camera():
    """stop() debe llamar a cap.release()."""
    with patch("src.core.video_stream.cv2.VideoCapture") as MockCap:
        mock_cap = _make_mock_cap()
        MockCap.return_value = mock_cap
        from src.core.video_stream import VideoStream

        vs = VideoStream(source=0).start()
        vs.stop()
        mock_cap.release.assert_called_once()


# ── read ──────────────────────────────────────────────────────────────────────


def test_read_returns_frame_when_running():
    """read() debe retornar un np.ndarray si el stream está activo."""
    with patch("src.core.video_stream.cv2.VideoCapture") as MockCap:
        MockCap.return_value = _make_mock_cap()
        from src.core.video_stream import VideoStream

        vs = VideoStream(source=0).start()
        time.sleep(0.1)  # Tiempo para que el hilo ponga frames en la queue
        frame = vs.read(timeout=1.0)
        vs.stop()
        assert frame is not None
        assert isinstance(frame, np.ndarray)


def test_read_returns_none_without_frames():
    """read() con timeout corto debe retornar None si no hay frames."""
    with patch("src.core.video_stream.cv2.VideoCapture") as MockCap:
        # Simulamos que read() siempre falla — el hilo se detiene
        mock_cap = _make_mock_cap()
        mock_cap.read.return_value = (False, None)
        MockCap.return_value = mock_cap
        from src.core.video_stream import VideoStream

        vs = VideoStream(source=0)
        # No iniciamos el hilo — la queue estará vacía
        result = vs.read(timeout=0.05)
        assert result is None


# ── Context manager ───────────────────────────────────────────────────────────


def test_context_manager_starts_stream():
    """El context manager debe iniciar el stream al entrar."""
    with patch("src.core.video_stream.cv2.VideoCapture") as MockCap:
        MockCap.return_value = _make_mock_cap()
        from src.core.video_stream import VideoStream

        with VideoStream(source=0) as vs:
            time.sleep(0.05)
            assert vs.is_running is True


def test_context_manager_stops_on_exit():
    """El context manager debe llamar a stop() al salir del bloque."""
    with patch("src.core.video_stream.cv2.VideoCapture") as MockCap:
        MockCap.return_value = _make_mock_cap()
        from src.core.video_stream import VideoStream

        with VideoStream(source=0) as vs:
            pass
        assert vs.is_running is False


def test_context_manager_releases_camera():
    """El context manager debe liberar la cámara al salir."""
    with patch("src.core.video_stream.cv2.VideoCapture") as MockCap:
        mock_cap = _make_mock_cap()
        MockCap.return_value = mock_cap
        from src.core.video_stream import VideoStream

        with VideoStream(source=0):
            pass
        mock_cap.release.assert_called_once()
