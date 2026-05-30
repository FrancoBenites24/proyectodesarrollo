"""Tests unitarios para DrivingTimer."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.alarm.driving_timer import DrivingTimer


class TestDrivingTimer:
    def test_no_alert_before_warning(self):
        """No debe alertar antes de los 210 minutos."""
        timer = DrivingTimer()
        timer.start()
        with patch("src.alarm.driving_timer.time") as mock_time:
            mock_time.time.return_value = timer._start_time + 180 * 60
            assert timer.check() is None

    def test_warning_alert_at_210_minutes(self):
        """Debe alertar con warning a los 210 minutos."""
        timer = DrivingTimer()
        timer.start()
        start = timer._start_time
        with patch("src.alarm.driving_timer.time") as mock_time:
            mock_time.time.return_value = start + 210 * 60
            result = timer.check()
        assert result is not None
        assert "Te quedan" in result

    def test_critical_alert_at_240_minutes(self):
        """Debe alertar con mensaje crítico a las 4 horas."""
        timer = DrivingTimer()
        timer.start()
        start = timer._start_time
        with patch("src.alarm.driving_timer.time") as mock_time:
            mock_time.time.return_value = start + 240 * 60
            result = timer.check()
        assert result is not None
        assert "detente y descansa" in result.lower()

    def test_stop_resets_timer(self):
        """stop() debe reiniciar el timer."""
        timer = DrivingTimer()
        timer.start()
        timer.stop()
        assert timer.check() is None
        assert timer._start_time is None

    def test_elapsed_minutes_not_started(self):
        """elapsed_minutes debe ser 0.0 si no ha iniciado."""
        timer = DrivingTimer()
        assert timer.elapsed_minutes == 0.0

    def test_elapsed_minutes_after_start(self):
        """elapsed_minutes debe reflejar el tiempo transcurrido."""
        timer = DrivingTimer()
        timer.start()
        start = timer._start_time
        with patch("src.alarm.driving_timer.time") as mock_time:
            mock_time.time.return_value = start + 60 * 60
            assert abs(timer.elapsed_minutes - 60.0) < 0.01

    def test_check_returns_none_when_not_started(self):
        """check() debe retornar None si no fue iniciado."""
        timer = DrivingTimer()
        assert timer.check() is None

    def test_stop_and_restart(self):
        """Después de stop() y start(), el timer debe funcionar desde cero."""
        timer = DrivingTimer()
        timer.start()
        timer.stop()
        timer.start()
        assert timer._start_time is not None
        assert timer.check() is None
