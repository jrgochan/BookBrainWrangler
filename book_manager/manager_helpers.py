"""
Helper functions for BookManager.
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from database import get_connection
from utils.logger import get_logger

logger = get_logger(__name__)

def count_books() -> int:
    """
    Count the total number of books in the database.
    
    Returns:
        int: Total number of books
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM books")
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        logger.error(f"Error counting books: {str(e)}")
        return 0
        
def count_categories() -> int:
    """
    Count the number of unique categories across all books.
    
    Returns:
        int: Number of unique categories
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if the category column exists
        cursor.execute("PRAGMA table_info(books)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'category' in columns:
            cursor.execute("SELECT COUNT(DISTINCT category) FROM books WHERE category IS NOT NULL AND category != ''")
            count = cursor.fetchone()[0]
            return count
        else:
            logger.warning("Category column not found in books table")
            return 0
    except Exception as e:
        logger.error(f"Error counting categories: {str(e)}")
        return 0
        
def get_recent_books(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get the most recently added books.
    
    Args:
        limit: Maximum number of books to return
        
    Returns:
        List of book dictionaries
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if the created_at column exists
        cursor.execute("PRAGMA table_info(books)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Determine which columns to select and how to order
        if 'created_at' in columns:
            cursor.execute("""
                SELECT id, title, author, created_at 
                FROM books 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            books = []
            for row in cursor.fetchall():
                books.append({
                    "id": row[0],
                    "title": row[1],
                    "author": row[2],
                    "created_at": row[3]
                })
        else:
            # Fallback to just ordering by ID if created_at doesn't exist
            cursor.execute("""
                SELECT id, title, author
                FROM books 
                ORDER BY id DESC 
                LIMIT ?
            """, (limit,))
            
            books = []
            for row in cursor.fetchall():
                books.append({
                    "id": row[0],
                    "title": row[1],
                    "author": row[2],
                    "created_at": datetime.now().strftime("%Y-%m-%d") # Default date
                })
            
            logger.warning("created_at column not found in books table, using ID for ordering")
            
        return books
    except Exception as e:
        logger.error(f"Error getting recent books: {str(e)}")
        return []