"""
Database connection module for the application.
"""

import os
import sqlite3
import time
from utils.logger import get_logger

# Get a logger for this module
logger = get_logger(__name__)

def get_connection():
    """
    Get a connection to the SQLite database.
    Creates the database file if it doesn't exist.
    
    Returns:
        A SQLite connection object
    """
    start_time = time.time()
    logger.debug("Getting database connection")
    
    try:
        # Get the base directory (project root)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Database file path
        db_path = os.path.join(base_dir, "book_manager.db")
        logger.debug(f"Connecting to database at: {db_path}")
        
        # Track if this is a new database
        db_exists = os.path.exists(db_path)
        if not db_exists:
            logger.info(f"Creating new database file at: {db_path}")
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        
        # Enable foreign key support
        conn.execute("PRAGMA foreign_keys = ON")
        
        elapsed_time = time.time() - start_time
        logger.debug(f"Database connection established in {elapsed_time:.4f}s")
        return conn
        
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise