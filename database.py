"""
Database connection module for the application.
"""

import os
import sqlite3

def get_connection():
    """
    Get a connection to the SQLite database.
    Creates the database file if it doesn't exist.
    
    Returns:
        A SQLite connection object
    """
    # Get the directory where the database file should be stored
    db_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create the directory if it doesn't exist
    os.makedirs(db_dir, exist_ok=True)
    
    # Database file path
    db_path = os.path.join(db_dir, "book_manager.db")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    
    # Enable foreign key support
    conn.execute("PRAGMA foreign_keys = ON")
    
    return conn