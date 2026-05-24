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
        phone_detected: bool = False,
    ) -> np.ndarray:
        """Dibuja landmarks y métricas."""

        color = GREEN if eye_open else RED

        # Ojo izquierdo
        for pt in left_eye:
            cv2.circle(frame, pt, 2, color, -1)

        # Ojo derecho
        for pt in right_eye:
            cv2.circle(frame, pt, 2, color, -1)

        # Labios
        for pt in lips:
            cv2.circle(frame, pt, 2, WHITE, -1)

        # EAR
        cv2.putText(
            frame,
            f"EAR: {ear:.3f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )

        # MOR
        cv2.putText(
            frame,
            f"MOR: {mor:.3f}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            WHITE,
            2,
        )

        # Ojos cerrados
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

        # Celular detectado
        if phone_detected:
            cv2.putText(
                frame,
                "CELULAR DETECTADO",
                (10, 140),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                RED,
                2,
            )

        return frame