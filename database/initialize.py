"""
Database initialization for Book Knowledge AI application.
"""

from utils.logger import get_logger
from database.schema import init_database, insert_default_settings

# Get a logger for this module
logger = get_logger(__name__)

def initialize_database(reset: bool = False) -> bool:
    """
    Initialize the database schema and default settings.
    
    Args:
        reset: If True, drop and recreate all tables (WARNING: data loss)
        
    Returns:
        True if successful, False otherwise
    """
    # Initialize schema
    schema_initialized = init_database(reset)
    
    if not schema_initialized:
        logger.error("Failed to initialize database schema")
        return False
    
    # Insert default settings
    insert_default_settings()
    
    logger.info("Database initialization complete")
    return True