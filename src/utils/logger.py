"""Logging centralizado con loguru.

Todos los módulos del proyecto deben usar este logger en lugar de print().
Configuración controlada por variables de entorno:
    - LOG_LEVEL: nivel mínimo de log (default: INFO)
    - LOG_FILE: ruta del archivo de log (default: logs/drowsyguard.log)

Uso:
    from src.utils.logger import get_logger

    logger = get_logger(__name__)
    logger.info("Mensaje informativo")
    logger.warning("Advertencia")
    logger.error("Error grave")
"""
from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from loguru import logger as _logger

# Cargar variables de entorno desde .env si existe
load_dotenv()

_configured = False


def _configure() -> None:
    """Configura loguru una sola vez (singleton).

    - Consola: formato colorido con timestamp, nivel, módulo y línea.
    - Archivo: rotación semanal, retención 4 semanas, compresión zip.
    """
    global _configured
    if _configured:
        return

    # Limpiar handlers por defecto de loguru
    _logger.remove()

    level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Handler de consola
    _logger.add(
        sys.stderr,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> \u2014 {message}"
        ),
        colorize=True,
    )

    # Handler de archivo
    log_file = os.getenv("LOG_FILE", "logs/drowsyguard.log")
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    _logger.add(
        log_file,
        level="DEBUG",
        rotation="1 week",
        retention="4 weeks",
        compression="zip",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{line} \u2014 {message}"
        ),
    )

    _configured = True
    _logger.debug(f"Logger configurado | level={level} | file={log_file}")


def get_logger(name: str):
    """Retorna un logger configurado con el nombre del módulo.

    Args:
        name: Nombre del módulo (usar __name__).

    Returns:
        Logger de loguru con contexto del módulo.

    Example:
        logger = get_logger(__name__)
        logger.info("Sistema iniciado")
    """
    _configure()
    return _logger.bind(name=name)
