"""
SQLite export functionality for knowledge base data.
"""

import os
import json
import sqlite3
import tempfile
import datetime
from typing import Optional, Any, Callable

from .common import logger

def export_to_sqlite(
    book_manager: Any, 
    knowledge_base: Any,
    include_metadata: bool = True,
    include_content: bool = True,
    include_embeddings: bool = False,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> bytes:
    """
    Export knowledge base to SQLite database.
    
    Args:
        book_manager: BookManager instance
        knowledge_base: KnowledgeBase instance
        include_metadata: Whether to include book metadata
        include_content: Whether to include chunk content
        include_embeddings: Whether to include embedding vectors
        progress_callback: Optional callback for progress updates
        
    Returns:
        Bytes data for the SQLite database
    """
    # Get indexed books
    kb_book_ids = knowledge_base.get_indexed_book_ids()
    total_books = len(kb_book_ids)
    
    if progress_callback:
        progress_callback(0.1, f"Exporting {total_books} books to SQLite")
    
    # Create a temporary file for the database
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_path = db_file.name
    db_file.close()
    
    try:
        # Create database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
        CREATE TABLE export_metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE books (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT,
            categories TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id TEXT,
            content TEXT,
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE kb_book_ids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id TEXT NOT NULL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE export_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id TEXT,
            error_message TEXT
        )
        ''')
        
        if include_embeddings:
            cursor.execute('''
            CREATE TABLE embeddings (
                chunk_id INTEGER PRIMARY KEY,
                embedding BLOB,
                FOREIGN KEY (chunk_id) REFERENCES chunks(id)
            )
            ''')
        
        # Insert metadata
        kb_stats = knowledge_base.get_stats()
        metadata = {
            'generated_at': datetime.datetime.now().isoformat(),
            'vector_store_type': knowledge_base.vector_store_type,
            'book_count': str(kb_stats.get('book_count', 0)),
            'chunk_count': str(kb_stats.get('chunk_count', 0)),
            'dimensions': str(kb_stats.get('dimensions', 0)),
            'include_metadata': str(include_metadata),
            'include_content': str(include_content),
            'include_embeddings': str(include_embeddings),
            'export_options': json.dumps({
                'include_metadata': include_metadata,
                'include_content': include_content,
                'include_embeddings': include_embeddings
            })
        }
        
        for key, value in metadata.items():
            cursor.execute(
                'INSERT INTO export_metadata (key, value) VALUES (?, ?)',
                (key, value)
            )
        
        # Insert all book IDs from knowledge base
        for i, book_id in enumerate(kb_book_ids):
            cursor.execute(
                'INSERT INTO kb_book_ids (book_id) VALUES (?)',
                (book_id,)
            )
        
        # Track content chunks for unknown books
        content_samples = []
        
        # Track if we found any books
        found_books = False
        
        # Insert books
        for i, book_id in enumerate(kb_book_ids):
            # Calculate progress percentage
            progress = 0.1 + (0.3 * (i / total_books)) if total_books > 0 else 0.2
            
            try:
                book = book_manager.get_book(book_id)
                
                if book:
                    found_books = True
                    if progress_callback:
                        progress_callback(progress, f"Processing book {i+1}/{total_books}: {book['title']}")
                    
                    # Insert book
                    cursor.execute(
                        'INSERT INTO books (id, title, author, categories) VALUES (?, ?, ?, ?)',
                        (
                            book['id'],
                            book['title'],
                            book.get('author', '') if include_metadata else '',
                            ','.join(book.get('categories', [])) if include_metadata else ''
                        )
                    )
                    
                    # Insert chunks if content is included
                    if include_content or include_embeddings:
                        chunks = knowledge_base.get_document_chunks(book_id)
                        
                        if chunks:
                            # Save some samples in case no books are found later
                            if len(content_samples) < 5:
                                content_samples.extend(chunks[:5 - len(content_samples)])
                                
                            for chunk in chunks:
                                content = getattr(chunk, 'page_content', str(chunk)) if include_content else ''
                                
                                cursor.execute(
                                    'INSERT INTO chunks (book_id, content) VALUES (?, ?)',
                                    (book['id'], content)
                                )
                                
                                chunk_id = cursor.lastrowid
                                
                                # Insert embedding if requested
                                if include_embeddings and hasattr(chunk, 'embedding'):
                                    # Convert embedding to bytes
                                    embedding_bytes = json.dumps(chunk.embedding).encode('utf-8')
                                    
                                    cursor.execute(
                                        'INSERT INTO embeddings (chunk_id, embedding) VALUES (?, ?)',
                                        (chunk_id, embedding_bytes)
                                    )
                else:
                    # Book not found in book manager
                    cursor.execute(
                        'INSERT INTO export_errors (book_id, error_message) VALUES (?, ?)',
                        (book_id, "Book not found in book manager")
                    )
                    
                    if progress_callback:
                        progress_callback(progress, f"Book ID {book_id} not found in book manager")
                    
                    # Try to get content samples anyway
                    if include_content or include_embeddings:
                        chunks = knowledge_base.get_document_chunks(book_id)
                        if chunks and len(chunks) > 0:
                            if len(content_samples) < 5:
                                content_samples.extend(chunks[:5 - len(content_samples)])
            
            except Exception as e:
                # Log error
                cursor.execute(
                    'INSERT INTO export_errors (book_id, error_message) VALUES (?, ?)',
                    (book_id, str(e))
                )
                
                logger.error(f"Error processing book ID {book_id}: {str(e)}")
                if progress_callback:
                    progress_callback(progress, f"Error processing book ID {book_id}: {str(e)}")
        
        # If no books were found but we have content, add a placeholder book
        if not found_books and content_samples and (include_content or include_embeddings):
            # Add a placeholder book
            cursor.execute(
                'INSERT INTO books (id, title, author, categories) VALUES (?, ?, ?, ?)',
                ('placeholder', 'Content Samples', '', '')
            )
            
            # Insert content samples
            for i, chunk in enumerate(content_samples[:5]):
                content = getattr(chunk, 'page_content', str(chunk)) if include_content else ''
                
                cursor.execute(
                    'INSERT INTO chunks (book_id, content) VALUES (?, ?)',
                    ('placeholder', content)
                )
                
                chunk_id = cursor.lastrowid
                
                # Insert embedding if requested
                if include_embeddings and hasattr(chunk, 'embedding'):
                    # Convert embedding to bytes
                    embedding_bytes = json.dumps(chunk.embedding).encode('utf-8')
                    
                    cursor.execute(
                        'INSERT INTO embeddings (chunk_id, embedding) VALUES (?, ?)',
                        (chunk_id, embedding_bytes)
                    )
        
        # Create indices for better performance
        cursor.execute('CREATE INDEX idx_chunks_book_id ON chunks(book_id)')
        
        # Commit changes
        conn.commit()
        conn.close()
        
        if progress_callback:
            progress_callback(0.9, "Reading database file")
        
        # Read the database file
        with open(db_path, 'rb') as f:
            db_data = f.read()
            
        if progress_callback:
            progress_callback(0.95, "Finalizing SQLite export")
        
        return db_data
    
    finally:
        # Clean up temporary file
        if os.path.exists(db_path):
            os.unlink(db_path)
