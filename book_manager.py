import sqlite3
import datetime
from database import get_connection

class BookManager:
    def __init__(self):
        """Initialize the BookManager with a database connection."""
        # Make sure the database is initialized
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
                date_added TEXT NOT NULL
            )
        ''')
        
        # Create categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Create book_categories junction table for many-to-many relationship
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS book_categories (
                book_id INTEGER,
                category_id INTEGER,
                PRIMARY KEY (book_id, category_id),
                FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
            )
        ''')
        
        # Create book_content table to store the extracted text content
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS book_content (
                book_id INTEGER PRIMARY KEY,
                content TEXT,
                FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE
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
        cursor = conn.cursor()
        
        try:
            # Get current date in ISO format
            date_added = datetime.datetime.now().isoformat()
            
            # Insert the book
            cursor.execute(
                'INSERT INTO books (title, author, file_path, date_added) VALUES (?, ?, ?, ?)',
                (title, author, file_path, date_added)
            )
            
            # Get the book ID
            book_id = cursor.lastrowid
            
            # Add categories
            for category in categories:
                # Try to find the category ID
                cursor.execute('SELECT id FROM categories WHERE name = ?', (category,))
                result = cursor.fetchone()
                
                if result:
                    category_id = result[0]
                else:
                    # Create new category
                    cursor.execute('INSERT INTO categories (name) VALUES (?)', (category,))
                    category_id = cursor.lastrowid
                
                # Link the book to the category
                cursor.execute(
                    'INSERT INTO book_categories (book_id, category_id) VALUES (?, ?)',
                    (book_id, category_id)
                )
            
            # Store book content if provided
            if content:
                cursor.execute(
                    'INSERT INTO book_content (book_id, content) VALUES (?, ?)',
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
            # Update book information if provided
            if title is not None or author is not None:
                update_parts = []
                params = []
                
                if title is not None:
                    update_parts.append("title = ?")
                    params.append(title)
                
                if author is not None:
                    update_parts.append("author = ?")
                    params.append(author)
                
                params.append(book_id)
                cursor.execute(
                    f"UPDATE books SET {', '.join(update_parts)} WHERE id = ?",
                    params
                )
            
            # Update categories if provided
            if categories is not None:
                # First, remove all existing category links
                cursor.execute(
                    'DELETE FROM book_categories WHERE book_id = ?',
                    (book_id,)
                )
                
                # Then, add the new categories
                for category in categories:
                    # Try to find the category ID
                    cursor.execute('SELECT id FROM categories WHERE name = ?', (category,))
                    result = cursor.fetchone()
                    
                    if result:
                        category_id = result[0]
                    else:
                        # Create new category
                        cursor.execute('INSERT INTO categories (name) VALUES (?)', (category,))
                        category_id = cursor.lastrowid
                    
                    # Link the book to the category
                    cursor.execute(
                        'INSERT INTO book_categories (book_id, category_id) VALUES (?, ?)',
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
            # Delete the book (cascade will take care of related records)
            cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))
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
        cursor = conn.cursor()
        
        try:
            # Get the book
            cursor.execute('''
                SELECT b.id, b.title, b.author, b.file_path, b.date_added
                FROM books b
                WHERE b.id = ?
            ''', (book_id,))
            
            book_data = cursor.fetchone()
            if not book_data:
                return None
            
            # Get the book's categories
            cursor.execute('''
                SELECT c.name
                FROM categories c
                JOIN book_categories bc ON c.id = bc.category_id
                WHERE bc.book_id = ?
            ''', (book_id,))
            
            categories = [row[0] for row in cursor.fetchall()]
            
            book = {
                'id': book_data[0],
                'title': book_data[1],
                'author': book_data[2],
                'file_path': book_data[3],
                'date_added': book_data[4],
                'categories': categories
            }
            
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
            cursor.execute('SELECT content FROM book_content WHERE book_id = ?', (book_id,))
            result = cursor.fetchone()
            return result[0] if result else None
            
        finally:
            conn.close()
    
    def get_all_books(self):
        """
        Get all books in the database.
        
        Returns:
            A list of dictionaries with book details
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Get all books
            cursor.execute('''
                SELECT b.id, b.title, b.author, b.file_path, b.date_added
                FROM books b
                ORDER BY b.date_added DESC
            ''')
            
            books = []
            for book_data in cursor.fetchall():
                book_id = book_data[0]
                
                # Get the book's categories
                cursor.execute('''
                    SELECT c.name
                    FROM categories c
                    JOIN book_categories bc ON c.id = bc.category_id
                    WHERE bc.book_id = ?
                ''', (book_id,))
                
                categories = [row[0] for row in cursor.fetchall()]
                
                book = {
                    'id': book_id,
                    'title': book_data[1],
                    'author': book_data[2],
                    'file_path': book_data[3],
                    'date_added': book_data[4],
                    'categories': categories
                }
                
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
        cursor = conn.cursor()
        
        try:
            params = []
            sql = '''
                SELECT DISTINCT b.id, b.title, b.author, b.file_path, b.date_added
                FROM books b
            '''
            
            # If filtering by category, join with the category tables
            if category:
                sql += '''
                    JOIN book_categories bc ON b.id = bc.book_id
                    JOIN categories c ON bc.category_id = c.id
                    WHERE c.name = ?
                '''
                params.append(category)
                
                # Add search query if provided
                if query:
                    sql += '''
                        AND (b.title LIKE ? OR b.author LIKE ?)
                    '''
                    params.extend([f'%{query}%', f'%{query}%'])
            
            # If only search query provided
            elif query:
                sql += '''
                    WHERE b.title LIKE ? OR b.author LIKE ?
                '''
                params.extend([f'%{query}%', f'%{query}%'])
            
            sql += ' ORDER BY b.date_added DESC'
            
            cursor.execute(sql, params)
            
            books = []
            for book_data in cursor.fetchall():
                book_id = book_data[0]
                
                # Get the book's categories
                cursor.execute('''
                    SELECT c.name
                    FROM categories c
                    JOIN book_categories bc ON c.id = bc.category_id
                    WHERE bc.book_id = ?
                ''', (book_id,))
                
                categories = [row[0] for row in cursor.fetchall()]
                
                book = {
                    'id': book_id,
                    'title': book_data[1],
                    'author': book_data[2],
                    'file_path': book_data[3],
                    'date_added': book_data[4],
                    'categories': categories
                }
                
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
            cursor.execute('SELECT name FROM categories ORDER BY name')
            return [row[0] for row in cursor.fetchall()]
            
        finally:
            conn.close()
