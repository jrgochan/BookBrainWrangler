"""
Logger module for Book Knowledge AI application.
"""

import os
import logging
import sys
from datetime import datetime
from typing import Union, Optional

# Define log file paths
LOG_DIR = os.environ.get("LOG_DIR", "logs")
DEFAULT_LOG_FILE = os.path.join(LOG_DIR, "app.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "errors.log")

# Create log directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Create file handlers
def create_file_handler(log_file: str, level: int = logging.DEBUG) -> logging.Handler:
    """
    Create a file handler for logging.
    
    Args:
        log_file: Path to the log file
        level: Logging level
        
    Returns:
        File handler
    """
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    handler = logging.FileHandler(log_file)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    
    return handler

# Create stream handler for console output
def create_stream_handler(level: int = logging.INFO) -> logging.Handler:
    """
    Create a stream handler for console logging.
    
    Args:
        level: Logging level
        
    Returns:
        Stream handler
    """
    formatter = logging.Formatter(
        "%(levelname)s - %(message)s"
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    
    return handler

# Add custom logging level for success messages
def _add_success_level():
    """Add custom SUCCESS logging level."""
    SUCCESS = 25  # Between INFO and WARNING
    
    if not hasattr(logging, "SUCCESS"):
        logging.SUCCESS = SUCCESS
        logging.addLevelName(SUCCESS, "SUCCESS")
    
    def success(self, message, *args, **kwargs):
        """Log a success message."""
        self.log(logging.SUCCESS, message, *args, **kwargs)
    
    logging.Logger.success = success

# Add custom logging level
_add_success_level()

# Initialize default handlers
default_file_handler = create_file_handler(DEFAULT_LOG_FILE)
error_file_handler = create_file_handler(ERROR_LOG_FILE, level=logging.ERROR)
console_handler = create_stream_handler()

# Get a logger
def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Optional custom log file path
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add file handler
    if log_file:
        custom_file_handler = create_file_handler(log_file)
        logger.addHandler(custom_file_handler)
    else:
        logger.addHandler(default_file_handler)
    
    # Add error file handler
    logger.addHandler(error_file_handler)
    
    # Add console handler
    logger.addHandler(console_handler)
    
    # Set logger level
    logger.setLevel(logging.DEBUG)
    
    return logger

# Default application logger
app_logger = get_logger("book_knowledge_ai")

def log_info(message: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Log an info message.
    
    Args:
        message: Message to log
        logger: Optional logger instance (default: app_logger)
    """
    (logger or app_logger).info(message)

def log_error(message: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Log an error message.
    
    Args:
        message: Message to log
        logger: Optional logger instance (default: app_logger)
    """
    (logger or app_logger).error(message)

def log_warning(message: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Log a warning message.
    
    Args:
        message: Message to log
        logger: Optional logger instance (default: app_logger)
    """
    (logger or app_logger).warning(message)

def log_debug(message: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Log a debug message.
    
    Args:
        message: Message to log
        logger: Optional logger instance (default: app_logger)
    """
    (logger or app_logger).debug(message)

def log_success(message: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Log a success message.
    
    Args:
        message: Message to log
        logger: Optional logger instance (default: app_logger)
    """
    (logger or app_logger).success(message)

# Initialize application logger
log_info("Logger initialized")