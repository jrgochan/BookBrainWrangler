"""
Database utility functions for Book Knowledge AI application.
"""

import sqlite3
from typing import List, Dict, Any, Optional, Union, Tuple

from utils.logger import get_logger
from database.connection import get_connection

# Get a logger for this module
logger = get_logger(__name__)

def table_exists(table_name: str) -> bool:
    """
    Check if a table exists in the database.
    
    Args:
        table_name: Name of the table to check
        
    Returns:
        True if the table exists, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        
        exists = cursor.fetchone() is not None
        
        conn.close()
        
        return exists
        
    except sqlite3.Error as e:
        logger.error(f"Error checking if table exists: {str(e)}")
        return False

def execute_query(query: str, params: Optional[Union[List, Tuple]] = None) -> List[Dict[str, Any]]:
    """
    Execute a database query and return results as a list of dictionaries.
    
    Args:
        query: SQL query string
        params: Query parameters
        
    Returns:
        List of dictionaries with query results
    """
    try:
        conn = get_connection()
        
        # Set row_factory to return dictionaries
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Convert results to list of dictionaries
        results = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return results
        
    except sqlite3.Error as e:
        logger.error(f"Error executing query: {str(e)}")
        logger.debug(f"Query: {query}")
        if params:
            logger.debug(f"Params: {params}")
        return []

def execute_insert(query: str, params: Optional[Union[List, Tuple]] = None) -> Optional[int]:
    """
    Execute an INSERT query and return the ID of the inserted row.
    
    Args:
        query: SQL query string
        params: Query parameters
        
    Returns:
        ID of the inserted row or None if failed
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Get the ID of the inserted row
        last_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return last_id
        
    except sqlite3.Error as e:
        logger.error(f"Error executing insert: {str(e)}")
        logger.debug(f"Query: {query}")
        if params:
            logger.debug(f"Params: {params}")
        return None

def execute_update(query: str, params: Optional[Union[List, Tuple]] = None) -> int:
    """
    Execute an UPDATE query and return the number of affected rows.
    
    Args:
        query: SQL query string
        params: Query parameters
        
    Returns:
        Number of affected rows
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Get the number of affected rows
        row_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return row_count
        
    except sqlite3.Error as e:
        logger.error(f"Error executing update: {str(e)}")
        logger.debug(f"Query: {query}")
        if params:
            logger.debug(f"Params: {params}")
        return 0

def get_column_names(table_name: str) -> List[str]:
    """
    Get the names of columns in a table.
    
    Args:
        table_name: Name of the table
        
    Returns:
        List of column names
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get column info from table
        cursor.execute(f"PRAGMA table_info({table_name})")
        
        # Extract column names
        column_names = [row[1] for row in cursor.fetchall()]
        
        conn.close()
        
        return column_names
        
    except sqlite3.Error as e:
        logger.error(f"Error getting column names: {str(e)}")
        return []

def get_database_size() -> int:
    """
    Get the size of the database in bytes.
    
    Returns:
        Size in bytes
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get database page count and size
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        
        conn.close()
        
        # Calculate size
        size_bytes = page_count * page_size
        
        return size_bytes
        
    except sqlite3.Error as e:
        logger.error(f"Error getting database size: {str(e)}")
        return 0

def backup_database(backup_path: str) -> bool:
    """
    Backup the database to a file.
    
    Args:
        backup_path: Path to save the backup
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get source connection
        source_conn = get_connection()
        
        # Create destination connection
        dest_conn = sqlite3.connect(backup_path)
        
        # Backup database
        source_conn.backup(dest_conn)
        
        # Close connections
        source_conn.close()
        dest_conn.close()
        
        logger.info(f"Database backed up to {backup_path}")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Error backing up database: {str(e)}")
        return False