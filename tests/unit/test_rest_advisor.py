"""Tests unitarios para RestAdvisor."""

from __future__ import annotations

import pytest

from src.alarm.rest_advisor import RestAdvisor, RestStop


class TestRestAdvisor:
    def test_suggest_returns_correct_count(self):
        """suggest() debe retornar el número solicitado."""
        advisor = RestAdvisor()
        stops = advisor.suggest(count=2)
        assert len(stops) == 2

    def test_suggest_returns_max_available(self):
        """suggest() no retorna más de las disponibles."""
        advisor = RestAdvisor()
        total = len(advisor._SIMULATED_STOPS)
        stops = advisor.suggest(count=total + 10)
        assert len(stops) == total

    def test_suggest_sorted_by_distance(self):
        """Las paradas deben estar ordenadas por distancia."""
        advisor = RestAdvisor()
        stops = advisor.suggest(count=3)
        distances = [s.distance_km for s in stops]
        assert distances == sorted(distances)

    def test_suggest_returns_rest_stop_instances(self):
        """suggest() debe retornar instancias de RestStop."""
        advisor = RestAdvisor()
        stops = advisor.suggest(count=1)
        assert isinstance(stops[0], RestStop)

    def test_format_suggestion_returns_string(self):
        """format_suggestion() debe retornar un string no vacío."""
        advisor = RestAdvisor()
        result = advisor.format_suggestion()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_format_suggestion_contains_distance(self):
        """format_suggestion() debe mencionar kilómetros o lugar seguro."""
        advisor = RestAdvisor()
        result = advisor.format_suggestion()
        assert "kilómetros" in result or "seguro" in result

    def test_rest_stop_is_frozen(self):
        """RestStop debe ser inmutable."""
        stop = RestStop(name="Test", type="gasolinera", distance_km=1.0)
        with pytest.raises(Exception):
            stop.name = "Otro"  # type: ignore[misc]
