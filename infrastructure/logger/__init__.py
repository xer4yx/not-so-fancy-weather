"""
Logger infrastructure module for Not-So-Fancy-Weather.
"""
from .factory import get_logger
from .logger import shutdown_logger, get_logger_instance

__all__ = [
    "get_logger",
    "shutdown_logger",
    "get_logger_instance"
] 