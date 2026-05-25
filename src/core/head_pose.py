"""Estimación de orientación de la cabeza (Head Pose Estimation)."""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class HeadPose:
    """Resultado de la estimación de orientación de la cabeza.

    Attributes:
        yaw: Rotación izquierda/derecha en grados.
        pitch: Rotación arriba/abajo en grados.
        roll: Inclinación lateral en grados.
        is_distracted: True si supera algún umbral de distracción.
    """

    yaw: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    is_distracted: bool = False


class HeadPoseEstimator:
    """Calcula la orientación de la cabeza (yaw, pitch, roll) usando solvePnP."""

    YAW_THRESHOLD = 30.0
    PITCH_THRESHOLD = 25.0
    ROLL_THRESHOLD = 30.0

    # Puntos 3D genéricos del rostro (en mm) correspondientes a los landmarks:
    # 1 (nariz), 152 (barbilla), 263 (ojo izq), 33 (ojo der),
    # 61 (boca izq), 291 (boca der)
    model_points = np.array(
        [
            (0.0, 0.0, 0.0),  # Punta de nariz (1)
            (0.0, -330.0, -65.0),  # Barbilla (152)
            (-225.0, 170.0, -135.0),  # Esquina externa ojo izq (263)
            (225.0, 170.0, -135.0),  # Esquina externa ojo der (33)
            (-150.0, -150.0, -125.0),  # Comisura labio izq (61)
            (150.0, -150.0, -125.0),  # Comisura labio der (291)
        ],
        dtype="double",
    )

    def estimate(
        self,
        face_landmarks,
        frame_width: int,
        frame_height: int,
    ) -> HeadPose:
        """Estima la orientación de la cabeza a partir de landmarks faciales.

        Args:
            face_landmarks: Landmarks normalizados de Mediapipe.
            frame_width: Ancho del frame en píxeles.
            frame_height: Alto del frame en píxeles.

        Returns:
            HeadPose con los ángulos y flag de distracción.
        """
        if face_landmarks is None:
            return HeadPose()

        # Extraer puntos 2D en el mismo orden que model_points
        indices = [1, 152, 263, 33, 61, 291]
        image_points = []

        for idx in indices:
            lm = face_landmarks.landmark[idx]
            x = lm.x * frame_width
            y = lm.y * frame_height
            image_points.append((x, y))

        image_points = np.array(image_points, dtype="double")

        # Matriz de cámara aproximada
        focal_length = frame_width
        center = (frame_width / 2.0, frame_height / 2.0)
        camera_matrix = np.array(
            [
                [focal_length, 0.0, center[0]],
                [0.0, focal_length, center[1]],
                [0.0, 0.0, 1.0],
            ],
            dtype="double",
        )

        # Distorsión nula asumida
        dist_coeffs = np.zeros((4, 1), dtype="double")

        # Resolver PnP
        success, rvec, tvec = cv2.solvePnP(
            self.model_points,
            image_points,
            camera_matrix,
            dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )

        if not success:
            return HeadPose()

        # Obtener matriz de rotación R
        R, _ = cv2.Rodrigues(rvec)

        # Calcular ángulos de Euler de forma manual y robusta
        sy = math.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
        singular = sy < 1e-6

        if not singular:
            x = math.atan2(R[2, 1], R[2, 2])
            y = math.atan2(-R[2, 0], sy)
            z = math.atan2(R[1, 0], R[0, 0])
        else:
            x = math.atan2(-R[1, 2], R[1, 1])
            y = math.atan2(-R[2, 0], sy)
            z = 0

        pitch = math.degrees(x)
        yaw = math.degrees(y)
        roll = math.degrees(z)

        # Comprobar umbrales de distracción
        is_distracted = (
            abs(yaw) > self.YAW_THRESHOLD
            or abs(pitch) > self.PITCH_THRESHOLD
            or abs(roll) > self.ROLL_THRESHOLD
        )

        return HeadPose(
            yaw=round(yaw, 1),
            pitch=round(pitch, 1),
            roll=round(roll, 1),
            is_distracted=is_distracted,
        )
