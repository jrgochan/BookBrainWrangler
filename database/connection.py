"""
Database connection for Book Knowledge AI application.
"""

import os
import sqlite3
from typing import Optional

from utils.logger import get_logger

# Get a logger for this module
logger = get_logger(__name__)

# Database configuration
DB_FILE = "book_manager.db"
DB_PATH = os.path.join(os.getcwd(), DB_FILE)

def get_connection() -> sqlite3.Connection:
    """
    Get a connection to the SQLite database.
    
    Returns:
        SQLite database connection
    """
    try:
        # Create database directory if it doesn't exist
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
        return conn
        
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise