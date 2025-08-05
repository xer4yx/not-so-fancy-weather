"""
Logger implementation for Not-So-Fancy-Weather.
Implements asynchronous logging with QueueHandler/QueueListener using FastAPI's logger style.
"""
import sys
import json
import logging
import os
import queue
import threading
from datetime import datetime
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from typing import Optional, Dict, Any, List, Callable

from fastapi.logger import logger as fastapi_logger
from fastapi.concurrency import contextmanager_in_threadpool

from utils.configs import NSFWLogSettings


# Define level prefixes to match FastAPI's style
LEVEL_PREFIXES = {
    logging.DEBUG: "\033[36mDEBUG\033[0m:",
    logging.INFO: "\033[32mINFO\033[0m: ",
    logging.WARNING: "\033[33mWARNING\033[0m:",
    logging.ERROR: "\033[31mERROR\033[0m:  ",
    logging.CRITICAL: "\033[31mCRITICAL\033[0m:",
}


class FastAPIStyleFormatter(logging.Formatter):
    """
    Custom formatter that adds levelprefix to match FastAPI's logging style.
    """
    def format(self, record):
        # Add levelprefix attribute
        record.levelprefix = LEVEL_PREFIXES.get(record.levelno, f"{record.levelname}:")
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """
    Custom formatter to output logs in JSON format.
    """
    def format(self, record):
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra attributes from the record
        if hasattr(record, 'extra'):
            for key, value in record.extra.items():
                log_data[key] = value
        
        # Add other custom attributes from the record
        for key, value in record.__dict__.items():
            if key not in {"args", "exc_info", "exc_text", "msg", "message", 
                          "created", "levelname", "name", "pathname", 
                          "filename", "module", "lineno", "funcName", 
                          "levelno", "msecs", "relativeCreated", "thread", 
                          "threadName", "processName", "process", "asctime",
                          "levelprefix", "extra"}:
                log_data[key] = value

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }
            
        # Use compact JSON formatting with minimal separators
        return json.dumps(log_data, separators=(",", ":"))


class JSONLogFileHandler(RotatingFileHandler):
    """
    Custom file handler that ensures each log entry is on its own line.
    """
    def __init__(self, filename, **kwargs):
        # Create the directory if it doesn't exist
        log_dir = os.path.dirname(filename)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Initialize the handler with the file
        super().__init__(filename, **kwargs)
        
    def emit(self, record):
        """
        Emit a record with proper newline handling.
        
        This ensures each JSON object is on its own line.
        """
        if self.stream is None:
            self.stream = self._open()
            
        try:
            msg = self.format(record)
            # Add a newline at the end of each JSON object
            msg += "\n"
            self.stream.write(msg)
            self.flush()
        except Exception as e:
            self.handleError(record)


class NSFWLogger:
    """
    Logger class for Not-So-Fancy-Weather application.
    Implements asynchronous logging with QueueHandler/QueueListener.
    """

    def __init__(self, config: Optional[NSFWLogSettings] = None):
        """
        Initialize the logger with the given configuration.
        
        Args:
            config: Logger configuration settings. If None, defaults will be used.
        """
        self.config = config or NSFWLogSettings()
        self._queue = queue.Queue(self.config.QUEUE_SIZE)
        self._configure_logging()
        self._handlers_cache = {}
        self._configure_queue_listener()

    def _configure_logging(self) -> None:
        """Configure logging with FastAPI style and settings."""
        # Get log level
        log_level = getattr(logging, self.config.LEVEL.upper(), logging.INFO)
        
        # Create queue handler
        queue_handler = QueueHandler(self._queue)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Remove existing handlers if any
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
        # Add queue handler
        root_logger.addHandler(queue_handler)

    def _get_file_handler(self, file_path: str) -> JSONLogFileHandler:
        """
        Get or create a file handler for the given file path.
        
        Args:
            file_path: Path to the log file.
            
        Returns:
            A configured file handler.
        """
        if file_path in self._handlers_cache:
            return self._handlers_cache[file_path]
        
        try:
            file_handler = JSONLogFileHandler(
                file_path,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
            )
            json_formatter = JSONFormatter()
            file_handler.setFormatter(json_formatter)
            self._handlers_cache[file_path] = file_handler
            return file_handler
        except Exception as e:
            # Log to stderr if there's an issue with the file handler
            sys.stderr.write(f"Error setting up log file {file_path}: {str(e)}\n")
            return None

    def _configure_queue_listener(self) -> None:
        """Configure and start the queue listener for asynchronous logging."""
        handlers = []
        
        # Console handler with FastAPI-style formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_format = self.config.FORMAT
        console_formatter = FastAPIStyleFormatter(console_format)
        console_handler.setFormatter(console_formatter)
        handlers.append(console_handler)
        
        # Default file handler with JSON formatter
        if self.config.FILE_PATH:
            file_handler = self._get_file_handler(self.config.FILE_PATH)
            if file_handler:
                handlers.append(file_handler)
        
        # Create and start queue listener
        self._listener = QueueListener(
            self._queue,
            *handlers,
            respect_handler_level=True,
        )
        self._listener.start()

    def get_logger(self, name: str, custom_file_path: Optional[str] = None) -> logging.Logger:
        """
        Get a logger instance with the given name and optional custom file path.
        
        Args:
            name: Name of the logger, typically the module name.
            custom_file_path: Optional custom file path for this logger's output.
                              If provided, logs will be written to this file instead of 
                              the default file specified in config.
            
        Returns:
            A configured logger instance.
        """
        logger = logging.getLogger(name)
        
        # If a custom file path is provided, ensure there's a handler for it
        if custom_file_path:
            # Create a filter for this specific logger name
            class LoggerNameFilter(logging.Filter):
                def __init__(self, logger_name):
                    super().__init__()
                    self.logger_name = logger_name
                
                def filter(self, record):
                    return record.name == self.logger_name
            
            # Get or create file handler for this path
            file_handler = self._get_file_handler(custom_file_path)
            if file_handler:
                # Add a filter to only process logs from this logger
                name_filter = LoggerNameFilter(name)
                file_handler.addFilter(name_filter)
                
                # Add the handler to the queue listener if not already added
                if file_handler not in self._listener.handlers:
                    self._listener.handlers = list(self._listener.handlers) + [file_handler]
        
        return logger

    def shutdown(self) -> None:
        """Shutdown the logger and queue listener."""
        if hasattr(self, '_listener'):
            self._listener.stop()


# Singleton instance of the logger
_logger_instance = None
_logger_lock = threading.Lock()


def get_logger_instance(config: Optional[NSFWLogSettings] = None) -> NSFWLogger:
    """
    Get or create the singleton logger instance.
    
    Args:
        config: Optional configuration to use when creating the logger.
        
    Returns:
        The configured NSFWLogger instance.
    """
    global _logger_instance
    
    if _logger_instance is None:
        with _logger_lock:
            if _logger_instance is None:
                _logger_instance = NSFWLogger(config)
    
    return _logger_instance


def get_logger(name: str, custom_file_path: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with the given name and optional custom file path.
    
    Args:
        name: Name of the logger, typically the module name.
        custom_file_path: Optional custom file path to store logs for this logger.
                          If provided, logs from this logger will be written to this file
                          in addition to the default logging behavior.
                          
    Returns:
        A configured logger instance.
    """
    logger_instance = get_logger_instance()
    return logger_instance.get_logger(name, custom_file_path)


def shutdown_logger() -> None:
    """Shutdown the logger instance if it exists."""
    global _logger_instance
    
    if _logger_instance is not None:
        with _logger_lock:
            if _logger_instance is not None:
                _logger_instance.shutdown()
                _logger_instance = None 