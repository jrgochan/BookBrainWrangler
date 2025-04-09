"""
Database utility functions.
"""

import sqlite3
from typing import List, Dict, Any, Optional, Tuple

from utils.logger import get_logger
from database.connection import get_connection

# Get a logger for this module
logger = get_logger(__name__)

def execute_query(query: str, params: Tuple = (), fetch_all: bool = True) -> List[Tuple]:
    """
    Execute a SQL query and return the results.
    
    Args:
        query: SQL query string
        params: Parameters for the query
        fetch_all: Whether to fetch all results or just one
        
    Returns:
        List of tuple results or None if fetch_all is False and no results
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(query, params)
        
        if fetch_all:
            results = cursor.fetchall()
        else:
            results = cursor.fetchone()
            
        conn.commit()
        conn.close()
        
        return results
    except Exception as e:
        logger.error(f"Database error executing query: {str(e)}")
        logger.debug(f"Query: {query}")
        logger.debug(f"Params: {params}")
        raise

def execute_insert(query: str, params: Tuple = ()) -> int:
    """
    Execute an INSERT query and return the last row id.
    
    Args:
        query: SQL query string
        params: Parameters for the query
        
    Returns:
        Last row id
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(query, params)
        
        # Get the last rowid (sqlite_last_insert_rowid returns 0 if no insert)
        if cursor.lastrowid is None:
            cursor.execute("SELECT last_insert_rowid()")
            row_id = cursor.fetchone()[0]
        else:
            row_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return row_id
    except Exception as e:
        logger.error(f"Database error executing insert: {str(e)}")
        logger.debug(f"Query: {query}")
        logger.debug(f"Params: {params}")
        raise

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
        
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
    except Exception as e:
        logger.error(f"Database error checking if table exists: {str(e)}")
        return False