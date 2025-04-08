"""
Book Manager module for handling book operations.
"""

import os
import sqlite3
import json
import time
from typing import Dict, List, Any, Optional, Union
from database import get_connection
from loguru import logger

class BookManager:
    def __init__(self):
        """Initialize the BookManager with a database connection."""
        logger.info("Initializing BookManager")
        self._init_database()
    
    def _init_database(self):
        """Initialize the book database tables if they don't exist."""
        logger.debug("Initializing book database tables")
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Create books table
            logger.trace("Creating books table if not exists")
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                file_path TEXT,
                date_added TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create categories table
            logger.trace("Creating categories table if not exists")
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
            ''')
            
            # Create book_categories junction table
            logger.trace("Creating book_categories table if not exists")
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS book_categories (
                book_id INTEGER,
                category_id INTEGER,
                PRIMARY KEY (book_id, category_id),
                FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            )
            ''')
            
            # Create book_contents table for storing extracted text
            logger.trace("Creating book_contents table if not exists")
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS book_contents (
                book_id INTEGER PRIMARY KEY,
                content TEXT,
                FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
            )
            ''')
            
            conn.commit()
            logger.debug("Database tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
        finally:
            conn.close()
    
    def add_book(self, title, author, categories, file_path=None, content=None):
        """
        Add a new book to the database.
        
        Args:
            title: The book title
            author: The book author
            categories: List of categories the book belongs to
            file_path: Path to the PDF file
            content: Extracted text content from the book
            
        Returns:
            The ID of the newly added book
        """
        logger.info(f"Adding new book: '{title}' by '{author}'")
        start_time = time.time()
        
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Insert book with current timestamp for date_added
            logger.debug(f"Inserting book record: '{title}' by '{author}', file: {file_path}")
            cursor.execute(
                "INSERT INTO books (title, author, file_path, date_added) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (title, author, file_path)
            )
            book_id = cursor.lastrowid
            logger.debug(f"Book inserted with ID: {book_id}")
            
            # Add categories
            logger.debug(f"Adding {len(categories)} categories for book ID {book_id}")
            for category in categories:
                # Insert category if it doesn't exist
                cursor.execute(
                    "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                    (category,)
                )
                
                # Get category ID
                cursor.execute("SELECT id FROM categories WHERE name = ?", (category,))
                category_id = cursor.fetchone()[0]
                
                # Link book to category
                cursor.execute(
                    "INSERT INTO book_categories (book_id, category_id) VALUES (?, ?)",
                    (book_id, category_id)
                )
                logger.trace(f"Added category '{category}' (ID: {category_id}) to book ID {book_id}")
            
            # Add content if provided
            if content:
                content_length = len(content) if isinstance(content, str) else "binary data"
                logger.debug(f"Adding content for book ID {book_id} (length: {content_length})")
                cursor.execute(
                    "INSERT INTO book_contents (book_id, content) VALUES (?, ?)",
                    (book_id, content)
                )
            
            conn.commit()
            elapsed_time = time.time() - start_time
            logger.info(f"Book '{title}' (ID: {book_id}) added successfully in {elapsed_time:.2f}s")
            return book_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error adding book '{title}': {str(e)}")
            raise e
        finally:
            conn.close()
    
    def update_book(self, book_id, title=None, author=None, categories=None):
        """
        Update an existing book's metadata.
        
        Args:
            book_id: The ID of the book to update
            title: The new title (if None, will not update)
            author: The new author (if None, will not update)
            categories: The new list of categories (if None, will not update)
        """
        logger.info(f"Updating book ID {book_id}")
        start_time = time.time()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Get existing book data for logging
            cursor.execute("SELECT title, author FROM books WHERE id = ?", (book_id,))
            existing_book = cursor.fetchone()
            
            if not existing_book:
                logger.warning(f"Attempted to update nonexistent book ID {book_id}")
                return
                
            existing_title, existing_author = existing_book
            logger.debug(f"Updating book: '{existing_title}' by '{existing_author}' (ID: {book_id})")
            
            # Update title and/or author if provided
            if title or author:
                update_fields = []
                params = []
                
                if title:
                    update_fields.append("title = ?")
                    params.append(title)
                    logger.debug(f"Updating title from '{existing_title}' to '{title}'")
                
                if author:
                    update_fields.append("author = ?")
                    params.append(author)
                    logger.debug(f"Updating author from '{existing_author}' to '{author}'")
                
                params.append(book_id)
                
                cursor.execute(
                    f"UPDATE books SET {', '.join(update_fields)} WHERE id = ?",
                    tuple(params)
                )
            
            # Update categories if provided
            if categories:
                # Get existing categories for logging
                cursor.execute(
                    """
                    SELECT categories.name
                    FROM categories
                    JOIN book_categories ON categories.id = book_categories.category_id
                    WHERE book_categories.book_id = ?
                    """, 
                    (book_id,)
                )
                existing_categories = [row[0] for row in cursor.fetchall()]
                
                # Delete existing category links
                logger.debug(f"Removing existing categories for book ID {book_id}: {existing_categories}")
                cursor.execute(
                    "DELETE FROM book_categories WHERE book_id = ?",
                    (book_id,)
                )
                
                # Add new categories
                logger.debug(f"Adding new categories for book ID {book_id}: {categories}")
                for category in categories:
                    # Insert category if it doesn't exist
                    cursor.execute(
                        "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                        (category,)
                    )
                    
                    # Get category ID
                    cursor.execute("SELECT id FROM categories WHERE name = ?", (category,))
                    category_id = cursor.fetchone()[0]
                    
                    # Link book to category
                    cursor.execute(
                        "INSERT INTO book_categories (book_id, category_id) VALUES (?, ?)",
                        (book_id, category_id)
                    )
                    logger.trace(f"Added category '{category}' (ID: {category_id}) to book ID {book_id}")
            
            conn.commit()
            elapsed_time = time.time() - start_time
            logger.info(f"Book ID {book_id} updated successfully in {elapsed_time:.2f}s")
        
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating book ID {book_id}: {str(e)}")
            raise e
        finally:
            conn.close()
    
    def delete_book(self, book_id):
        """
        Delete a book from the database.
        
        Args:
            book_id: The ID of the book to delete
        """
        logger.info(f"Deleting book ID {book_id}")
        start_time = time.time()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Get book info before deletion (for potential file cleanup)
            cursor.execute("SELECT title, author, file_path FROM books WHERE id = ?", (book_id,))
            book = cursor.fetchone()
            
            if not book:
                logger.warning(f"Attempted to delete nonexistent book ID {book_id}")
                return
                
            title, author, file_path = book
            logger.debug(f"Deleting book: '{title}' by '{author}' (ID: {book_id})")
                
            # Delete the book (cascade will delete related records)
            cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
            logger.debug(f"Book record deleted from database (ID: {book_id})")
            
            # Delete the physical file if it exists and is a file
            if file_path and os.path.isfile(file_path):
                try:
                    logger.debug(f"Removing physical file: {file_path}")
                    os.remove(file_path)
                    logger.debug(f"Physical file removed: {file_path}")
                except Exception as file_error:
                    # Log the file deletion failure
                    logger.warning(f"Failed to delete physical file {file_path}: {str(file_error)}")
            
            conn.commit()
            elapsed_time = time.time() - start_time
            logger.info(f"Book '{title}' (ID: {book_id}) deleted successfully in {elapsed_time:.2f}s")
        
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting book ID {book_id}: {str(e)}")
            raise e
        finally:
            conn.close()
    
    def get_book(self, book_id):
        """
        Get a book by its ID.
        
        Args:
            book_id: The ID of the book to retrieve
            
        Returns:
            A dictionary with the book details or None if not found
        """
        logger.debug(f"Retrieving book with ID {book_id}")
        start_time = time.time()
        
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Get book
            cursor.execute(
                """
                SELECT books.id, books.title, books.author, books.file_path, books.date_added
                FROM books
                WHERE books.id = ?
                """,
                (book_id,)
            )
            book_row = cursor.fetchone()
            
            if not book_row:
                logger.debug(f"Book with ID {book_id} not found")
                return None
            
            # Convert row to dict
            book = dict(book_row)
            
            # Get categories
            cursor.execute(
                """
                SELECT categories.name
                FROM categories
                JOIN book_categories ON categories.id = book_categories.category_id
                WHERE book_categories.book_id = ?
                """,
                (book_id,)
            )
            
            book['categories'] = [row['name'] for row in cursor.fetchall()]
            
            elapsed_time = time.time() - start_time
            logger.trace(f"Retrieved book '{book['title']}' (ID: {book_id}) in {elapsed_time:.4f}s")
            return book
        
        except Exception as e:
            logger.error(f"Error retrieving book with ID {book_id}: {str(e)}")
            raise
        finally:
            conn.close()
    
    def get_book_content(self, book_id):
        """
        Get the text content of a book.
        
        Args:
            book_id: The ID of the book
            
        Returns:
            The text content of the book or None if not found
        """
        logger.debug(f"Retrieving content for book ID {book_id}")
        start_time = time.time()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT content FROM book_contents WHERE book_id = ?",
                (book_id,)
            )
            result = cursor.fetchone()
            
            if result:
                content = result[0]
                content_length = len(content) if isinstance(content, str) else "binary data"
                elapsed_time = time.time() - start_time
                logger.trace(f"Retrieved book content for ID {book_id} ({content_length} chars) in {elapsed_time:.4f}s")
                return content
                
            logger.debug(f"No content found for book ID {book_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving content for book ID {book_id}: {str(e)}")
            raise
        finally:
            conn.close()
    
    def get_all_books(self):
        """
        Get all books in the database.
        
        Returns:
            A list of dictionaries with book details
        """
        logger.debug("Retrieving all books")
        start_time = time.time()
        
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Get all books
            cursor.execute(
                """
                SELECT books.id, books.title, books.author, books.file_path, books.date_added
                FROM books
                ORDER BY books.title
                """
            )
            book_rows = cursor.fetchall()
            
            # Convert rows to dicts and add categories
            books = []
            for book_row in book_rows:
                book = dict(book_row)
                
                # Get categories for this book
                cursor.execute(
                    """
                    SELECT categories.name
                    FROM categories
                    JOIN book_categories ON categories.id = book_categories.category_id
                    WHERE book_categories.book_id = ?
                    """,
                    (book['id'],)
                )
                
                book['categories'] = [row['name'] for row in cursor.fetchall()]
                books.append(book)
            
            elapsed_time = time.time() - start_time
            logger.debug(f"Retrieved {len(books)} books in {elapsed_time:.4f}s")
            return books
            
        except Exception as e:
            logger.error(f"Error retrieving all books: {str(e)}")
            raise
        finally:
            conn.close()
    
    def search_books(self, query="", category=None):
        """
        Search books by title, author, or category.
        
        Args:
            query: Search string for title or author
            category: Filter by category name
            
        Returns:
            A list of dictionaries with book details
        """
        logger.debug(f"Searching books with query: '{query}', category: '{category}'")
        start_time = time.time()
        
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Base query
            base_query = """
            SELECT DISTINCT books.id, books.title, books.author, books.file_path, books.date_added
            FROM books
            """
            
            # Add category join if needed
            if category:
                base_query += """
                JOIN book_categories ON books.id = book_categories.book_id
                JOIN categories ON book_categories.category_id = categories.id
                """
            
            # Add WHERE clause
            where_clauses = []
            params = []
            
            if query:
                where_clauses.append("(books.title LIKE ? OR books.author LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])
            
            if category:
                where_clauses.append("categories.name = ?")
                params.append(category)
            
            if where_clauses:
                base_query += f" WHERE {' AND '.join(where_clauses)}"
            
            # Add order by
            base_query += " ORDER BY books.title"
            
            logger.trace(f"Search SQL: {base_query} with params {params}")
            
            # Execute query
            cursor.execute(base_query, params)
            book_rows = cursor.fetchall()
            
            # Convert rows to dicts and add categories
            books = []
            for book_row in book_rows:
                book = dict(book_row)
                
                # Get categories for this book
                cursor.execute(
                    """
                    SELECT categories.name
                    FROM categories
                    JOIN book_categories ON categories.id = book_categories.category_id
                    WHERE book_categories.book_id = ?
                    """,
                    (book['id'],)
                )
                
                book['categories'] = [row['name'] for row in cursor.fetchall()]
                books.append(book)
            
            elapsed_time = time.time() - start_time
            logger.debug(f"Search found {len(books)} books in {elapsed_time:.4f}s")
            return books
            
        except Exception as e:
            logger.error(f"Error searching books: {str(e)}")
            raise
        finally:
            conn.close()
    
    def get_all_categories(self):
        """
        Get all unique categories in the database.
        
        Returns:
            A list of category names
        """
        logger.debug("Retrieving all categories")
        start_time = time.time()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """
                SELECT name FROM categories
                ORDER BY name
                """
            )
            
            categories = [row[0] for row in cursor.fetchall()]
            elapsed_time = time.time() - start_time
            logger.debug(f"Retrieved {len(categories)} categories in {elapsed_time:.4f}s")
            return categories
            
        except Exception as e:
            logger.error(f"Error retrieving categories: {str(e)}")
            raise
        finally:
            conn.close()