"""
Book Manager module for handling book operations.
"""

import os
import sqlite3
import json
from typing import Dict, List, Any, Optional, Union
from database import get_connection

class BookManager:
    def __init__(self):
        """Initialize the BookManager with a database connection."""
        self._init_database()
    
    def _init_database(self):
        """Initialize the book database tables if they don't exist."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Create books table
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
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        ''')
        
        # Create book_categories junction table
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
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS book_contents (
            book_id INTEGER PRIMARY KEY,
            content TEXT,
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
        )
        ''')
        
        conn.commit()
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
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Insert book with current timestamp for date_added
            cursor.execute(
                "INSERT INTO books (title, author, file_path, date_added) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (title, author, file_path)
            )
            book_id = cursor.lastrowid
            
            # Add categories
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
            
            # Add content if provided
            if content:
                cursor.execute(
                    "INSERT INTO book_contents (book_id, content) VALUES (?, ?)",
                    (book_id, content)
                )
            
            conn.commit()
            return book_id
            
        except Exception as e:
            conn.rollback()
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
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Update title and/or author if provided
            if title or author:
                update_fields = []
                params = []
                
                if title:
                    update_fields.append("title = ?")
                    params.append(title)
                
                if author:
                    update_fields.append("author = ?")
                    params.append(author)
                
                params.append(book_id)
                
                cursor.execute(
                    f"UPDATE books SET {', '.join(update_fields)} WHERE id = ?",
                    tuple(params)
                )
            
            # Update categories if provided
            if categories:
                # Delete existing category links
                cursor.execute(
                    "DELETE FROM book_categories WHERE book_id = ?",
                    (book_id,)
                )
                
                # Add new categories
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
            
            conn.commit()
        
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def delete_book(self, book_id):
        """
        Delete a book from the database.
        
        Args:
            book_id: The ID of the book to delete
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Get book info before deletion (for potential file cleanup)
            cursor.execute("SELECT file_path FROM books WHERE id = ?", (book_id,))
            book = cursor.fetchone()
            
            if book:
                file_path = book[0]
                
                # Delete the book (cascade will delete related records)
                cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
                
                # Delete the physical file if it exists and is a file
                if file_path and os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        # Just log or ignore if file deletion fails
                        pass
            
            conn.commit()
        
        except Exception as e:
            conn.rollback()
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
            
            return book
        
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
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT content FROM book_contents WHERE book_id = ?",
                (book_id,)
            )
            result = cursor.fetchone()
            
            if result:
                return result[0]
            return None
        
        finally:
            conn.close()
    
    def get_all_books(self):
        """
        Get all books in the database.
        
        Returns:
            A list of dictionaries with book details
        """
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
            
            return books
        
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
            
            return books
        
        finally:
            conn.close()
    
    def get_all_categories(self):
        """
        Get all unique categories in the database.
        
        Returns:
            A list of category names
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """
                SELECT name FROM categories
                ORDER BY name
                """
            )
            
            return [row[0] for row in cursor.fetchall()]
        
        finally:
            conn.close()