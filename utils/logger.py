"""
Centralized logging configuration for BookBrainWrangler.

This module configures the Loguru logger for the entire application and provides
helper functions for consistent logging across modules.
"""

import os
import sys
from pathlib import Path
from loguru import logger

class BookBrainLogger:
    """
    Centralized logger configuration for the BookBrainWrangler application.
    Handles setup, configuration and provides convenient access to the logger.
    """
    
    def __init__(self, log_level="INFO"):
        """
        Initialize the logging system.
        
        Args:
            log_level: The minimum log level to display (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.log_level = log_level
        self.log_dir = Path("logs")
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure the logger with console and file handlers."""
        # Create logs directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Remove default logger
        logger.remove()
        
        # Add console handler with color formatting
        logger.add(
            sys.stderr, 
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=self.log_level,
            colorize=True
        )
        
        # Add rotating file handler
        logger.add(
            self.log_dir / "bookbrainwrangler.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",  # Always log everything to file
            rotation="10 MB",  # Rotate when file reaches 10MB
            compression="zip",  # Compress rotated logs
            retention="1 month",  # Keep logs for a month
            backtrace=True,  # Include traceback for errors
            diagnose=True,  # Enable exception diagnostics
            enqueue=True     # Thread-safe logging
        )
        
        # Add a separate error log file for easy troubleshooting
        logger.add(
            self.log_dir / "errors.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="ERROR",  # Only log errors and above
            rotation="5 MB",
            compression="zip",
            retention="3 months",
            backtrace=True,
            diagnose=True,
            enqueue=True
        )
        
        # Set exception handler to log uncaught exceptions
        sys.excepthook = self._handle_exception
        
    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """Log any uncaught exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Don't log keyboard interrupt (Ctrl+C)
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        logger.opt(exception=(exc_type, exc_value, exc_traceback)).error("Uncaught exception")
    
    def get_logger(self, name=None):
        """
        Get a logger with an optional name.
        The name helps identify which module a log entry is coming from.
        
        Args:
            name: Optional name for the logger (typically __name__)
            
        Returns:
            Configured logger instance
        """
        if name:
            return logger.bind(name=name)
        return logger

# Create a singleton instance
log_manager = BookBrainLogger()

# Helper function to get a logger
def get_logger(name=None):
    """
    Get a configured logger with the given name.
    
    Args:
        name: Optional name for the logger (typically __name__)
            
    Returns:
        Configured logger instance
    """
    return log_manager.get_logger(name)
