"""
Utility functions for the Knowledge Base module.
"""

import os
import tempfile
import shutil
from utils.logger import get_logger

logger = get_logger(__name__)

def get_writable_temp_dir(prefix="kb_tmp_"):
    """
    Create a writable temporary directory.
    
    Args:
        prefix: Prefix for the temporary directory name
        
    Returns:
        Path to the temporary directory
    """
    try:
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        logger.debug(f"Created temporary directory: {temp_dir}")
        return temp_dir
    except Exception as e:
        logger.error(f"Error creating temporary directory: {str(e)}")
        raise

def safe_delete_directory(directory_path):
    """
    Safely delete a directory and its contents.
    
    Args:
        directory_path: Path to the directory to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if os.path.exists(directory_path):
            shutil.rmtree(directory_path)
            logger.debug(f"Deleted directory: {directory_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting directory {directory_path}: {str(e)}")
        return False

def chunk_list(lst, chunk_size):
    """
    Split a list into chunks of specified size.
    
    Args:
        lst: List to split
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def format_runtime_stats(start_time, end_time, item_count):
    """
    Format runtime statistics for logging.
    
    Args:
        start_time: Start time in seconds (from time.time())
        end_time: End time in seconds (from time.time())
        item_count: Number of items processed
        
    Returns:
        Formatted string with runtime statistics
    """
    duration = end_time - start_time
    rate = item_count / max(duration, 0.001)  # Avoid division by zero
    
    return f"Processed {item_count} items in {duration:.2f}s ({rate:.2f} items/s)"
