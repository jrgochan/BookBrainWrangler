"""
Logging configuration module for the Book Knowledge AI application.
Uses Loguru for better formatting, context, and levels.
"""

import sys
import os
from pathlib import Path
from loguru import logger

# Define log levels and their display names
LOG_LEVELS = {
    "TRACE": {"name": "TRACE", "color": "<dim>"},
    "DEBUG": {"name": "DEBUG", "color": "<blue>"},
    "INFO": {"name": "INFO", "color": "<green>"},
    "SUCCESS": {"name": "SUCCESS", "color": "<green><bold>"},
    "WARNING": {"name": "WARNING", "color": "<yellow>"},
    "ERROR": {"name": "ERROR", "color": "<red>"},
    "CRITICAL": {"name": "CRITICAL", "color": "<red><bold>"}
}

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

def format_record(record):
    """Format log records with colors and additional metadata"""
    log_level = LOG_LEVELS.get(record["level"].name, {"name": record["level"].name, "color": ""})
    
    # Format: [time] [level] [module:line_no] [function] message
    # Using a simpler format to avoid tag parsing issues
    format_string = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {function} | {message}\n{exception}"
    
    return format_string

def configure_logger():
    """Configure the global logger instance with console and file handlers"""
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stderr,
        format=format_record,
        level="INFO",  # Default console level
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # Add file handlers
    # 1. All logs (rotating by size, keep 3 files of 10MB each)
    logger.add(
        logs_dir / "app.log",
        format=format_record,
        level="DEBUG",
        rotation="10 MB",
        retention=3,
        compression="zip",
        backtrace=True,
        diagnose=True,
    )
    
    # 2. Errors only (rotating daily, keep for 30 days)
    logger.add(
        logs_dir / "errors.log",
        format=format_record,
        level="ERROR",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        backtrace=True, 
        diagnose=True,
    )
    
    # Add environment variable to control log level
    if os.getenv("LOG_LEVEL"):
        level = os.getenv("LOG_LEVEL").upper()
        if level in LOG_LEVELS:
            logger.configure(levels=[level])
    
    logger.info("Logging system initialized")
    return logger

# Export the configured logger
configure_logger()
