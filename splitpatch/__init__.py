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

    # Add debug mode methods to logger
    logger.set_debug_mode = lambda enabled: logger.setLevel(logging.DEBUG if enabled else logging.INFO)
    logger.is_debug_mode = lambda: logger.getEffectiveLevel() <= logging.DEBUG

__all__ = ['logger', 'setup_logging']
