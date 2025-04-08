"""
File helper functions for handling various file operations.
"""

import os
import time
import shutil
import hashlib
import tempfile
from typing import Dict, List, Any, Optional, BinaryIO, Union

def is_valid_document(file_path: str, supported_extensions: Optional[List[str]] = None) -> bool:
    """
    Check if a file is a valid document type.
    
    Args:
        file_path: Path to the file
        supported_extensions: List of supported file extensions (default: ['.pdf', '.docx'])
        
    Returns:
        True if the file is a valid document type, False otherwise
    """
    if not supported_extensions:
        supported_extensions = ['.pdf', '.docx']
    
    # Convert to lowercase for case-insensitive comparison
    supported_extensions = [ext.lower() for ext in supported_extensions]
    
    # Get file extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    return ext in supported_extensions

def save_uploaded_file(uploaded_file: Any, target_dir: str = "uploads") -> str:
    """
    Save an uploaded file to the filesystem.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        target_dir: Directory to save the file (default: 'uploads')
        
    Returns:
        Path to the saved file
    """
    # Create target directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    
    # Generate a unique filename with timestamp
    timestamp = int(time.time())
    filename = f"{timestamp}_{uploaded_file.name}"
    file_path = os.path.join(target_dir, filename)
    
    # Save the file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

def get_file_hash(file_path: str) -> str:
    """
    Calculate the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        SHA-256 hash as a hexadecimal string
    """
    if not os.path.exists(file_path):
        return ""
    
    # Calculate SHA-256 hash
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read the file in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()

def get_file_size_mb(file_path: str) -> float:
    """
    Get the size of a file in megabytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in megabytes
    """
    if not os.path.exists(file_path):
        return 0
    
    # Get file size in bytes
    size_bytes = os.path.getsize(file_path)
    
    # Convert to megabytes
    size_mb = size_bytes / (1024 * 1024)
    
    return size_mb

def clean_temp_files(temp_dir: Optional[str] = None, age_hours: int = 24) -> List[str]:
    """
    Clean temporary files older than a specified age.
    
    Args:
        temp_dir: Directory containing temporary files (default: system temp dir)
        age_hours: Age in hours after which files should be deleted (default: 24)
        
    Returns:
        List of deleted file paths
    """
    # Use system temp directory if none specified
    if not temp_dir:
        temp_dir = tempfile.gettempdir()
    
    # Current time
    current_time = time.time()
    
    # Age threshold in seconds
    age_threshold = age_hours * 3600
    
    # Files deleted
    deleted_files = []
    
    # Iterate through files in the directory
    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)
        
        # Skip directories
        if os.path.isdir(file_path):
            continue
        
        # Check if the file is a temporary file created by this application
        if not filename.startswith("temp_"):
            continue
        
        # Check file age
        file_age = current_time - os.path.getmtime(file_path)
        
        # Delete if older than threshold
        if file_age > age_threshold:
            try:
                os.unlink(file_path)
                deleted_files.append(file_path)
            except Exception:
                # Ignore errors when deleting files
                pass
    
    return deleted_files