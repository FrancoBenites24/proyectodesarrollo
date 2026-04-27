"""Tests para DrowsinessDetector y FrameResult.

Todos los tests usan frames en blanco y mocks de FaceMeshWrapper
para no depender de Mediapipe ni de una webcam física.
Lo que se verifica es el contrato de la interfaz:
  - Retorna siempre FrameResult (nunca lanza excepción).
  - annotated_frame siempre es np.ndarray (nunca None).
  - EAR y MOR están en rangos válidos.
  - face_detected=False cuando no hay cara.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np

from src.core.detector import DEFAULT_KEYPOINTS, DrowsinessDetector, FrameResult


def make_blank_frame(h: int = 480, w: int = 480) -> np.ndarray:
    """Crea un frame en negro del tamaño indicado (sin cara)."""
    return np.zeros((h, w, 3), dtype=np.uint8)


def make_detector(return_landmarks=None, **kwargs):
    """Crea un DrowsinessDetector con FaceMeshWrapper mockeado.

    Args:
        return_landmarks: Valor que retorna mock.process().
                          None simula 'sin cara detectada'.
        **kwargs: Parámetros adicionales para DrowsinessDetector.
    """
    with patch("src.core.detector.FaceMeshWrapper") as MockFM:
        mock_fm = MagicMock()
        mock_fm.process.return_value = return_landmarks
        MockFM.return_value = mock_fm
        det = DrowsinessDetector(**kwargs)
    det._face_mesh = mock_fm
    return det


# ── FrameResult ────────────────────────────────────────────────────────────────


def test_frame_result_default_values():
    """FrameResult sin argumentos debe tener valores seguros por defecto."""
    r = FrameResult()
    assert r.ear == 0.0
    assert r.mor == 0.0
    assert r.eye_open is True
    assert r.yawning is False
    assert r.face_detected is False
    assert r.annotated_frame is None
    assert r.timestamp > 0


def test_frame_result_custom_fields():
    """FrameResult debe poder instanciarse con campos personalizados."""
    r = FrameResult(ear=0.15, mor=0.3, eye_open=False, face_detected=True)
    assert r.ear == 0.15
    assert r.mor == 0.3
    assert r.eye_open is False
    assert r.face_detected is True


# ── DrowsinessDetector — contrato de interfaz ─────────────────────────────────


def test_process_returns_frame_result():
    """process() debe retornar siempre una instancia de FrameResult."""
    det = make_detector()
    result = det.process(make_blank_frame())
    assert isinstance(result, FrameResult)


def test_no_face_returns_face_detected_false():
    """Sin landmarks, face_detected debe ser False."""
    det = make_detector(return_landmarks=None)
    result = det.process(make_blank_frame())
    assert result.face_detected is False


def test_annotated_frame_always_returned():
    """annotated_frame siempre debe ser np.ndarray, incluso sin cara."""
    det = make_detector()
    result = det.process(make_blank_frame())
    assert result.annotated_frame is not None
    assert isinstance(result.annotated_frame, np.ndarray)


def test_ear_zero_without_face():
    """Sin cara detectada, EAR debe quedar en 0.0 (valor por defecto)."""
    det = make_detector()
    result = det.process(make_blank_frame())
    assert result.ear == 0.0


def test_mor_zero_without_face():
    """Sin cara detectada, MOR debe quedar en 0.0 (valor por defecto)."""
    det = make_detector()
    result = det.process(make_blank_frame())
    assert result.mor == 0.0


def test_ear_within_valid_range():
    """EAR sin cara debe ser 0.0, que está en rango [0, 1]."""
    det = make_detector()
    result = det.process(make_blank_frame())
    assert 0.0 <= result.ear <= 1.0


def test_process_never_raises():
    """process() no debe lanzar excepción en ninguna ejecución."""
    det = make_detector()
    for _ in range(5):
        result = det.process(make_blank_frame())
        assert isinstance(result, FrameResult)


def test_custom_ear_threshold():
    """El detector debe aceptar umbrales de EAR personalizados."""
    det = make_detector(ear_threshold=0.20, mor_threshold=0.5)
    result = det.process(make_blank_frame())
    assert isinstance(result, FrameResult)


def test_custom_frame_size():
    """El detector debe aceptar tamaños de frame personalizados."""
    det = make_detector(frame_size=(320, 240))
    result = det.process(make_blank_frame(h=240, w=320))
    assert isinstance(result, FrameResult)


def test_annotated_frame_shape_matches_frame_size():
    """El frame anotado debe tener el tamaño configurado."""
    det = make_detector(frame_size=(320, 320))
    result = det.process(make_blank_frame())
    assert result.annotated_frame is not None
    assert result.annotated_frame.shape[0] == 320
    assert result.annotated_frame.shape[1] == 320


# ── Keypoints por defecto ─────────────────────────────────────────────────────


def test_default_keypoints_exist():
    """DEFAULT_KEYPOINTS debe tener las 4 claves requeridas."""
    for key in ("left_eye", "right_eye", "lips", "nose_to_chin"):
        assert key in DEFAULT_KEYPOINTS


def test_default_eye_keypoints_have_6_points():
    """Los landmarks de ojos deben tener exactamente 6 índices."""
    assert len(DEFAULT_KEYPOINTS["left_eye"]) == 6
    assert len(DEFAULT_KEYPOINTS["right_eye"]) == 6


def test_default_lips_keypoints_have_4_points():
    """Los landmarks de labios deben tener exactamente 4 índices."""
    assert len(DEFAULT_KEYPOINTS["lips"]) == 4
