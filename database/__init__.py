"""
Database package for Book Knowledge AI application.
Provides functionality for database operations, schema management, and data access.
"""

from database.connection import get_connection
from database.utils import execute_query, execute_insert, table_exists
from database.initialize import initialize_database
from database.schema import init_database, apply_migrations, get_database_info
from database.models import Book, BookContent, Category, KnowledgeBaseEntry
from database.repository import BookRepository, KnowledgeBaseRepository

__all__ = [
    # Connection and utilities
    'get_connection',
    'execute_query',
    'execute_insert',
    'table_exists',
    
    # Initialization and schema management
    'initialize_database',
    'init_database',
    'apply_migrations',
    'get_database_info',
    
    # Data models
    'Book',
    'BookContent',
    'Category',
    'KnowledgeBaseEntry',
    
    # Repositories
    'BookRepository',
    'KnowledgeBaseRepository',
]