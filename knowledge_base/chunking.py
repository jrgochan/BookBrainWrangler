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
    Split text into chunks with enhanced handling for various text formats.
    
    Args:
        text: Text to split
        chunk_size: Maximum chunk size in characters
        chunk_overlap: Overlap between chunks in characters
        split_by: How to split the text ('paragraph', 'sentence', 'character', 'hybrid')
        
    Returns:
        List of text chunks
    """
    if not text:
        logger.warning("Attempted to chunk empty text")
        return []
    
    # Clean text before chunking to ensure consistent patterns
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Restore paragraph breaks
    text = re.sub(r'(\. |\? |! )([A-Z])', r'.\n\n\2', text)
    
    # Log text length for debugging
    logger.info(f"Chunking text of length {len(text)} with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}, split_by={split_by}")
    
    # Auto-detect the best splitting method based on content
    if split_by == "auto":
        # Count paragraphs
        paragraph_count = len(re.split(r'\n\s*\n', text))
        # Count sentences
        sentence_count = len(re.split(r'(?<=[.!?])\s', text))
        
        logger.info(f"Text has approximately {paragraph_count} paragraphs and {sentence_count} sentences")
        
        # Choose method based on content structure
        if paragraph_count > 5:
            split_by = "paragraph"
            logger.info("Auto-selected paragraph splitting method")
        elif sentence_count > 10:
            split_by = "sentence"
            logger.info("Auto-selected sentence splitting method")
        else:
            split_by = "character"
            logger.info("Auto-selected character splitting method")
    
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
            chunk = text[i:i + chunk_size].strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
        
        logger.info(f"Character-based chunking created {len(chunks)} chunks")
        return chunks
    elif split_by == "hybrid":
        # Try paragraph splitting first
        segments = re.split(r'\n\s*\n', text)
        segments = [s.strip() for s in segments if s.strip()]
        
        # If paragraphs are too large, split them into sentences
        processed_segments = []
        for segment in segments:
            if len(segment) > chunk_size:
                # Split large paragraphs into sentences
                sentences = re.split(r'(?<=[.!?])\s', segment)
                sentences = [s.strip() for s in sentences if s.strip()]
                processed_segments.extend(sentences)
            else:
                processed_segments.append(segment)
        
        segments = processed_segments
        logger.info(f"Hybrid chunking created {len(segments)} initial segments")
    else:
        # Default to paragraph splitting
        split_pattern = r'\n\s*\n'
        logger.info(f"Using default paragraph splitting method")
    
    # Split text by pattern (except for character and hybrid methods)
    segments = []
    if split_by not in ["character", "hybrid"]:
        segments = re.split(split_pattern, text)
        segments = [s.strip() for s in segments if s.strip()]
    
    # Handle case where splitting produced no segments (common with PDFs)
    if not segments:
        logger.warning(f"Splitting with method '{split_by}' produced no segments, falling back to character method")
        # Fall back to character-based chunking
        chunks = []
        for i in range(0, len(text), chunk_size - chunk_overlap):
            chunk = text[i:i + chunk_size].strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
        
        logger.info(f"Fallback character-based chunking created {len(chunks)} chunks")
        return chunks
    
    chunks = []
    current_chunk = ""
    
    for segment in segments:
        # Skip empty segments
        if not segment.strip():
            continue
            
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
        
        # If the segment itself is larger than the chunk size, we need to split it
        if len(segment) > chunk_size:
            # First add any current chunk if it exists
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
            # Split the large segment into smaller chunks of chunk_size with overlap
            for i in range(0, len(segment), chunk_size - chunk_overlap):
                sub_chunk = segment[i:i + chunk_size]
                if i + chunk_size >= len(segment):  # This is the last sub-chunk
                    current_chunk = sub_chunk
                else:
                    chunks.append(sub_chunk)
        else:
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
        logger.warning("Chunking process created no chunks, falling back to basic truncation")
        chunks = [text[:chunk_size]]
    
    # Ensure minimum chunk size
    MIN_VIABLE_CHUNK_SIZE = 50  # Minimum number of characters to be considered a valid chunk
    chunks = [chunk for chunk in chunks if len(chunk) >= MIN_VIABLE_CHUNK_SIZE]
    
    # If we removed all chunks due to minimum size, keep at least one
    if not chunks and text:
        chunks = [text[:chunk_size]]
    
    logger.info(f"Chunked text into {len(chunks)} chunks (min size={MIN_VIABLE_CHUNK_SIZE})")
    
    # Log the size distribution of chunks for debugging
    if chunks:
        chunk_sizes = [len(chunk) for chunk in chunks]
        avg_size = sum(chunk_sizes) / len(chunks)
        min_size = min(chunk_sizes)
        max_size = max(chunk_sizes)
        logger.info(f"Chunk size distribution - avg: {avg_size:.1f}, min: {min_size}, max: {max_size}")
    
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
    for i, chunk_content in enumerate(text_chunks):
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
            "text": chunk_content,
            "metadata": chunk_metadata
        }
        
        chunks.append(chunk)
    
    logger.info(f"Created {len(chunks)} document chunks")
    return chunks