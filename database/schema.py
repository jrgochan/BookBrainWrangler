"""
Database schema for Book Knowledge AI application.
Handles database schema creation and migrations.
"""

import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime

from utils.logger import get_logger
from database.connection import get_connection
from database.utils import table_exists, execute_query

# Get a logger for this module
logger = get_logger(__name__)

# SQL statements for creating database tables
CREATE_BOOKS_TABLE = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    file_path TEXT,
    content_length INTEGER,
    date_added TEXT DEFAULT CURRENT_TIMESTAMP,
    last_modified TEXT DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT DEFAULT '{}'
)
"""

CREATE_BOOK_CATEGORIES_TABLE = """
CREATE TABLE IF NOT EXISTS book_categories (
    id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL,
    category_name TEXT NOT NULL,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    UNIQUE(book_id, category_name)
)
"""

CREATE_BOOK_CONTENTS_TABLE = """
CREATE TABLE IF NOT EXISTS book_contents (
    id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    format TEXT DEFAULT 'text',
    extracted_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
)
"""

CREATE_CATEGORIES_TABLE = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    parent_id INTEGER,
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL
)
"""

CREATE_KNOWLEDGE_BASE_TABLE = """
CREATE TABLE IF NOT EXISTS knowledge_base (
    id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL,
    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
    is_indexed INTEGER DEFAULT 0,
    last_indexed TEXT,
    chunk_count INTEGER DEFAULT 0,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    UNIQUE(book_id)
)
"""

CREATE_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY,
    key TEXT NOT NULL UNIQUE,
    value TEXT,
    value_type TEXT,
    description TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_METADATA_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS metadata_history (
    id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL,
    metadata TEXT NOT NULL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
)
"""

# Define database migrations
MIGRATIONS = [
    # Migration 1: Add metadata column to books table if it doesn't exist
    """
    ALTER TABLE books ADD COLUMN metadata TEXT DEFAULT '{}';
    """,
    # Migration 2: Add format column to book_contents table if it doesn't exist
    """
    ALTER TABLE book_contents ADD COLUMN format TEXT DEFAULT 'text';
    """,
    # Migration 3: Add chunk_count column to knowledge_base table if it doesn't exist
    """
    ALTER TABLE knowledge_base ADD COLUMN chunk_count INTEGER DEFAULT 0;
    """
]

def init_database(reset: bool = False) -> bool:
    """
    Initialize the database schema by creating necessary tables if they don't exist.
    
    Args:
        reset: If True, drop and recreate all tables (WARNING: data loss)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Track created tables for logging
        created_tables = []
        
        # If reset is True, drop existing tables
        if reset:
            logger.warning("Resetting database (all data will be lost)")
            
            # Drop tables in order (respect foreign key constraints)
            tables = [
                "metadata_history",
                "book_categories",
                "book_contents",
                "knowledge_base", 
                "books",
                "categories",
                "settings"
            ]
            
            for table in tables:
                if table_exists(table):
                    cursor.execute(f"DROP TABLE {table}")
                    logger.info(f"Dropped table: {table}")
        
        # Create tables if they don't exist
        if not table_exists("books"):
            cursor.execute(CREATE_BOOKS_TABLE)
            created_tables.append("books")
        
        if not table_exists("book_categories"):
            cursor.execute(CREATE_BOOK_CATEGORIES_TABLE)
            created_tables.append("book_categories")
        
        if not table_exists("book_contents"):
            cursor.execute(CREATE_BOOK_CONTENTS_TABLE)
            created_tables.append("book_contents")
        
        if not table_exists("categories"):
            cursor.execute(CREATE_CATEGORIES_TABLE)
            created_tables.append("categories")
        
        if not table_exists("knowledge_base"):
            cursor.execute(CREATE_KNOWLEDGE_BASE_TABLE)
            created_tables.append("knowledge_base")
        
        if not table_exists("settings"):
            cursor.execute(CREATE_SETTINGS_TABLE)
            created_tables.append("settings")
        
        if not table_exists("metadata_history"):
            cursor.execute(CREATE_METADATA_HISTORY_TABLE)
            created_tables.append("metadata_history")
        
        # Apply any pending migrations
        apply_migrations(conn)
        
        # Commit the changes
        conn.commit()
        conn.close()
        
        # Log created tables
        if created_tables:
            logger.info(f"Created database tables: {', '.join(created_tables)}")
        else:
            logger.debug("Database schema already exists, no tables created")
        
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

def apply_migrations(conn: sqlite3.Connection) -> None:
    """
    Apply any pending database migrations.
    
    Args:
        conn: SQLite database connection
    """
    cursor = conn.cursor()
    
    # Create migrations table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS migrations (
        id INTEGER PRIMARY KEY,
        migration_id INTEGER NOT NULL UNIQUE,
        applied_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Check which migrations have been applied
    cursor.execute("SELECT migration_id FROM migrations ORDER BY migration_id")
    applied_migrations = {row[0] for row in cursor.fetchall()}
    
    # Apply pending migrations
    for i, migration in enumerate(MIGRATIONS, start=1):
        if i not in applied_migrations:
            try:
                logger.info(f"Applying migration {i}")
                
                # Split migration into separate statements
                statements = migration.strip().split(';')
                
                # Execute each statement
                for statement in statements:
                    if statement.strip():
                        try:
                            cursor.execute(statement)
                        except sqlite3.OperationalError as e:
                            # Ignore "duplicate column" errors
                            if "duplicate column" not in str(e):
                                raise
                
                # Record that the migration was applied
                cursor.execute(
                    "INSERT INTO migrations (migration_id) VALUES (?)",
                    (i,)
                )
                
                logger.info(f"Migration {i} applied successfully")
                
            except sqlite3.Error as e:
                logger.error(f"Error applying migration {i}: {str(e)}")
                # Continue with next migration
                continue

def insert_default_settings() -> None:
    """
    Insert default settings into the settings table.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Default settings
        default_settings = [
            {
                "key": "embedding_model", 
                "value": "all-MiniLM-L6-v2", 
                "value_type": "string",
                "description": "Default embedding model for knowledge base"
            },
            {
                "key": "chunk_size", 
                "value": "512", 
                "value_type": "integer",
                "description": "Default chunk size for text splitting"
            },
            {
                "key": "chunk_overlap", 
                "value": "50", 
                "value_type": "integer",
                "description": "Default chunk overlap for text splitting"
            },
            {
                "key": "default_ai_provider", 
                "value": "ollama", 
                "value_type": "string",
                "description": "Default AI provider for chat"
            },
            {
                "key": "app_theme", 
                "value": "light", 
                "value_type": "string",
                "description": "Application theme (light/dark)"
            }
        ]
        
        # Insert or update default settings
        for setting in default_settings:
            # Check if setting exists
            cursor.execute(
                "SELECT id FROM settings WHERE key = ?",
                (setting["key"],)
            )
            
            if cursor.fetchone() is None:
                # Insert new setting
                cursor.execute(
                    """
                    INSERT INTO settings (key, value, value_type, description)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        setting["key"],
                        setting["value"],
                        setting["value_type"],
                        setting["description"]
                    )
                )
                logger.debug(f"Inserted default setting: {setting['key']}")
        
        # Commit changes
        conn.commit()
        conn.close()
        
    except sqlite3.Error as e:
        logger.error(f"Error inserting default settings: {str(e)}")

def get_database_info() -> Dict[str, Any]:
    """
    Get information about the database.
    
    Returns:
        Dictionary with database information
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get table counts
        tables = [
            "books", 
            "book_categories", 
            "book_contents", 
            "categories", 
            "knowledge_base", 
            "settings",
            "metadata_history"
        ]
        
        table_counts = {}
        for table in tables:
            if table_exists(table):
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_counts[table] = count
        
        # Get database file size
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        
        db_size = page_count * page_size
        
        # Get last modified timestamp
        cursor.execute("""
            SELECT MAX(last_modified) FROM books
        """)
        last_modified = cursor.fetchone()[0]
        
        # Check if any migrations are pending
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE name = 'migrations'")
        migrations_table_exists = cursor.fetchone()[0] > 0
        
        pending_migrations = 0
        if migrations_table_exists:
            cursor.execute("SELECT MAX(migration_id) FROM migrations")
            last_migration = cursor.fetchone()[0] or 0
            pending_migrations = max(0, len(MIGRATIONS) - last_migration)
        else:
            pending_migrations = len(MIGRATIONS)
        
        conn.close()
        
        return {
            "table_counts": table_counts,
            "size_bytes": db_size,
            "size_mb": round(db_size / (1024 * 1024), 2),
            "last_modified": last_modified,
            "pending_migrations": pending_migrations
        }
        
    except sqlite3.Error as e:
        logger.error(f"Error getting database info: {str(e)}")
        return {
            "error": str(e)
        }