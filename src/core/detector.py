"""Motor principal de detección de somnolencia.

Integra todos los utils del Issue #2 para producir un FrameResult
con EAR, MOR y si el conductor tiene los ojos abiertos o está bostezando.

Landmarks de referencia validados:
    left_eye:    (362, 385, 387, 263, 373, 380)
    right_eye:   (33, 160, 158, 133, 153, 144)
    lips:        (61, 17, 291, 0)
    nose_to_chin: (1, 152)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from src.core.head_pose import HeadPoseEstimator
from src.core.phone_detector import PhoneDetector
from src.utils.calculations import Calculator
from src.utils.drawing import Drawer
from src.utils.logger import get_logger
from src.utils.mediapipe_wrapper import FaceMeshWrapper, PointsExtractor
from src.utils.preprocess import Enhancer, Preprocessor

logger = get_logger(__name__)

DEFAULT_KEYPOINTS: dict[str, tuple[int, ...]] = {
    "left_eye": (362, 385, 387, 263, 373, 380),
    "right_eye": (33, 160, 158, 133, 153, 144),
    "lips": (61, 17, 291, 0),
    "nose_to_chin": (1, 152),
    # Nuevos landmarks v3.0
    "left_eyebrow": (46, 53, 52, 65, 55),
    "right_eyebrow": (276, 283, 282, 295, 285),
    "left_iris": (468, 469, 470, 471),
    "right_iris": (473, 474, 475, 476),
    "head_pose": (1, 152, 263, 33, 61, 291),
}


@dataclass
class FrameResult:
    ear: float = 0.0
    mor: float = 0.0
    eye_open: bool = True
    yawning: bool = False
    phone_detected: bool = False
    is_distracted: bool = False  # NUEVO
    head_yaw: float = 0.0  # NUEVO
    head_pitch: float = 0.0  # NUEVO
    face_detected: bool = False
    annotated_frame: np.ndarray | None = None
    timestamp: float = field(default_factory=time.time)


class DrowsinessDetector:
    """Detecta somnolencia en tiempo real usando Mediapipe FaceMesh.

    Pipeline por frame:
        1. Resize al tamaño estándar.
        2. BGR → RGB.
        3. Mejora de iluminación si el frame está oscuro.
        4. Detección de landmarks con FaceMesh.
        5. Cálculo de EAR y MOR.
        6. Anotación visual del frame.

    Uso:
        detector = DrowsinessDetector()
        result = detector.process(frame_bgr)
        if result.face_detected:
            print(result.ear, result.alert_level)

    Nota:
        `process()` NUNCA lanza excepciones — captura todo
        internamente y retorna un FrameResult con face_detected=False.
    """

    def __init__(
        self,
        keypoints: dict[str, tuple[int, ...]] | None = None,
        frame_size: tuple[int, int] = (480, 480),
        ear_threshold: float = 0.25,
        mor_threshold: float = 0.6,
    ) -> None:
        """Inicializa el detector con los parámetros dados.

        Args:
            keypoints: Diccionario con índices de landmarks de Mediapipe.
                       Si es None se usan los DEFAULT_KEYPOINTS validados.
            frame_size: Tamaño (ancho, alto) al que se redimensionará cada frame.
            ear_threshold: EAR por debajo del cual se considera ojo cerrado.
            mor_threshold: MOR por encima del cual se considera bostezo.
        """
        self._frame_size = frame_size
        self._ear_threshold = ear_threshold
        self._mor_threshold = mor_threshold
        self._keypoints = keypoints or DEFAULT_KEYPOINTS

        self._preprocessor = Preprocessor()
        self._enhancer = Enhancer()
        self._calculator = Calculator()
        self._drawer = Drawer()
        self._face_mesh = FaceMeshWrapper()
        self._points = PointsExtractor()
        self._phone_detector = PhoneDetector()
        self._head_pose = HeadPoseEstimator()

        logger.info(
            f"DrowsinessDetector listo | "
            f"EAR_threshold={ear_threshold} | "
            f"MOR_threshold={mor_threshold}"
        )

    def process(self, frame: np.ndarray) -> FrameResult:
        """Procesa un frame BGR y retorna las métricas de somnolencia.

        Garantía: este método NUNCA lanza excepciones. Si ocurre cualquier
        error se retorna un FrameResult con face_detected=False y el frame
        original (o None si el frame de entrada también es None).

        Args:
            frame: Frame en formato BGR de OpenCV (np.ndarray).

        Returns:
            FrameResult con EAR, MOR, flags de alerta y frame anotado.
        """
        result = FrameResult()

        try:
            frame = self._preprocessor.resize(frame, self._frame_size)
            rgb = self._preprocessor.bgr_to_rgb(frame)
            enhanced = self._enhancer.enhance(rgb)
            h, w = self._frame_size

            face_landmarks = self._face_mesh.process(enhanced)
            if not face_landmarks:
                result.annotated_frame = frame
                return result

            result.face_detected = True
            kp = self._keypoints

            left_eye = self._points.get(face_landmarks, kp["left_eye"], w, h)
            right_eye = self._points.get(face_landmarks, kp["right_eye"], w, h)
            lips = self._points.get(face_landmarks, kp["lips"], w, h)

            ear_l = self._calculator.ear(left_eye)
            ear_r = self._calculator.ear(right_eye)

            if ear_l is None or ear_r is None:
                logger.warning("EAR retornó None — saltando frame")
                result.annotated_frame = frame
                return result

            result.ear = round(min(ear_l, ear_r), 3)
            result.mor = round(self._calculator.mor(lips), 3)
            result.eye_open = result.ear > self._ear_threshold
            result.yawning = result.mor > self._mor_threshold

            # Detección de uso de celular
            phone_res = self._phone_detector.detect(enhanced, face_landmarks[0], w, h)
            result.phone_detected = phone_res.phone_detected

            # Estimación de orientación
            pose_res = self._head_pose.estimate(face_landmarks[0], w, h)
            result.is_distracted = pose_res.is_distracted
            result.head_yaw = pose_res.yaw
            result.head_pitch = pose_res.pitch

            # Extraer nuevos landmarks
            left_eyebrow = self._points.get(face_landmarks, kp["left_eyebrow"], w, h)
            right_eyebrow = self._points.get(face_landmarks, kp["right_eyebrow"], w, h)
            left_iris = self._points.get(face_landmarks, kp["left_iris"], w, h)
            right_iris = self._points.get(face_landmarks, kp["right_iris"], w, h)

            result.annotated_frame = self._drawer.annotate(
                frame,
                left_eye,
                right_eye,
                lips,
                result.ear,
                result.mor,
                result.eye_open,
                phone_detected=result.phone_detected,
                left_eyebrow=left_eyebrow,
                right_eyebrow=right_eyebrow,
                left_iris=left_iris,
                right_iris=right_iris,
                head_pose=pose_res,
            )

        except Exception:
            logger.exception("Error inesperado en DrowsinessDetector.process()")
            result.annotated_frame = frame

        return result
