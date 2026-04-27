"""Utilidades de dibujo sobre frames OpenCV.

Dibuja landmarks faciales y métricas (EAR, MOR, alertas)
directamente sobre el frame para visualización en tiempo real.
"""

from __future__ import annotations

import cv2
import numpy as np

from src.utils.logger import get_logger

logger = get_logger(__name__)

GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (0, 255, 255)


class Drawer:
    """Dibuja landmarks y métricas sobre frames de OpenCV."""

    def annotate(
        self,
        frame: np.ndarray,
        left_eye: tuple,
        right_eye: tuple,
        lips: tuple,
        ear: float,
        mor: float,
        eye_open: bool,
    ) -> np.ndarray:
        """Dibuja landmarks y muestra EAR/MOR en el frame.

        Args:
            frame: Frame BGR de OpenCV a anotar.
            left_eye: Puntos del ojo izquierdo.
            right_eye: Puntos del ojo derecho.
            lips: Puntos de los labios.
            ear: Valor de Eye Aspect Ratio.
            mor: Valor de Mouth Open Ratio.
            eye_open: True si los ojos están abiertos.

        Returns:
            Frame anotado con landmarks y métricas.
        """
        color = GREEN if eye_open else RED

        # Dibujar puntos del ojo izquierdo
        for pt in left_eye:
            cv2.circle(frame, pt, 2, color, -1)

        # Dibujar puntos del ojo derecho
        for pt in right_eye:
            cv2.circle(frame, pt, 2, color, -1)

        # Dibujar puntos de labios
        for pt in lips:
            cv2.circle(frame, pt, 2, WHITE, -1)

        # Texto de métricas
        cv2.putText(
            frame,
            f"EAR: {ear:.3f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )
        cv2.putText(
            frame,
            f"MOR: {mor:.3f}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            WHITE,
            2,
        )

        if not eye_open:
            cv2.putText(
                frame,
                "OJOS CERRADOS!",
                (10, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                RED,
                2,
            )

        return frame
