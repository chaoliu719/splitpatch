#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def setup_logging(log_level: bool):
    """Configure package-level logging settings

    Args:
        log_level: boolean value (True for DEBUG, False for INFO)
    """
    numeric_level = logging.DEBUG if log_level else logging.INFO
    logger.setLevel(numeric_level)

    # Add is_debug_mode method to logger
    def is_debug_mode() -> bool:
        """Check if current logging level is DEBUG

        Returns:
            bool: True if logging level is DEBUG, False otherwise
        """
        return logger.getEffectiveLevel() <= logging.DEBUG

    logger.is_debug_mode = is_debug_mode

__all__ = ['logger', 'setup_logging']
