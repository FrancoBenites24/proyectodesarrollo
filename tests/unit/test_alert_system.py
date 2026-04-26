"""Tests para AlertSystem."""
from unittest.mock import patch

import pytest

from src.alarm.alert_system import AlertSystem
from src.core.temporal import AlertLevel, TemporalState


def make_state(level: AlertLevel, perclos: float = 0.5):
    return TemporalState(
        perclos=perclos,
        alert_level=level,
        frames_in_window=90,
        closed_frames=int(90 * perclos),
    )


def test_none_level_does_not_trigger():
    system = AlertSystem()
    state = make_state(AlertLevel.NONE, perclos=0.0)
    with patch.object(system, "_play_sound_async") as mock_play:
        system.process(state)
        mock_play.assert_not_called()


def test_low_alert_triggers_sound():
    system = AlertSystem()
    state = make_state(AlertLevel.LOW, perclos=0.25)
    with patch.object(system, "_play_sound_async") as mock_play:
        system.process(state)
        mock_play.assert_called_once_with(AlertLevel.LOW)


def test_cooldown_prevents_rapid_repeat():
    system = AlertSystem()
    system.COOLDOWN_SECONDS = 10
    state = make_state(AlertLevel.HIGH, perclos=0.45)

    with patch.object(system, "_play_sound_async") as mock_play:
        system.process(state)
        system.process(state)
        assert mock_play.call_count == 1


def test_different_levels_independent_cooldowns():
    system = AlertSystem()
    state_low = make_state(AlertLevel.LOW, perclos=0.25)
    state_high = make_state(AlertLevel.HIGH, perclos=0.45)

    with patch.object(system, "_play_sound_async") as mock_play:
        system.process(state_low)
        system.process(state_high)
        assert mock_play.call_count == 2