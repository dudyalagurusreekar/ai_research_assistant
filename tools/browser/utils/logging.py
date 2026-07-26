"""Logging utilities for the Browser Tool.

This module provides contextual logger configuration ensuring structured,
consistent output formatting across all Browser Tool submodules.
"""

import logging
import sys
from typing import Optional

LOGGER_NAME = "tools.browser"


def get_browser_logger(name: Optional[str] = None) -> logging.Logger:
    """Retrieve or configure a contextual logger for the Browser Tool.

    Args:
        name (Optional[str]): Submodule logger suffix.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger_name = f"{LOGGER_NAME}.{name}" if name else LOGGER_NAME
    logger = logging.getLogger(logger_name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
