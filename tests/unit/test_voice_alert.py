"""Tests para VoiceAlertSystem."""

from unittest.mock import MagicMock, patch

import pytest

from src.alarm.voice_alert import VoiceAlertSystem
from src.core.temporal import AlertLevel, TemporalState


@pytest.fixture
def voice_system():
    with patch("src.alarm.voice_alert.VoiceEngine") as mock_engine:
        system = VoiceAlertSystem()
        system._voice = mock_engine.return_value
        yield system


def test_inherits_alert_system(voice_system):
    """VoiceAlertSystem hereda de AlertSystem."""
    from src.alarm.alert_system import AlertSystem
    assert isinstance(voice_system, AlertSystem)


def test_play_sound_calls_speak(voice_system):
    """_play_sound debe llamar a voice.speak con el mensaje correcto."""
    voice_system._play_sound(AlertLevel.HIGH)
    voice_system._voice.speak.assert_called_once()
    args = voice_system._voice.speak.call_args[0][0]
    assert "fatiga" in args.lower()


def test_play_sound_critical_message(voice_system):
    """Nivel CRITICAL debe mencionar 'alerta crítica'."""
    voice_system._play_sound(AlertLevel.CRITICAL)
    args = voice_system._voice.speak.call_args[0][0]
    assert "crítica" in args.lower()


def test_none_level_not_spoken(voice_system):
    """Nivel NONE no debe generar voz."""
    voice_system._play_sound(AlertLevel.NONE)
    voice_system._voice.speak.assert_not_called()