import pytest
import numpy as np
from unittest.mock import MagicMock
from src.utils.drawing import Drawer
from src.core.head_pose import HeadPose

@pytest.fixture
def drawer():
    return Drawer()

def test_drawer_annotate_returns_valid_frame(drawer):
    """Asegura que el Drawer puede anotar un frame sin lanzar excepciones."""
    # Simular un frame de video vacío (negro) de 480x480 RGB
    mock_frame = np.zeros((480, 480, 3), dtype=np.uint8)
    
    # Coordenadas dummy para los landmarks
    dummy_points = [(10, 10), (20, 20)]
    mock_head_pose = HeadPose(yaw=0.0, pitch=0.0, roll=0.0, is_distracted=False)
    
    # Ejecutar la función
    result = drawer.annotate(
        frame=mock_frame.copy(),
        left_eye=dummy_points,
        right_eye=dummy_points,
        lips=dummy_points,
        ear=0.35,
        mor=0.15,
        eye_open=True,
        phone_detected=False,
        left_eyebrow=dummy_points,
        right_eyebrow=dummy_points,
        left_iris=dummy_points,
        right_iris=dummy_points,
        head_pose=mock_head_pose
    )
    
    # Verificaciones
    assert isinstance(result, np.ndarray), "El resultado debe ser un numpy array (imagen)"
    assert result.shape == mock_frame.shape, "La resolución del frame no debe verse alterada"
    assert result.dtype == np.uint8, "El tipo de dato de la imagen debe mantenerse en uint8"

def test_drawer_annotate_alert_states(drawer):
    """Verifica el comportamiento cuando hay distracciones o teléfono detectado."""
    mock_frame = np.zeros((480, 480, 3), dtype=np.uint8)
    dummy_points = [(10, 10)]
    
    result = drawer.annotate(
        frame=mock_frame.copy(),
        left_eye=dummy_points,
        right_eye=dummy_points,
        lips=dummy_points,
        ear=0.1,  # Ojos cerrados
        mor=0.8,  # Bostezando
        eye_open=False,
        phone_detected=True,  # Teléfono
        left_eyebrow=dummy_points,
        right_eyebrow=dummy_points,
        left_iris=dummy_points,
        right_iris=dummy_points,
        head_pose=HeadPose(is_distracted=True) # Distracción
    )
    
    assert isinstance(result, np.ndarray)