"""Detección de posible uso de celular."""

from __future__ import annotations

from math import hypot

import numpy as np

from src.core.phone_result import PhoneResult
from src.utils.mediapipe_wrapper import HandsWrapper


class PhoneDetector:
    """Detecta posible uso de celular usando manos + rostro."""

    HAND_FACE_DISTANCE_RATIO = 0.15

    def __init__(self) -> None:
        self._hands = HandsWrapper()

    @staticmethod
    def _landmark_to_pixel(
        landmark,
        frame_width: int,
        frame_height: int,
    ) -> tuple[int, int]:
        """Convierte landmark normalizado a pixel."""

        x = int(landmark.x * frame_width)
        y = int(landmark.y * frame_height)

        return x, y

    @staticmethod
    def _calculate_distance(
        p1: tuple[int, int],
        p2: tuple[int, int],
    ) -> float:
        """Calcula distancia euclidiana."""

        return hypot(p1[0] - p2[0], p1[1] - p2[1])

    def _get_hand_center(
        self,
        hand_landmarks,
        frame_width: int,
        frame_height: int,
    ) -> tuple[int, int]:
        """
        Calcula centro de la mano usando:
            0 = WRIST
            5 = INDEX_MCP
            9 = MIDDLE_MCP
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
        frame,
        face_landmarks,
        frame_width: int,
        frame_height: int,
    ) -> PhoneResult:
        """Detecta posible uso de celular."""

        if face_landmarks is None:
            return PhoneResult()

        hands_result = self._hands.process(frame)

        if not hands_result:
            return PhoneResult(
                phone_detected=False,
                hand_detected=False,
            )

        hand_landmarks = hands_result[0]

        hand_center = self._get_hand_center(
            hand_landmarks,
            frame_width,
            frame_height,
        )

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

        dist_left = self._calculate_distance(
            hand_center,
            left_ear,
        )

        dist_right = self._calculate_distance(
            hand_center,
            right_ear,
        )

        min_distance = min(dist_left, dist_right)

        max_distance = (
            frame_width * self.HAND_FACE_DISTANCE_RATIO
        )

        hand_y = hand_center[1]
        nose_y = nose[1]

        face_top = int(nose_y - (frame_height * 0.15))
        face_bottom = int(nose_y + (frame_height * 0.20))

        hand_in_face_zone = (
            face_top <= hand_y <= face_bottom
        )

        phone_detected = (
            min_distance < max_distance
            and hand_in_face_zone
        )

        return PhoneResult(
            phone_detected=phone_detected,
            hand_detected=True,
            hand_position=(
                hand_center[0] / frame_width,
                hand_center[1] / frame_height,
            ),
            confidence=1.0 if phone_detected else 0.3,
        )