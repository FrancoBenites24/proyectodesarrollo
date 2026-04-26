"""Wrappers de Mediapipe FaceMesh y Hands.

Encapsulan la inicialización y el procesamiento de Mediapipe,
exponiendo una interfaz limpia y consistente con type hints.
"""

from __future__ import annotations

import numpy as np

from src.utils.logger import get_logger

logger = get_logger(__name__)

Point = tuple[int, int]


class FaceMeshWrapper:
    """Wrapper de Mediapipe FaceMesh para detección de landmarks faciales.

    Uso:
        mesh = FaceMeshWrapper()
        landmarks = mesh.process(rgb_frame)
        if landmarks:
            # landmarks[0].landmark[idx].x / .y
    """

    def __init__(
        self,
        max_num_faces: int = 1,
        refine_landmarks: bool = True,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        """Inicializa el modelo FaceMesh de Mediapipe.

        Args:
            max_num_faces: Número máximo de caras a detectar.
            refine_landmarks: Refinar landmarks para ojos y labios.
            min_detection_confidence: Confianza mínima para detección.
            min_tracking_confidence: Confianza mínima para seguimiento.
        """
        import mediapipe as mp

        mp_face = mp.solutions.face_mesh
        self._mesh = mp_face.FaceMesh(
            static_image_mode=False,
            max_num_faces=max_num_faces,
            refine_landmarks=refine_landmarks,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        logger.info(
            f"FaceMeshWrapper inicializado | "
            f"max_faces={max_num_faces} | "
            f"refine={refine_landmarks}"
        )

    def process(self, rgb_frame: np.ndarray):
        """Procesa un frame RGB y retorna landmarks faciales.

        Args:
            rgb_frame: Frame en formato RGB como np.ndarray.

        Returns:
            Lista de landmarks faciales, o None si no se detecta cara.
        """
        result = self._mesh.process(rgb_frame)
        return result.multi_face_landmarks


class HandsWrapper:
    """Wrapper de Mediapipe Hands para detección de landmarks de manos.

    Uso:
        hands = HandsWrapper()
        landmarks = hands.process(rgb_frame)
        if landmarks:
            # landmarks[0].landmark[idx].x / .y
    """

    def __init__(
        self,
        max_num_hands: int = 1,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        """Inicializa el modelo Hands de Mediapipe.

        Args:
            max_num_hands: Número máximo de manos a detectar.
            min_detection_confidence: Confianza mínima para detección.
            min_tracking_confidence: Confianza mínima para seguimiento.
        """
        import mediapipe as mp

        mp_hands = mp.solutions.hands
        self._hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        logger.info("HandsWrapper inicializado | " f"max_hands={max_num_hands}")

    def process(self, rgb_frame: np.ndarray):
        """Procesa un frame RGB y retorna landmarks de manos.

        Args:
            rgb_frame: Frame en formato RGB como np.ndarray.

        Returns:
            Lista de landmarks de manos, o None si no se detectan.
        """
        result = self._hands.process(rgb_frame)
        return result.multi_hand_landmarks


class PointsExtractor:
    """Extrae coordenadas (x, y) en píxeles a partir de landmarks de Mediapipe."""

    @staticmethod
    def get(
        landmarks,
        keypoint_indices: tuple[int, ...],
        w: int,
        h: int,
    ) -> tuple[Point, ...]:
        """Extrae puntos de landmarks para los índices dados.

        Convierte las coordenadas normalizadas de Mediapipe (0.0–1.0)
        a coordenadas en píxeles usando el ancho y alto del frame.

        Args:
            landmarks: Lista de face/hand landmarks de Mediapipe.
            keypoint_indices: Índices de los landmarks a extraer.
            w: Ancho del frame en píxeles.
            h: Alto del frame en píxeles.

        Returns:
            Tupla de puntos (x, y) en píxeles.
        """
        return tuple(
            (
                int(landmarks[0].landmark[idx].x * w),
                int(landmarks[0].landmark[idx].y * h),
            )
            for idx in keypoint_indices
        )
