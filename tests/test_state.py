import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.api.state import AppState

@pytest.fixture
def app_state():
    return AppState()

@pytest.mark.asyncio
async def test_app_state_start_success(app_state):
    """Prueba que el stream inicie correctamente."""
    with patch("src.api.state.VideoStream") as mock_vs_class, \
         patch("src.api.state.DrivingTimer") as mock_timer_class:
        
        # Simular el retorno de VideoStream().start()
        mock_vs_instance = MagicMock()
        mock_vs_class.return_value.start.return_value = mock_vs_instance
        
        await app_state.start(source=0)
        
        assert app_state.is_running is True
        assert app_state.camera_connected is True
        assert app_state._task is not None
        mock_vs_class.return_value.start.assert_called_once()
        
        # Limpieza
        await app_state.stop()

@pytest.mark.asyncio
async def test_app_state_stop(app_state):
    """Prueba que el stream y las tareas se detengan limpiamente."""
    with patch("src.api.state.VideoStream") as mock_vs_class:
        mock_vs_instance = MagicMock()
        mock_vs_class.return_value.start.return_value = mock_vs_instance
        
        await app_state.start(source=0)
        await app_state.stop()
        
        assert app_state.is_running is False
        assert app_state.camera_connected is False
        assert app_state._stream is None
        mock_vs_instance.stop.assert_called_once()

@pytest.mark.asyncio
async def test_app_state_start_failure(app_state):
    """Prueba el manejo de errores si la cámara falla al iniciar."""
    with patch("src.api.state.VideoStream") as mock_vs_class:
        # Simular un error al acceder a la cámara
        mock_vs_class.return_value.start.side_effect = RuntimeError("Mock error: Cámara no encontrada")
        
        with pytest.raises(RuntimeError):
            await app_state.start(source=0)
            
        assert app_state.is_running is False
        assert app_state.camera_connected is False