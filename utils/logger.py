"""
Logging utility for Book Knowledge AI.
"""

import os
import logging
import sys
from datetime import datetime
from typing import Optional

# Configure logging
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "errors.log")

# Create logs directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# Set up root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Create formatters
standard_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
detailed_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
)

# File handler for all logs
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(standard_formatter)
root_logger.addHandler(file_handler)

# File handler for error logs
error_file_handler = logging.FileHandler(ERROR_LOG_FILE)
error_file_handler.setLevel(logging.ERROR)
error_file_handler.setFormatter(detailed_formatter)
root_logger.addHandler(error_file_handler)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(standard_formatter)
root_logger.addHandler(console_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Name of the module (usually __name__)
        
    Returns:
        Logger instance for the module
    """
    return logging.getLogger(name)

def set_log_level(level: int) -> None:
    """
    Set the log level for all handlers.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
    """
    root_logger.setLevel(level)
    for handler in root_logger.handlers:
        if handler != error_file_handler:  # Keep error handler at ERROR level
            handler.setLevel(level)
            
def archive_logs(max_size_mb: int = 10) -> bool:
    """
    Archive logs if they exceed a certain size.
    
    Args:
        max_size_mb: Maximum size in MB before archiving
        
    Returns:
        True if logs were archived, False otherwise
    """
    import zipfile
    import os.path
    
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > max_size_mb * 1024 * 1024:
        # Create a timestamped archive filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
        archive_name = os.path.join(LOG_DIR, f"app.{timestamp}.log.zip")
        
        # Create a zip file and add the log file
        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(LOG_FILE, os.path.basename(LOG_FILE))
        
        # Clear the log file
        with open(LOG_FILE, 'w') as f:
            f.write(f"Logs archived to {archive_name} at {datetime.now().isoformat()}\n")
            
        return True
    
    return False