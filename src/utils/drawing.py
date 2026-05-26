"""Utilidades de dibujo sobre frames OpenCV.

Dibuja landmarks faciales y métricas (EAR, MOR, alertas)
directamente sobre el frame para visualización en tiempo real.
"""

from __future__ import annotations

import cv2
import numpy as np

from src.core.head_pose import HeadPose
from src.utils.logger import get_logger

logger = get_logger(__name__)

GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (0, 255, 255)
ORANGE = (0, 165, 255)
CYAN = (255, 255, 0)


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
        left_eyebrow: tuple | None = None,
        right_eyebrow: tuple | None = None,
        left_iris: tuple | None = None,
        right_iris: tuple | None = None,
        head_pose: HeadPose | None = None,
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

        # Cejas
        if left_eyebrow:
            for pt in left_eyebrow:
                cv2.circle(frame, pt, 2, ORANGE, -1)
        if right_eyebrow:
            for pt in right_eyebrow:
                cv2.circle(frame, pt, 2, ORANGE, -1)

        # Iris
        if left_iris:
            for pt in left_iris:
                cv2.circle(frame, pt, 1, CYAN, -1)
        if right_iris:
            for pt in right_iris:
                cv2.circle(frame, pt, 1, CYAN, -1)

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

        # Orientación de cabeza y ejes 3D
        if head_pose:
            # Mostrar métricas numéricas
            cv2.putText(
                frame,
                f"Yaw: {head_pose.yaw:+.1f}",
                (10, 180),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                WHITE,
                2,
            )
            cv2.putText(
                frame,
                f"Pitch: {head_pose.pitch:+.1f}",
                (10, 210),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                WHITE,
                2,
            )

            # Mostrar alerta de distracción
            if head_pose.is_distracted:
                cv2.putText(
                    frame,
                    "DISTRACCION!",
                    (10, 250),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    YELLOW,
                    2,
                )

            # Proyección de ejes 3D en la nariz
            if head_pose.rvec is not None and head_pose.tvec is not None:
                h, w = frame.shape[:2]
                focal_length = w
                center = (w / 2.0, h / 2.0)
                camera_matrix = np.array(
                    [
                        [focal_length, 0.0, center[0]],
                        [0.0, focal_length, center[1]],
                        [0.0, 0.0, 1.0],
                    ],
                    dtype="double",
                )
                dist_coeffs = np.zeros((4, 1), dtype="double")

                # Puntos 3D de los ejes
                axis_points = np.array(
                    [
                        (0.0, 0.0, 0.0),  # Origen (punta de la nariz)
                        (50.0, 0.0, 0.0),  # Eje X (Rojo)
                        (0.0, 50.0, 0.0),  # Eje Y (Verde)
                        (0.0, 0.0, 50.0),  # Eje Z (Azul)
                    ],
                    dtype="double",
                )

                # Proyectar
                imgpts, _ = cv2.projectPoints(
                    axis_points,
                    head_pose.rvec,
                    head_pose.tvec,
                    camera_matrix,
                    dist_coeffs,
                )

                origin = tuple(map(int, imgpts[0].ravel()))
                x_end = tuple(map(int, imgpts[1].ravel()))
                y_end = tuple(map(int, imgpts[2].ravel()))
                z_end = tuple(map(int, imgpts[3].ravel()))

                # Dibujar ejes
                cv2.line(frame, origin, x_end, (0, 0, 255), 2)  # Rojo
                cv2.line(frame, origin, y_end, (0, 255, 0), 2)  # Verde
                cv2.line(frame, origin, z_end, (255, 0, 0), 2)  # Azul

        return frame
