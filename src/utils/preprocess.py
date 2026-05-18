"""Preprocesado de frames: resize, conversión de color, mejora de iluminación.

Corrección del bug del repo original: ZeroDivisionError en enhance()
cuando pixel_count es cero. Se usa luminance.size en el denominador.
"""

from __future__ import annotations

import cv2
import numpy as np

from src.utils.logger import get_logger

logger = get_logger(__name__)


class Preprocessor:
    """Operaciones básicas sobre frames BGR de OpenCV."""

    @staticmethod
    def resize(frame: np.ndarray, size: tuple[int, int]) -> np.ndarray:
        """Redimensiona el frame al tamaño dado.

        Args:
            frame: Frame de entrada como np.ndarray.
            size: Tupla (ancho, alto) en píxeles.

        Returns:
            Frame redimensionado.
        """
        return cv2.resize(frame, size)

    @staticmethod
    def bgr_to_rgb(frame: np.ndarray) -> np.ndarray:
        """Convierte BGR (OpenCV) a RGB (Mediapipe).

        Args:
            frame: Frame en formato BGR.

        Returns:
            Frame en formato RGB.
        """
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


class Enhancer(Preprocessor):
    """Mejora la iluminación de frames oscuros con ecualización de histograma.

    FIX aplicado: el repo original dividía np.sum(luminance) / (n - i),
    lo cual lanza ZeroDivisionError cuando n == i. Aquí se usa
    luminance.size que nunca puede ser cero en una imagen válida.
    """

    LUMINANCE_THRESHOLD = 60

    def enhance(self, rgb_frame: np.ndarray) -> np.ndarray:
        """Mejora la iluminación si el frame está por debajo del umbral.

        Args:
            rgb_frame: Frame en formato RGB.

        Returns:
            Frame mejorado en RGB. Si falla, retorna el frame original.
        """
        try:
            ycbcr = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2YCrCb)
            luminance = ycbcr[:, :, 0].astype(np.float32)
            pixel_count = luminance.size

            # FIX: pixel_count nunca es cero en una imagen válida
            mean_lum = (
                luminance.sum() / pixel_count
                if pixel_count > 0
                else self.LUMINANCE_THRESHOLD
            )

            if mean_lum < self.LUMINANCE_THRESHOLD:
                logger.debug(f"Mejorando frame | luminancia_media={mean_lum:.1f}")
                return self._equalize(rgb_frame)

        except Exception:
            logger.exception(
                "Error en mejora de iluminación — retornando frame original"
            )

        return rgb_frame

    def _equalize(self, rgb_frame: np.ndarray) -> np.ndarray:
        """Aplica ecualización de histograma al canal de luminancia.

        Args:
            rgb_frame: Frame en formato RGB.

        Returns:
            Frame con iluminación ecualizada en RGB.
        """
        ycbcr = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2YCrCb)
        ycbcr[:, :, 0] = cv2.equalizeHist(ycbcr[:, :, 0])
        return cv2.cvtColor(ycbcr, cv2.COLOR_YCrCb2RGB)
