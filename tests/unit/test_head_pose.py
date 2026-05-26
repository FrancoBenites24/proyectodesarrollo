"""Tests unitarios para la estimación de orientación de la cabeza (Head Pose)."""

from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pytest

from src.core.head_pose import HeadPose, HeadPoseEstimator


class MockLandmark:
    def __init__(self, x: float, y: float, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z


class MockFaceLandmarks:
    def __init__(self, landmark_map: dict[int, tuple[float, float, float]]):
        self.landmark = [MockLandmark(0.0, 0.0, 0.0) for _ in range(500)]
        for idx, (x, y, z) in landmark_map.items():
            self.landmark[idx] = MockLandmark(x, y, z)


@pytest.fixture
def estimator() -> HeadPoseEstimator:
    return HeadPoseEstimator()


@pytest.fixture
def base_landmarks() -> MockFaceLandmarks:
    # Coordenadas dummy en rango 0.0-1.0
    return MockFaceLandmarks(
        {
            1: (0.5, 0.5, 0.0),  # nariz
            152: (0.5, 0.8, 0.0),  # barbilla
            263: (0.6, 0.4, 0.0),  # ojo izq
            33: (0.4, 0.4, 0.0),  # ojo der
            61: (0.45, 0.7, 0.0),  # boca izq
            291: (0.55, 0.7, 0.0),  # boca der
        }
    )


def test_estimate_returns_default_on_none_landmarks(estimator):
    """Debe retornar HeadPose por defecto si landmarks es None."""
    pose = estimator.estimate(None, 480, 480)
    assert isinstance(pose, HeadPose)
    assert pose.yaw == 0.0
    assert pose.pitch == 0.0
    assert pose.roll == 0.0
    assert pose.is_distracted is False
    assert pose.rvec is None
    assert pose.tvec is None


def test_estimate_straight_head(estimator, base_landmarks):
    """Prueba con rotación nula (cabeza recta)."""
    # rvec = [0, 0, 0], tvec = [0, 0, 100]
    rvec = np.zeros((3, 1), dtype="double")
    tvec = np.array([[0.0], [0.0], [100.0]], dtype="double")

    with patch("cv2.solvePnP", return_value=(True, rvec, tvec)):
        pose = estimator.estimate(base_landmarks, 640, 480)
        assert isinstance(pose, HeadPose)
        assert abs(pose.yaw) < 1e-3
        assert abs(pose.pitch) < 1e-3
        assert abs(pose.roll) < 1e-3
        assert pose.is_distracted is False
        assert np.array_equal(pose.rvec, rvec)
        assert np.array_equal(pose.tvec, tvec)


def test_estimate_distracted_by_yaw(estimator, base_landmarks):
    """Prueba distracción por yaw excesivo (rotación en Y)."""
    # 35 grados en radianes alrededor de Y (yaw = 35)
    yaw_rad = np.radians(35.0)
    # rvec para rotación sólo en Y
    rvec = np.array([[0.0], [yaw_rad], [0.0]], dtype="double")
    tvec = np.array([[0.0], [0.0], [100.0]], dtype="double")

    with patch("cv2.solvePnP", return_value=(True, rvec, tvec)):
        pose = estimator.estimate(base_landmarks, 640, 480)
        assert pose.is_distracted is True
        assert abs(pose.yaw - 35.0) < 1.0


def test_estimate_distracted_by_pitch(estimator, base_landmarks):
    """Prueba distracción por pitch excesivo (rotación en X)."""
    # 28 grados en radianes alrededor de X (pitch = 28)
    pitch_rad = np.radians(28.0)
    rvec = np.array([[pitch_rad], [0.0], [0.0]], dtype="double")
    tvec = np.array([[0.0], [0.0], [100.0]], dtype="double")

    with patch("cv2.solvePnP", return_value=(True, rvec, tvec)):
        pose = estimator.estimate(base_landmarks, 640, 480)
        assert pose.is_distracted is True
        assert abs(pose.pitch - 28.0) < 1.0


def test_estimate_distracted_by_roll(estimator, base_landmarks):
    """Prueba distracción por roll excesivo (rotación en Z)."""
    # 32 grados en radianes alrededor de Z (roll = 32)
    roll_rad = np.radians(32.0)
    rvec = np.array([[0.0], [0.0], [roll_rad]], dtype="double")
    tvec = np.array([[0.0], [0.0], [100.0]], dtype="double")

    with patch("cv2.solvePnP", return_value=(True, rvec, tvec)):
        pose = estimator.estimate(base_landmarks, 640, 480)
        assert pose.is_distracted is True
        assert abs(pose.roll - 32.0) < 1.0


def test_estimate_solve_pnp_fails(estimator, base_landmarks):
    """Debe retornar HeadPose por defecto si solvePnP falla."""
    with patch("cv2.solvePnP", return_value=(False, None, None)):
        pose = estimator.estimate(base_landmarks, 640, 480)
        assert pose.yaw == 0.0
        assert pose.is_distracted is False
