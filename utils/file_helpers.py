"""
File operation helper utilities.
"""

import os
import tempfile
from typing import List, Dict, Any, Optional, Union, Tuple

from utils.logger import get_logger

# Get a logger for this module
logger = get_logger(__name__)

# Define constants for file operations
ALLOWED_EXTENSIONS = {'.pdf', '.PDF', '.docx', '.DOCX'}
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}

def is_valid_document(file_path: str) -> bool:
    """
    Check if a file has a supported document extension.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if the file has a supported extension, False otherwise
    """
    _, ext = os.path.splitext(file_path)
    return ext.lower() in {'.pdf', '.docx'}

def is_valid_image(file_path: str) -> bool:
    """
    Check if a file has a supported image extension.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if the file has a supported extension, False otherwise
    """
    _, ext = os.path.splitext(file_path)
    return ext.lower() in {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}

def save_uploaded_file(uploaded_file: Any, directory: str) -> Tuple[bool, str]:
    """
    Save an uploaded file to the specified directory.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        directory: Directory to save the file to
        
    Returns:
        Tuple of (success, file_path_or_error_message)
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Get the file path
        file_path = os.path.join(directory, uploaded_file.name)
        
        # Write the file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        logger.info(f"Saved uploaded file: {file_path}")
        return True, file_path
    except Exception as e:
        error_msg = f"Error saving file: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def create_temp_file(content: bytes, file_extension: str = '.tmp') -> Tuple[bool, str]:
    """
    Create a temporary file with the given content.
    
    Args:
        content: Binary content to write to the file
        file_extension: Extension for the temporary file
        
    Returns:
        Tuple of (success, file_path_or_error_message)
    """
    try:
        # Create a temporary file with the specified extension
        fd, temp_path = tempfile.mkstemp(suffix=file_extension)
        
        # Write the content
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        
        logger.info(f"Created temporary file: {temp_path}")
        return True, temp_path
    except Exception as e:
        error_msg = f"Error creating temporary file: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def delete_file(file_path: str) -> Tuple[bool, str]:
    """
    Delete a file at the specified path.
    
    Args:
        file_path: Path to the file to delete
        
    Returns:
        Tuple of (success, message)
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
            return True, f"Successfully deleted file: {file_path}"
        else:
            return False, f"File not found: {file_path}"
    except Exception as e:
        error_msg = f"Error deleting file: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def get_file_hash(file_path: str) -> str:
    """
    Get a hash of the file contents.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hash string
    """
    import hashlib
    
    try:
        with open(file_path, "rb") as f:
            file_hash = hashlib.md5()
            chunk = f.read(8192)
            while chunk:
                file_hash.update(chunk)
                chunk = f.read(8192)
        return file_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating file hash: {str(e)}")
        return ""

def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in MB
    """
    try:
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        return size_mb
    except Exception as e:
        logger.error(f"Error getting file size: {str(e)}")
        return 0.0

def clean_temp_files(directory: str, max_age_hours: int = 24) -> Tuple[int, List[str]]:
    """
    Clean temporary files older than the specified age.
    
    Args:
        directory: Directory containing temporary files
        max_age_hours: Maximum age in hours
        
    Returns:
        Tuple of (number of files deleted, list of deleted files)
    """
    import time
    
    try:
        if not os.path.exists(directory):
            return 0, []
            
        current_time = time.time()
        max_age_seconds = max_age_hours * 60 * 60
        
        deleted_files = []
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            # Skip directories
            if os.path.isdir(file_path):
                continue
                
            # Get file age
            file_age_seconds = current_time - os.path.getmtime(file_path)
            
            # Delete if older than max age
            if file_age_seconds > max_age_seconds:
                os.remove(file_path)
                deleted_files.append(file_path)
                logger.info(f"Deleted old temporary file: {file_path}")
        
        return len(deleted_files), deleted_files
    except Exception as e:
        logger.error(f"Error cleaning temporary files: {str(e)}")
        return 0, []