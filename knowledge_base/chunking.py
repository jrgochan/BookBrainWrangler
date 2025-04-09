"""
Text chunking module for Book Knowledge AI.
Provides functions for chunking text for the knowledge base.
"""

import re
from typing import List, Dict, Any, Optional, Union, Tuple

from utils.logger import get_logger
from knowledge_base.config import (
    DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP, DEFAULT_SPLIT_BY
)

# Initialize logger
logger = get_logger(__name__)

def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    split_by: str = DEFAULT_SPLIT_BY
) -> List[str]:
    """
    Split text into chunks.
    
    Args:
        text: Text to split
        chunk_size: Maximum chunk size in characters
        chunk_overlap: Overlap between chunks in characters
        split_by: How to split the text ('paragraph', 'sentence', 'character')
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    # Define split patterns based on split_by
    if split_by == "paragraph":
        # Split by double newline (paragraph)
        split_pattern = r'\n\s*\n'
    elif split_by == "sentence":
        # Split by sentence-ending punctuation followed by space or newline
        split_pattern = r'(?<=[.!?])\s'
    elif split_by == "character":
        # Split by character count without respect to boundaries
        chunks = []
        for i in range(0, len(text), chunk_size - chunk_overlap):
            chunks.append(text[i:i + chunk_size])
        return chunks
    else:
        # Default to paragraph splitting
        split_pattern = r'\n\s*\n'
    
    # Split text by pattern
    segments = re.split(split_pattern, text)
    segments = [s.strip() for s in segments if s.strip()]
    
    chunks = []
    current_chunk = ""
    
    for segment in segments:
        # If adding segment exceeds chunk size and we already have content,
        # add current chunk to list and start a new one
        if len(current_chunk) + len(segment) > chunk_size and current_chunk:
            chunks.append(current_chunk)
            
            # Start new chunk with overlap if possible
            if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                # Try to find a clean break point for the overlap
                overlap_text = current_chunk[-chunk_overlap:]
                
                # Find a space to break at in the overlap region
                space_pos = overlap_text.find(' ')
                if space_pos > 0:
                    current_chunk = current_chunk[-(chunk_overlap - space_pos):]
                else:
                    current_chunk = current_chunk[-chunk_overlap:]
            else:
                current_chunk = ""
        
        # Add segment to current chunk
        if current_chunk:
            current_chunk += " " + segment
        else:
            current_chunk = segment
        
        # If current chunk is already at/over chunk size, add it and reset
        if len(current_chunk) >= chunk_size:
            chunks.append(current_chunk)
            current_chunk = ""
    
    # Add any remaining content
    if current_chunk:
        chunks.append(current_chunk)
    
    # Handle empty result
    if not chunks:
        # If no chunks were created, create at least one with the original text,
        # truncated if needed
        chunks = [text[:chunk_size]]
    
    logger.info(f"Chunked text into {len(chunks)} chunks")
    return chunks

def chunk_document(
    document: Dict[str, Any],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    split_by: str = DEFAULT_SPLIT_BY
) -> List[Dict[str, Any]]:
    """
    Chunk a document into smaller parts.
    
    Args:
        document: Document to chunk
        chunk_size: Maximum chunk size in characters
        chunk_overlap: Overlap between chunks in characters
        split_by: How to split the text ('paragraph', 'sentence', 'character')
        
    Returns:
        List of document chunks with metadata
    """
    if not document or "text" not in document:
        return []
    
    text = document["text"]
    metadata = document.get("metadata", {})
    
    # Get document ID
    doc_id = document.get("id") or metadata.get("id")
    
    # Chunk the text
    text_chunks = chunk_text(
        text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        split_by=split_by
    )
    
    # Create chunks with metadata
    chunks = []
    for i, chunk_text in enumerate(text_chunks):
        # Clone metadata for each chunk
        chunk_metadata = metadata.copy()
        
        # Add chunk-specific metadata
        chunk_metadata["chunk_index"] = i
        chunk_metadata["chunk_count"] = len(text_chunks)
        
        if doc_id:
            chunk_metadata["document_id"] = doc_id
        
        # Create chunk document
        chunk = {
            "id": f"{doc_id}_chunk_{i}" if doc_id else f"chunk_{i}",
            "text": chunk_text,
            "metadata": chunk_metadata
        }
        
        chunks.append(chunk)
    
    logger.info(f"Created {len(chunks)} document chunks")
    return chunks