"""
Utility functions for the knowledge base.
"""

import os
import re
import json
import uuid
import shutil
from typing import List, Dict, Any, Optional, Union

from utils.logger import get_logger
from knowledge_base.config import (
    DEFAULT_KB_DIR, DEFAULT_VECTOR_DIR, DEFAULT_DATA_DIR
)

# Initialize logger
logger = get_logger(__name__)

def generate_id() -> str:
    """
    Generate a unique ID.
    
    Returns:
        Unique ID string
    """
    return str(uuid.uuid4())

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to ensure it's valid.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Replace invalid characters with underscores
    s = re.sub(r'[\\/:*?"<>|]', '_', filename)
    
    # Remove any other non-alphanumeric characters except underscores, dots, and hyphens
    s = re.sub(r'[^\w.-]', '_', s)
    
    # Ensure the filename is not empty
    if not s:
        s = 'file'
    
    return s

def save_document_to_disk(
    document: Dict[str, Any],
    directory: str = DEFAULT_DATA_DIR
) -> str:
    """
    Save a document to disk.
    
    Args:
        document: Document to save
        directory: Directory to save to
        
    Returns:
        Path to saved document
    """
    if not document:
        return ""
    
    # Ensure directory exists
    os.makedirs(directory, exist_ok=True)
    
    # Generate a filename
    doc_id = document.get("id") or generate_id()
    document["id"] = doc_id  # Ensure ID is set
    
    # Sanitize ID for filename
    filename = sanitize_filename(doc_id) + ".json"
    filepath = os.path.join(directory, filename)
    
    # Save document
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(document, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Saved document to {filepath}")
    return filepath

def load_document_from_disk(
    doc_id: str,
    directory: str = DEFAULT_DATA_DIR
) -> Optional[Dict[str, Any]]:
    """
    Load a document from disk.
    
    Args:
        doc_id: Document ID
        directory: Directory to load from
        
    Returns:
        Loaded document or None if not found
    """
    # Sanitize ID for filename
    filename = sanitize_filename(doc_id) + ".json"
    filepath = os.path.join(directory, filename)
    
    # Check if file exists
    if not os.path.exists(filepath):
        logger.warning(f"Document file not found: {filepath}")
        return None
    
    # Load document
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            document = json.load(f)
        
        logger.info(f"Loaded document from {filepath}")
        return document
    
    except Exception as e:
        logger.error(f"Error loading document from {filepath}: {str(e)}")
        return None

def delete_document_from_disk(
    doc_id: str, 
    directory: str = DEFAULT_DATA_DIR
) -> bool:
    """
    Delete a document from disk.
    
    Args:
        doc_id: Document ID
        directory: Directory to delete from
        
    Returns:
        True if deleted, False otherwise
    """
    # Sanitize ID for filename
    filename = sanitize_filename(doc_id) + ".json"
    filepath = os.path.join(directory, filename)
    
    # Check if file exists
    if not os.path.exists(filepath):
        logger.warning(f"Document file not found for deletion: {filepath}")
        return False
    
    # Delete file
    try:
        os.remove(filepath)
        logger.info(f"Deleted document file: {filepath}")
        return True
    
    except Exception as e:
        logger.error(f"Error deleting document file {filepath}: {str(e)}")
        return False

def list_documents_on_disk(
    directory: str = DEFAULT_DATA_DIR
) -> List[Dict[str, Any]]:
    """
    List all documents stored on disk.
    
    Args:
        directory: Directory to list from
        
    Returns:
        List of document metadata
    """
    if not os.path.exists(directory):
        logger.warning(f"Document directory not found: {directory}")
        return []
    
    documents = []
    
    # List JSON files
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    document = json.load(f)
                
                # Add document metadata to list
                documents.append({
                    "id": document.get("id", ""),
                    "metadata": document.get("metadata", {})
                })
            
            except Exception as e:
                logger.error(f"Error reading document file {filepath}: {str(e)}")
    
    logger.info(f"Found {len(documents)} documents on disk")
    return documents

def clean_knowledge_base(
    kb_dir: str = DEFAULT_KB_DIR,
    vector_dir: str = DEFAULT_VECTOR_DIR,
    data_dir: str = DEFAULT_DATA_DIR
) -> bool:
    """
    Clean all knowledge base files.
    
    Args:
        kb_dir: Knowledge base directory
        vector_dir: Vector directory
        data_dir: Data directory
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Clean vector directory
        if os.path.exists(vector_dir):
            shutil.rmtree(vector_dir)
            os.makedirs(vector_dir, exist_ok=True)
        
        # Clean data directory
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)
            os.makedirs(data_dir, exist_ok=True)
        
        logger.info("Knowledge base cleaned")
        return True
    
    except Exception as e:
        logger.error(f"Error cleaning knowledge base: {str(e)}")
        return False