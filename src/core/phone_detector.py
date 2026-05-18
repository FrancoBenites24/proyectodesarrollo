"""Detección de posible uso de celular."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot

import numpy as np


@dataclass
class PhoneDetectionResult:
    """Resultado de detección de celular."""

    phone_detected: bool
    hand_center: tuple[int, int] | None = None
    distance_to_face: float | None = None


class PhoneDetector:
    """Detecta posible uso de celular usando manos + rostro."""

    # Distancia máxima permitida entre mano y oreja
    HAND_FACE_DISTANCE_RATIO = 0.15

    def __init__(self) -> None:
        pass

    @staticmethod
    def _landmark_to_pixel(landmark, frame_width: int, frame_height: int):
        """Convierte landmark normalizado a coordenadas pixel."""

        x = int(landmark.x * frame_width)
        y = int(landmark.y * frame_height)

        return x, y

    @staticmethod
    def _calculate_distance(p1, p2) -> float:
        """Calcula distancia euclidiana."""

        return hypot(p1[0] - p2[0], p1[1] - p2[1])

    def _get_hand_center(
        self,
        hand_landmarks,
        frame_width: int,
        frame_height: int,
    ):
        """
        Calcula el centro de la mano usando:
        0  = WRIST
        5  = INDEX_MCP
        9  = MIDDLE_MCP
        """

        indices = [0, 5, 9]

        points = []

        for idx in indices:
            landmark = hand_landmarks.landmark[idx]

            x, y = self._landmark_to_pixel(
                landmark,
                frame_width,
                frame_height,
            )

            points.append((x, y))

        center_x = int(np.mean([p[0] for p in points]))
        center_y = int(np.mean([p[1] for p in points]))

        return center_x, center_y

    def detect(
        self,
        hand_landmarks,
        face_landmarks,
        frame_width: int,
        frame_height: int,
    ) -> PhoneDetectionResult:
        """
        Detecta si la mano está cerca de la cara.
        """

        # Validación básica
        if hand_landmarks is None or face_landmarks is None:
            return PhoneDetectionResult(phone_detected=False)

        # =========================
        # Centro de la mano
        # =========================
        hand_center = self._get_hand_center(
            hand_landmarks,
            frame_width,
            frame_height,
        )

        # =========================
        # Landmarks de referencia facial
        # =========================

        left_ear = self._landmark_to_pixel(
            face_landmarks.landmark[234],
            frame_width,
            frame_height,
        )

        right_ear = self._landmark_to_pixel(
            face_landmarks.landmark[454],
            frame_width,
            frame_height,
        )

        nose = self._landmark_to_pixel(
            face_landmarks.landmark[1],
            frame_width,
            frame_height,
        )

        # =========================
        # Distancias a las orejas
        # =========================

        dist_left = self._calculate_distance(hand_center, left_ear)
        dist_right = self._calculate_distance(hand_center, right_ear)

        min_distance = min(dist_left, dist_right)

        # =========================
        # Umbral dinámico
        # =========================

        max_distance = frame_width * self.HAND_FACE_DISTANCE_RATIO

        # =========================
        # Verificar altura de la mano
        # =========================

        hand_y = hand_center[1]
        nose_y = nose[1]

        # Zona aproximada de la cara
        face_top = int(nose_y - (frame_height * 0.15))
        face_bottom = int(nose_y + (frame_height * 0.20))

        hand_in_face_zone = face_top <= hand_y <= face_bottom

        # =========================
        # Detección final
        # =========================

        phone_detected = (
            min_distance < max_distance
            and hand_in_face_zone
        )

        return PhoneDetectionResult(
            phone_detected=phone_detected,
            hand_center=hand_center,
            distance_to_face=min_distance,
        )