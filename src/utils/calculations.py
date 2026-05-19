"""Cálculos geométricos para detección facial: EAR, MOR, intersección.

Módulo que centraliza toda la geometría necesaria para calcular
métricas de somnolencia a partir de landmarks faciales.
"""

from __future__ import annotations

import math

from src.utils.logger import get_logger

logger = get_logger(__name__)

Point = tuple[int, int]


class Calculator:
    """Cálculos geométricos para landmarks faciales."""

    @staticmethod
    def distance(p1: Point, p2: Point) -> float:
        """Distancia euclidiana entre dos puntos.

        Args:
            p1: Primer punto (x, y).
            p2: Segundo punto (x, y).

        Returns:
            Distancia como float.
        """
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    @staticmethod
    def midpoint(p1: Point, p2: Point) -> Point:
        """Punto medio entre dos puntos.

        Args:
            p1: Primer punto (x, y).
            p2: Segundo punto (x, y).

        Returns:
            Punto medio como tupla (x, y).
        """
        return ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)

    def ear(self, points: tuple[Point, ...]) -> float | None:
        """Eye Aspect Ratio. Retorna None si los puntos son inválidos.

        Calcula la relación de aspecto del ojo usando 6 landmarks:
            EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)

        Args:
            points: Tupla de 6 puntos del ojo (p1..p6).

        Returns:
            EAR como float entre 0 y 1, o None si el cálculo no es posible.
        """
        if len(points) != 6:
            logger.warning(f"EAR esperaba 6 puntos, recibió {len(points)}")
            return None

        p1, p2, p3, p4, p5, p6 = points
        A = self.distance(p2, p6)
        B = self.distance(p3, p5)
        C = self.distance(p1, p4)

        if C < 1e-6:
            logger.warning("EAR: distancia horizontal cercana a cero")
            return None

        return (A + B) / (2.0 * C)

    def mor(self, lips: tuple[Point, ...]) -> float:
        """Mouth Open Ratio.

        Calcula qué tan abierta está la boca usando 4 landmarks:
            MOR = altura_boca / ancho_boca

        Args:
            lips: Tupla de 4 puntos de los labios (l1, l2, l3, l4).

        Returns:
            MOR como float. Retorna 0.0 si el cálculo no es posible.
        """
        if len(lips) != 4:
            logger.warning(f"MOR esperaba 4 puntos, recibió {len(lips)}")
            return 0.0

        l1, l2, l3, l4 = lips
        w = self.distance(l1, l3)
        h = self.distance(l2, l4)

        if w < 1e-6:
            return 0.0

        return h / w

    def check_intersection(self, line1: tuple, line2: tuple) -> bool:
        """Verifica si dos segmentos de línea se intersectan.

        Args:
            line1: Tupla de dos puntos ((x1,y1), (x2,y2)).
            line2: Tupla de dos puntos ((x3,y3), (x4,y4)).

        Returns:
            True si los segmentos se intersectan, False si no.
        """
        (x1, y1), (x2, y2) = line1
        (x3, y3), (x4, y4) = line2
        denom = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)

        if abs(denom) < 1e-10:
            return False

        t = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / denom
        u = ((x3 - x1) * (y2 - y1) - (y3 - y1) * (x2 - x1)) / denom
        return 0 <= t <= 1 and 0 <= u <= 1
