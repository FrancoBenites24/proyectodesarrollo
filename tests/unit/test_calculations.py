"""Tests para Calculator.

Verifica que los cálculos geométricos sean correctos y que
los casos borde (puntos inválidos, divisiones por cero) se manejen
retornando None o 0.0 en lugar de lanzar excepciones.
"""

from __future__ import annotations

import math

import pytest

from src.utils.calculations import Calculator

calc = Calculator()


# ── distance ──────────────────────────────────────────────────────────────────


def test_distance_known_points():
    """Distancia 3-4-5: distancia entre (0,0) y (3,4) debe ser 5.0."""
    assert calc.distance((0, 0), (3, 4)) == pytest.approx(5.0)


def test_distance_same_point():
    """Distancia entre el mismo punto debe ser 0."""
    assert calc.distance((5, 5), (5, 5)) == pytest.approx(0.0)


def test_distance_horizontal():
    """Distancia horizontal pura."""
    assert calc.distance((0, 0), (10, 0)) == pytest.approx(10.0)


# ── midpoint ──────────────────────────────────────────────────────────────────


def test_midpoint_basic():
    """Punto medio entre (0,0) y (4,4) debe ser (2,2)."""
    assert calc.midpoint((0, 0), (4, 4)) == (2, 2)


def test_midpoint_asymmetric():
    """Punto medio con coordenadas asimétricas."""
    assert calc.midpoint((1, 3), (5, 7)) == (3, 5)


# ── ear ───────────────────────────────────────────────────────────────────────


def test_ear_returns_none_for_wrong_point_count():
    """EAR con menos de 6 puntos debe retornar None."""
    assert calc.ear(((0, 0), (1, 1), (2, 2))) is None


def test_ear_returns_none_for_zero_horizontal_distance():
    """EAR con distancia horizontal = 0 debe retornar None (evita división por cero)."""
    p = (0, 0)
    assert calc.ear((p, p, p, p, p, p)) is None


def test_ear_valid_returns_float():
    """EAR con puntos válidos debe retornar un float positivo."""
    points = ((0, 0), (1, 2), (2, 2), (4, 0), (3, 2), (2, -1))
    result = calc.ear(points)
    assert result is not None
    assert isinstance(result, float)
    assert result > 0


def test_ear_open_eye_above_threshold():
    """Ojos muy abiertos deben producir EAR > 0.25."""
    # Ojo con altura máxima: puntos verticales muy separados
    left = (0, 0)
    right = (6, 0)
    top1 = (1, 4)
    top2 = (5, 4)
    bot1 = (1, -4)
    bot2 = (5, -4)
    result = calc.ear((left, top1, top2, right, bot2, bot1))
    assert result is not None
    assert result > 0.25


# ── mor ───────────────────────────────────────────────────────────────────────


def test_mor_returns_zero_for_wrong_point_count():
    """MOR con cantidad incorrecta de puntos debe retornar 0.0."""
    assert calc.mor(((0, 0), (1, 1))) == 0.0


def test_mor_returns_zero_for_zero_width():
    """MOR con ancho = 0 debe retornar 0.0 (evita división por cero)."""
    p = (0, 0)
    assert calc.mor((p, p, p, p)) == 0.0


def test_mor_closed_mouth():
    """Boca cerrada: altura ~ 0 → MOR cercano a 0."""
    result = calc.mor(((0, 0), (2, 0), (4, 0), (2, 0)))
    assert result == pytest.approx(0.0)


def test_mor_open_mouth():
    """Boca abierta: altura grande → MOR > 0."""
    # ancho = 4, altura = 2 → MOR = 0.5
    result = calc.mor(((0, 0), (2, 2), (4, 0), (2, -2)))
    assert result == pytest.approx(1.0)


# ── check_intersection ────────────────────────────────────────────────────────


def test_intersection_crossing_lines():
    """Dos líneas en cruz deben intersectarse."""
    line1 = ((0, 1), (2, 1))
    line2 = ((1, 0), (1, 2))
    assert calc.check_intersection(line1, line2) is True


def test_no_intersection_parallel_lines():
    """Líneas paralelas no deben intersectarse."""
    line1 = ((0, 0), (2, 0))
    line2 = ((0, 1), (2, 1))
    assert calc.check_intersection(line1, line2) is False
