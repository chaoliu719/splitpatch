#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

__version__ = "0.1.0"

logger = logging.getLogger(__name__)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def setup_logging(log_level: str = 'WARNING') -> None:
    """Configure package-level logging settings

    Args:
        log_level: Logging level, options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    logger.setLevel(numeric_level)

__all__ = ['__version__', 'logger', 'setup_logging']
