"""
Logger factory for Not-So-Fancy-Weather.
Provides easy access to logger instances.
"""
import logging
from typing import Any, Optional

from .logger import get_logger_instance


class LoggerAdapter(logging.LoggerAdapter):
    """
    Adapter to allow binding values to loggers.
    """
    def __init__(self, logger, extra=None):
        super().__init__(logger, extra or {})
        
    def process(self, msg, kwargs):
        # If 'extra' is already in kwargs, merge with self.extra
        if 'extra' in kwargs:
            extra_dict = kwargs['extra'].copy() if isinstance(kwargs['extra'], dict) else {}
            extra_dict.update(self.extra)
            kwargs['extra'] = extra_dict
        else:
            # Otherwise, use self.extra as the 'extra' dict
            kwargs['extra'] = self.extra.copy()
        
        return msg, kwargs
    
    def bind(self, **kwargs):
        """
        Return a new logger with the given context values bound.
        """
        new_extra = self.extra.copy()
        new_extra.update(kwargs)
        return LoggerAdapter(self.logger, new_extra)


def get_logger(name: str, custom_file_path: Optional[str] = None, **initial_values: Any) -> LoggerAdapter:
    """
    Get a configured logger instance with the given name, optional custom file path, and initial values.
    
    Args:
        name: Name of the logger, typically the module name.
        custom_file_path: Optional custom file path to store logs for this logger.
                          If provided, logs from this logger will be written to this file
                          in addition to the default logging behavior.
        **initial_values: Initial key-value pairs to bind to the logger.
        
    Returns:
        A configured logger instance with initial values bound.
    """
    logger_instance = get_logger_instance()
    logger = logger_instance.get_logger(name, custom_file_path)
    
    # Add adapter for binding context
    adapter = LoggerAdapter(logger, initial_values or None)
    
    return adapter 