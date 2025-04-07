import sqlite3
import os

# Database file path
DB_FILE = "book_manager.db"

def get_connection():
    """
    Get a connection to the SQLite database.
    Creates the database file if it doesn't exist.
    
    Returns:
        A SQLite connection object
    """
    conn = sqlite3.connect(DB_FILE)
    
    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")
    
    return conn
