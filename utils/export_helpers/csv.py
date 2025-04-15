"""
CSV export functionality for knowledge base data.
"""

import os
import csv
import json
import tempfile
import shutil
import datetime
from typing import Optional, Any, Callable
from io import BytesIO
import zipfile

from .common import logger

def export_to_csv(
    book_manager: Any, 
    knowledge_base: Any,
    include_metadata: bool = True,
    include_content: bool = True,
    include_embeddings: bool = False,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> bytes:
    """
    Export knowledge base to CSV format (zipped).
    
    Args:
        book_manager: BookManager instance
        knowledge_base: KnowledgeBase instance
        include_metadata: Whether to include book metadata
        include_content: Whether to include chunk content
        include_embeddings: Whether to include embedding vectors
        progress_callback: Optional callback for progress updates
        
    Returns:
        Bytes data for the zip file
    """
    # Get indexed books
    kb_book_ids = knowledge_base.get_indexed_book_ids()
    total_books = len(kb_book_ids)
    
    if progress_callback:
        progress_callback(0.1, f"Exporting {total_books} books to CSV")
    
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create CSV files
        books_csv_path = os.path.join(temp_dir, "books.csv")
        chunks_csv_path = os.path.join(temp_dir, "chunks.csv")
        embeddings_csv_path = os.path.join(temp_dir, "embeddings.csv")
        book_ids_csv_path = os.path.join(temp_dir, "book_ids.csv")
        metadata_path = os.path.join(temp_dir, "metadata.json")
        errors_csv_path = os.path.join(temp_dir, "errors.csv")
        debug_info_path = os.path.join(temp_dir, "debug_info.txt")
        
        # Log debug information
        with open(debug_info_path, 'w', encoding='utf-8') as f:
            f.write("Export Debug Information\n")
            f.write("=======================\n\n")
            f.write(f"Export Date: {datetime.datetime.now().isoformat()}\n")
            f.write(f"Include Metadata: {include_metadata}\n")
            f.write(f"Include Content: {include_content}\n")
            f.write(f"Include Embeddings: {include_embeddings}\n\n")
            f.write(f"Book IDs in Knowledge Base: {kb_book_ids}\n\n")
            f.write(f"Knowledge Base Stats:\n")
            kb_stats = knowledge_base.get_stats()
            for key, value in kb_stats.items():
                f.write(f"  {key}: {value}\n")
        
        # Write metadata
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump({
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
            }, f, indent=2)
        
        # Write book_ids CSV to track all IDs in knowledge base
        with open(book_ids_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['index', 'book_id'])
            for i, book_id in enumerate(kb_book_ids):
                writer.writerow([i+1, book_id])
        
        # Track errors
        errors = []
        
        # Track found books
        found_books = False
        content_samples = []
        
        # Write books CSV
        with open(books_csv_path, 'w', newline='', encoding='utf-8') as f:
            if include_metadata:
                fieldnames = ['id', 'title', 'author', 'categories']
            else:
                fieldnames = ['id', 'title']
                
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, book_id in enumerate(kb_book_ids):
                # Calculate progress
                progress = 0.1 + (0.3 * (i / total_books)) if total_books > 0 else 0.2
                if progress_callback:
                    progress_callback(progress, f"Processing book {i+1}/{total_books} metadata")
                
                try:
                    book = book_manager.get_book(book_id)
                    if book:
                        found_books = True
                        row = {
                            'id': book['id'],
                            'title': book['title']
                        }
                        
                        if include_metadata:
                            row['author'] = book.get('author', '')
                            row['categories'] = ','.join(book.get('categories', []))
                            
                        writer.writerow(row)
                    else:
                        errors.append({
                            'book_id': book_id,
                            'error': 'Book not found in book manager'
                        })
                except Exception as e:
                    errors.append({
                        'book_id': book_id,
                        'error': str(e)
                    })
        
        # Write chunks CSV if content is included
        if include_content:
            with open(chunks_csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'book_id', 'content'])
                writer.writeheader()
                
                chunk_id = 0
                for i, book_id in enumerate(kb_book_ids):
                    # Update progress
                    progress = 0.1 + (0.6 * (i / total_books))
                    if progress_callback:
                        progress_callback(progress, f"Processing book {i+1}/{total_books} chunks")
                    
                    # Get chunks
                    chunks = knowledge_base.get_document_chunks(book_id)
                    
                    if chunks:
                        for chunk in chunks:
                            row = {
                                'id': chunk_id,
                                'book_id': book_id,
                                'content': getattr(chunk, 'page_content', str(chunk))
                            }
                            writer.writerow(row)
                            chunk_id += 1
        
        # Write embeddings CSV if requested
        if include_embeddings:
            with open(embeddings_csv_path, 'w', newline='', encoding='utf-8') as f:
                # First determine embedding dimension
                sample_chunk = None
                for book_id in kb_book_ids:
                    chunks = knowledge_base.get_document_chunks(book_id)
                    if chunks and hasattr(chunks[0], 'embedding'):
                        sample_chunk = chunks[0]
                        break
                
                if sample_chunk and hasattr(sample_chunk, 'embedding'):
                    # Create header with embedding dimensions
                    embedding_dim = len(sample_chunk.embedding)
                    fieldnames = ['chunk_id'] + [f'dim_{i}' for i in range(embedding_dim)]
                    
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    # Write embeddings
                    chunk_id = 0
                    for i, book_id in enumerate(kb_book_ids):
                        # Update progress
                        progress = 0.7 + (0.2 * (i / total_books))
                        if progress_callback:
                            progress_callback(progress, f"Processing book {i+1}/{total_books} embeddings")
                        
                        # Get chunks
                        chunks = knowledge_base.get_document_chunks(book_id)
                        
                        if chunks:
                            for chunk in chunks:
                                if hasattr(chunk, 'embedding'):
                                    row = {'chunk_id': chunk_id}
                                    for j, val in enumerate(chunk.embedding):
                                        row[f'dim_{j}'] = val
                                    writer.writerow(row)
                                chunk_id += 1
        
        # Create a zip file in memory
        if progress_callback:
            progress_callback(0.9, "Creating ZIP archive")
            
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(metadata_path, arcname="metadata.json")
            zip_file.write(books_csv_path, arcname="books.csv")
            
            if include_content and os.path.exists(chunks_csv_path):
                zip_file.write(chunks_csv_path, arcname="chunks.csv")
                
            if include_embeddings and os.path.exists(embeddings_csv_path):
                zip_file.write(embeddings_csv_path, arcname="embeddings.csv")
                
            # Add a readme
            readme_content = """# Knowledge Base Export

This ZIP archive contains CSV files exported from the Knowledge Base:

- `metadata.json`: Export information and statistics
- `books.csv`: Book information
- `chunks.csv`: Text chunks from the knowledge base
- `embeddings.csv`: Vector embeddings for chunks (if included)

"""
            zip_file.writestr("README.md", readme_content)
        
        if progress_callback:
            progress_callback(0.95, "Finalizing CSV export")
            
        return zip_buffer.getvalue()
            
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
