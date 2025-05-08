#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import functools
import cProfile
import pstats
from typing import Callable

from splitpatch import logger

# Global variable to control profiling
ENABLE_PROFILING = False

def profile_method(func: Callable) -> Callable:
    """Performance profiling decorator

    Args:
        func: Function to be profiled

    Returns:
        Wrapped function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not ENABLE_PROFILING:
            return func(*args, **kwargs)

        profiler = cProfile.Profile()
        try:
            return profiler.runcall(func, *args, **kwargs)
        finally:
            stats = pstats.Stats(profiler)
            stats.sort_stats('cumulative')
            logger.debug(f"Performance profile for {func.__name__}:")
            stats.print_stats(10)  # Only print top 10 most time-consuming calls
    return wrapper
