"""
JSON export functionality for knowledge base data.
"""

import json
import datetime
from typing import Optional, Dict, Any, Callable

from .common import logger

def export_to_json(
    book_manager: Any, 
    knowledge_base: Any,
    include_metadata: bool = True,
    include_content: bool = True,
    include_embeddings: bool = False,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Dict[str, Any]:
    """
    Export knowledge base to JSON format.
    
    Args:
        book_manager: BookManager instance
        knowledge_base: KnowledgeBase instance
        include_metadata: Whether to include book metadata
        include_content: Whether to include chunk content
        include_embeddings: Whether to include embedding vectors
        progress_callback: Optional callback for progress updates
        
    Returns:
        Dictionary to be JSON serialized
    """
    # Get indexed books
    kb_book_ids = knowledge_base.get_indexed_book_ids()
    total_books = len(kb_book_ids)
    
    if progress_callback:
        progress_callback(0.1, f"Exporting {total_books} books to JSON")
    
    # Get knowledge base stats
    kb_stats = knowledge_base.get_stats()
    
    # Create JSON structure
    export_data = {
        "metadata": {
            "generated_at": datetime.datetime.now().isoformat(),
            "vector_store_type": knowledge_base.vector_store_type,
            "book_count": kb_stats.get('book_count', 0),
            "chunk_count": kb_stats.get('chunk_count', 0),
            "dimensions": kb_stats.get('dimensions', 0),
            "export_options": {
                "include_metadata": include_metadata,
                "include_content": include_content,
                "include_embeddings": include_embeddings
            }
        },
        "book_ids_in_kb": kb_book_ids,
        "books": []
    }
    
    # Flag to track if we found any books
    found_books = False
    content_samples = []
    
    # Process each book
    for i, book_id in enumerate(kb_book_ids):
        # Calculate progress percentage
        progress = 0.1 + (0.8 * (i / total_books)) if total_books > 0 else 0.5
        
        try:
            # Get book details
            book = book_manager.get_book(book_id)
            
            if book:
                found_books = True
                if progress_callback:
                    progress_callback(progress, f"Processing book {i+1}/{total_books}: {book['title']}")
                
                # Book data
                book_data = {
                    "id": book['id'],
                    "title": book['title']
                }
                
                # Include metadata if requested
                if include_metadata:
                    book_data["author"] = book.get('author', '')
                    book_data["categories"] = book.get('categories', [])
                
                # Include content if requested
                if include_content or include_embeddings:
                    # Get chunks
                    chunks = knowledge_base.get_document_chunks(book_id)
                    
                    if chunks:
                        book_data["chunks"] = []
                        
                        # Store some content samples in case we need them later
                        if len(content_samples) < 5:
                            content_samples.extend(chunks[:5-len(content_samples)])
                        
                        for chunk in chunks:
                            chunk_data = {"id": getattr(chunk, 'id', f"chunk_{len(book_data['chunks'])}")}
                            
                            # Add content if requested
                            if include_content:
                                chunk_data["content"] = getattr(chunk, 'page_content', str(chunk))
                                
                            # Add embeddings if requested
                            if include_embeddings and hasattr(chunk, 'embedding'):
                                chunk_data["embedding"] = chunk.embedding
                                
                            book_data["chunks"].append(chunk_data)
                            
                # Add book to export data
                export_data["books"].append(book_data)
            else:
                # Book not found in book manager
                if progress_callback:
                    progress_callback(progress, f"Book ID {book_id} not found in book manager")
                
                # Try to get content samples anyway
                if include_content or include_embeddings:
                    chunks = knowledge_base.get_document_chunks(book_id)
                    if chunks and len(chunks) > 0:
                        if len(content_samples) < 5:
                            content_samples.extend(chunks[:5-len(content_samples)])
        
        except Exception as e:
            logger.error(f"Error processing book ID {book_id}: {str(e)}")
            if progress_callback:
                progress_callback(progress, f"Error processing book ID {book_id}: {str(e)}")
            
            # Add error information to export data
            export_data["books"].append({
                "id": book_id,
                "error": str(e)
            })
    
    # If no books were found but we have content chunks, add them to export data
    if not found_books and include_content and content_samples:
        export_data["content_samples"] = []
        for i, chunk in enumerate(content_samples[:5]):
            sample_data = {
                "id": f"sample_{i+1}",
                "content": getattr(chunk, 'page_content', str(chunk))
            }
            
            # Add embedding if requested
            if include_embeddings and hasattr(chunk, 'embedding'):
                sample_data["embedding"] = chunk.embedding
                
            export_data["content_samples"].append(sample_data)
    
    if progress_callback:
        progress_callback(0.95, "Finalizing JSON export")
    
    return export_data
