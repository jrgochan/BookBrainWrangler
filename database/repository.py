"""
Repository module for database operations.
Provides an abstraction layer for database operations.
"""

import json
import sqlite3
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime

from utils.logger import get_logger
from database.connection import get_connection
from database.utils import execute_query, execute_insert, table_exists
from database.models import Book, BookContent, Category, KnowledgeBaseEntry

# Get a logger for this module
logger = get_logger(__name__)

class BookRepository:
    """Repository for book-related database operations."""
    
    @staticmethod
    def add_book(book: Book) -> Optional[int]:
        """
        Add a new book to the database.
        
        Args:
            book: Book model to add
            
        Returns:
            ID of the newly added book or None if failed
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Start a transaction
            conn.execute("BEGIN TRANSACTION")
            
            # Convert metadata to JSON
            metadata_json = json.dumps(book.metadata or {})
            
            # Insert book record
            cursor.execute(
                """
                INSERT INTO books (title, author, file_path, content_length, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (book.title, book.author, book.file_path, book.content_length, metadata_json)
            )
            
            # Get the book ID
            book_id = cursor.lastrowid
            
            # Insert book categories
            for category in (book.categories or []):
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO book_categories (book_id, category_name)
                    VALUES (?, ?)
                    """,
                    (book_id, category)
                )
            
            # Commit transaction
            conn.commit()
            conn.close()
            
            return book_id
            
        except sqlite3.Error as e:
            logger.error(f"Error adding book: {str(e)}")
            if conn:
                conn.rollback()
                conn.close()
            return None
    
    @staticmethod
    def update_book(book: Book) -> bool:
        """
        Update an existing book in the database.
        
        Args:
            book: Book model with updated values
            
        Returns:
            True if update was successful, False otherwise
        """
        if book.id is None:
            logger.error("Cannot update book: Missing book ID")
            return False
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Start a transaction
            conn.execute("BEGIN TRANSACTION")
            
            # Convert metadata to JSON
            metadata_json = json.dumps(book.metadata or {})
            
            # Update book record
            cursor.execute(
                """
                UPDATE books
                SET title = ?, author = ?, file_path = ?, 
                    content_length = ?, last_modified = CURRENT_TIMESTAMP,
                    metadata = ?
                WHERE id = ?
                """,
                (book.title, book.author, book.file_path, 
                 book.content_length, metadata_json, book.id)
            )
            
            # Delete existing book categories
            cursor.execute(
                "DELETE FROM book_categories WHERE book_id = ?",
                (book.id,)
            )
            
            # Insert updated book categories
            for category in (book.categories or []):
                cursor.execute(
                    """
                    INSERT INTO book_categories (book_id, category_name)
                    VALUES (?, ?)
                    """,
                    (book.id, category)
                )
            
            # Commit transaction
            conn.commit()
            conn.close()
            
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error updating book: {str(e)}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    @staticmethod
    def delete_book(book_id: int) -> bool:
        """
        Delete a book from the database.
        
        Args:
            book_id: ID of the book to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Delete the book (foreign key cascade will handle related records)
            cursor.execute(
                "DELETE FROM books WHERE id = ?",
                (book_id,)
            )
            
            deleted = cursor.rowcount > 0
            
            conn.commit()
            conn.close()
            
            return deleted
            
        except sqlite3.Error as e:
            logger.error(f"Error deleting book: {str(e)}")
            return False
    
    @staticmethod
    def get_book(book_id: int) -> Optional[Book]:
        """
        Get a book by its ID.
        
        Args:
            book_id: ID of the book to retrieve
            
        Returns:
            Book object or None if not found
        """
        try:
            # Get book record
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT id, title, author, file_path, content_length,
                       date_added, last_modified, metadata
                FROM books
                WHERE id = ?
                """,
                (book_id,)
            )
            
            book_row = cursor.fetchone()
            
            if not book_row:
                conn.close()
                return None
            
            # Get book categories
            cursor.execute(
                """
                SELECT category_name
                FROM book_categories
                WHERE book_id = ?
                """,
                (book_id,)
            )
            
            categories = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            # Parse metadata JSON
            try:
                metadata = json.loads(book_row[7]) if book_row[7] else {}
            except (json.JSONDecodeError, TypeError):
                metadata = {}
            
            # Create and return Book object
            return Book(
                id=book_row[0],
                title=book_row[1],
                author=book_row[2],
                file_path=book_row[3],
                content_length=book_row[4],
                date_added=datetime.fromisoformat(book_row[5]) if book_row[5] else None,
                last_modified=datetime.fromisoformat(book_row[6]) if book_row[6] else None,
                categories=categories,
                metadata=metadata
            )
            
        except sqlite3.Error as e:
            logger.error(f"Error getting book: {str(e)}")
            return None
    
    @staticmethod
    def get_all_books() -> List[Book]:
        """
        Get all books in the database.
        
        Returns:
            List of Book objects
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get all book records
            cursor.execute(
                """
                SELECT id, title, author, file_path, content_length,
                       date_added, last_modified, metadata
                FROM books
                ORDER BY title
                """
            )
            
            book_rows = cursor.fetchall()
            books = []
            
            for book_row in book_rows:
                book_id = book_row[0]
                
                # Get book categories
                cursor.execute(
                    """
                    SELECT category_name
                    FROM book_categories
                    WHERE book_id = ?
                    """,
                    (book_id,)
                )
                
                categories = [row[0] for row in cursor.fetchall()]
                
                # Parse metadata JSON
                try:
                    metadata = json.loads(book_row[7]) if book_row[7] else {}
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
                
                # Create and add Book object
                books.append(Book(
                    id=book_id,
                    title=book_row[1],
                    author=book_row[2],
                    file_path=book_row[3],
                    content_length=book_row[4],
                    date_added=datetime.fromisoformat(book_row[5]) if book_row[5] else None,
                    last_modified=datetime.fromisoformat(book_row[6]) if book_row[6] else None,
                    categories=categories,
                    metadata=metadata
                ))
            
            conn.close()
            return books
            
        except sqlite3.Error as e:
            logger.error(f"Error getting all books: {str(e)}")
            return []
    
    @staticmethod
    def search_books(query: str = "", category: Optional[str] = None) -> List[Book]:
        """
        Search books by title, author, or category.
        
        Args:
            query: Search string for title or author
            category: Filter by category name
            
        Returns:
            List of Book objects matching the search criteria
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Build the query based on search parameters
            sql_query = """
                SELECT DISTINCT b.id, b.title, b.author, b.file_path, 
                       b.content_length, b.date_added, b.last_modified, b.metadata
                FROM books b
            """
            
            params = []
            
            # Add category filter if specified
            if category:
                sql_query += """
                    INNER JOIN book_categories bc ON b.id = bc.book_id
                    WHERE bc.category_name = ?
                """
                params.append(category)
            
            # Add title/author search if specified
            if query:
                if category:
                    sql_query += " AND"
                else:
                    sql_query += " WHERE"
                
                sql_query += """
                    (b.title LIKE ? OR b.author LIKE ?)
                """
                params.extend([f"%{query}%", f"%{query}%"])
            
            # Add order by clause
            sql_query += " ORDER BY b.title"
            
            # Execute the query
            cursor.execute(sql_query, params)
            book_rows = cursor.fetchall()
            
            books = []
            for book_row in book_rows:
                book_id = book_row[0]
                
                # Get book categories
                cursor.execute(
                    """
                    SELECT category_name
                    FROM book_categories
                    WHERE book_id = ?
                    """,
                    (book_id,)
                )
                
                categories = [row[0] for row in cursor.fetchall()]
                
                # Parse metadata JSON
                try:
                    metadata = json.loads(book_row[7]) if book_row[7] else {}
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
                
                # Create and add Book object
                books.append(Book(
                    id=book_id,
                    title=book_row[1],
                    author=book_row[2],
                    file_path=book_row[3],
                    content_length=book_row[4],
                    date_added=datetime.fromisoformat(book_row[5]) if book_row[5] else None,
                    last_modified=datetime.fromisoformat(book_row[6]) if book_row[6] else None,
                    categories=categories,
                    metadata=metadata
                ))
            
            conn.close()
            return books
            
        except sqlite3.Error as e:
            logger.error(f"Error searching books: {str(e)}")
            return []
    
    @staticmethod
    def get_all_categories() -> List[str]:
        """
        Get all unique categories in the database.
        
        Returns:
            List of category names
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT DISTINCT category_name
                FROM book_categories
                ORDER BY category_name
                """
            )
            
            categories = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return categories
            
        except sqlite3.Error as e:
            logger.error(f"Error getting categories: {str(e)}")
            return []
    
    @staticmethod
    def save_book_content(book_id: int, content: str, format: str = "text") -> bool:
        """
        Save or update book content.
        
        Args:
            book_id: ID of the book
            content: Text content of the book
            format: Format of the content (text, html, markdown, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Check if content already exists
            cursor.execute(
                "SELECT id FROM book_contents WHERE book_id = ?",
                (book_id,)
            )
            
            content_row = cursor.fetchone()
            
            if content_row:
                # Update existing content
                cursor.execute(
                    """
                    UPDATE book_contents
                    SET content = ?, format = ?, extracted_at = CURRENT_TIMESTAMP
                    WHERE book_id = ?
                    """,
                    (content, format, book_id)
                )
            else:
                # Insert new content
                cursor.execute(
                    """
                    INSERT INTO book_contents (book_id, content, format)
                    VALUES (?, ?, ?)
                    """,
                    (book_id, content, format)
                )
            
            # Update content length in book record
            cursor.execute(
                """
                UPDATE books
                SET content_length = ?, last_modified = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (len(content), book_id)
            )
            
            conn.commit()
            conn.close()
            
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error saving book content: {str(e)}")
            return False
    
    @staticmethod
    def get_book_content(book_id: int) -> Optional[str]:
        """
        Get the text content of a book.
        
        Args:
            book_id: ID of the book
            
        Returns:
            Book content as a string or None if not found
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT content FROM book_contents WHERE book_id = ?",
                (book_id,)
            )
            
            content_row = cursor.fetchone()
            conn.close()
            
            if content_row:
                return content_row[0]
            else:
                return None
            
        except sqlite3.Error as e:
            logger.error(f"Error getting book content: {str(e)}")
            return None

class KnowledgeBaseRepository:
    """Repository for knowledge base related database operations."""
    
    @staticmethod
    def add_to_knowledge_base(book_id: int) -> bool:
        """
        Add a book to the knowledge base.
        
        Args:
            book_id: ID of the book to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Check if book exists
            cursor.execute(
                "SELECT id FROM books WHERE id = ?",
                (book_id,)
            )
            
            if not cursor.fetchone():
                logger.error(f"Cannot add to knowledge base: Book {book_id} not found")
                conn.close()
                return False
            
            # Check if book is already in knowledge base
            cursor.execute(
                "SELECT id FROM knowledge_base WHERE book_id = ?",
                (book_id,)
            )
            
            if cursor.fetchone():
                # Update existing entry
                cursor.execute(
                    """
                    UPDATE knowledge_base
                    SET is_indexed = 0, last_indexed = NULL
                    WHERE book_id = ?
                    """,
                    (book_id,)
                )
            else:
                # Insert new entry
                cursor.execute(
                    """
                    INSERT INTO knowledge_base (book_id, is_indexed)
                    VALUES (?, 0)
                    """,
                    (book_id,)
                )
            
            conn.commit()
            conn.close()
            
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error adding to knowledge base: {str(e)}")
            return False
    
    @staticmethod
    def remove_from_knowledge_base(book_id: int) -> bool:
        """
        Remove a book from the knowledge base.
        
        Args:
            book_id: ID of the book to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM knowledge_base WHERE book_id = ?",
                (book_id,)
            )
            
            removed = cursor.rowcount > 0
            
            conn.commit()
            conn.close()
            
            return removed
            
        except sqlite3.Error as e:
            logger.error(f"Error removing from knowledge base: {str(e)}")
            return False
    
    @staticmethod
    def get_knowledge_base_books() -> List[int]:
        """
        Get IDs of all books in the knowledge base.
        
        Returns:
            List of book IDs in the knowledge base
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT book_id FROM knowledge_base"
            )
            
            book_ids = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            return book_ids
            
        except sqlite3.Error as e:
            logger.error(f"Error getting knowledge base books: {str(e)}")
            return []
    
    @staticmethod
    def mark_as_indexed(book_id: int, chunk_count: int = 0) -> bool:
        """
        Mark a book as indexed in the knowledge base.
        
        Args:
            book_id: ID of the book
            chunk_count: Number of chunks created during indexing
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                UPDATE knowledge_base
                SET is_indexed = 1, last_indexed = CURRENT_TIMESTAMP, chunk_count = ?
                WHERE book_id = ?
                """,
                (chunk_count, book_id)
            )
            
            updated = cursor.rowcount > 0
            
            conn.commit()
            conn.close()
            
            return updated
            
        except sqlite3.Error as e:
            logger.error(f"Error marking as indexed: {str(e)}")
            return False
    
    @staticmethod
    def get_knowledge_base_status(book_id: int) -> Dict[str, Any]:
        """
        Get the knowledge base status for a book.
        
        Args:
            book_id: ID of the book
            
        Returns:
            Dictionary with knowledge base status or empty dict if not found
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT is_indexed, last_indexed, chunk_count, added_at
                FROM knowledge_base
                WHERE book_id = ?
                """,
                (book_id,)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "is_indexed": bool(row[0]),
                    "last_indexed": row[1],
                    "chunk_count": row[2],
                    "added_at": row[3]
                }
            else:
                return {}
            
        except sqlite3.Error as e:
            logger.error(f"Error getting knowledge base status: {str(e)}")
            return {}