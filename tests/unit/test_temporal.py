"""Tests para TemporalAnalyzer y AlertLevel."""

import pytest

from src.core.temporal import AlertLevel, TemporalAnalyzer


def test_empty_buffer_returns_none_level():
    ta = TemporalAnalyzer(window_seconds=1, fps=10)
    assert ta.state.alert_level == AlertLevel.NONE
    assert ta.state.perclos == 0.0


def test_all_open_eyes_no_alert():
    ta = TemporalAnalyzer(window_seconds=1, fps=10)
    for _ in range(10):
        ta.update(eye_open=True)
    assert ta.state.perclos == 0.0
    assert ta.state.alert_level == AlertLevel.NONE


def test_30_percent_closed_triggers_low():
    ta = TemporalAnalyzer(window_seconds=1, fps=10)
    # 3 cerrados, 7 abiertos = 30% PERCLOS
    for i in range(10):
        ta.update(eye_open=(i >= 3))
    assert ta.state.perclos == pytest.approx(0.3)
    assert ta.state.alert_level == AlertLevel.LOW


def test_50_percent_closed_triggers_high():
    ta = TemporalAnalyzer(window_seconds=1, fps=10)
    for i in range(10):
        ta.update(eye_open=(i >= 5))
    assert ta.state.alert_level == AlertLevel.HIGH


def test_70_percent_closed_triggers_critical():
    ta = TemporalAnalyzer(window_seconds=1, fps=10)
    for i in range(10):
        ta.update(eye_open=(i >= 7))
    assert ta.state.alert_level == AlertLevel.CRITICAL


def test_window_slides_out_old_frames():
    ta = TemporalAnalyzer(window_seconds=1, fps=5)
    # Llena la ventana con ojos cerrados
    for _ in range(5):
        ta.update(eye_open=False)
    assert ta.state.perclos == 1.0
    # Agrega frame abierto — el más viejo (cerrado) sale
    ta.update(eye_open=True)
    assert ta.state.perclos < 1.0


def test_reset_clears_buffer():
    ta = TemporalAnalyzer(window_seconds=1, fps=5)
    for _ in range(5):
        ta.update(eye_open=False)
    ta.reset()
    assert ta.state.frames_in_window == 0
