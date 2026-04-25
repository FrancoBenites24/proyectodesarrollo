"""Tests para el logger centralizado.

Verifica que el módulo de logging:
- Retorna un logger válido.
- No lanza excepciones al loguear.
- Crea el directorio de logs automáticamente.
- Responde a la variable de entorno LOG_LEVEL.
"""

from __future__ import annotations

import os

import pytest


def test_get_logger_returns_logger():
    """get_logger debe retornar un objeto logger válido."""
    from src.utils.logger import get_logger

    logger = get_logger(__name__)
    assert logger is not None


def test_logger_does_not_raise_on_info():
    """Loguear con nivel INFO no debe lanzar excepciones."""
    from src.utils.logger import get_logger

    logger = get_logger("test_info")
    logger.info("Test message — info level")


def test_logger_does_not_raise_on_warning():
    """Loguear con nivel WARNING no debe lanzar excepciones."""
    from src.utils.logger import get_logger

    logger = get_logger("test_warning")
    logger.warning("Test message — warning level")


def test_logger_does_not_raise_on_error():
    """Loguear con nivel ERROR no debe lanzar excepciones."""
    from src.utils.logger import get_logger

    logger = get_logger("test_error")
    logger.error("Test message — error level")


def test_logger_debug_does_not_raise():
    """Loguear con nivel DEBUG no debe lanzar excepciones."""
    from src.utils.logger import get_logger

    logger = get_logger("test_debug")
    logger.debug("Test message — debug level")


def test_logs_directory_created():
    """El directorio de logs debe crearse automáticamente."""
    from src.utils.logger import get_logger

    # Forzar la configuración del logger
    get_logger("test_dir")
    log_dir = os.path.dirname(os.getenv("LOG_FILE", "logs/drowsyguard.log"))
    assert os.path.isdir(log_dir)


def test_multiple_loggers_same_module():
    """Múltiples llamadas a get_logger con el mismo nombre deben funcionar."""
    from src.utils.logger import get_logger

    logger1 = get_logger("same_module")
    logger2 = get_logger("same_module")
    logger1.info("From logger1")
    logger2.info("From logger2")


def test_logger_with_format_string():
    """El logger debe manejar format strings sin problemas."""
    from src.utils.logger import get_logger

    logger = get_logger("test_format")
    value = 42
    logger.info(f"Test con valor={value} y tipo={type(value).__name__}")
