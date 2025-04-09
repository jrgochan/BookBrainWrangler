"""
Configuration settings for the Knowledge Base.
"""

# Vector store settings
DEFAULT_VECTOR_STORE_SETTINGS = {
    "persist_directory": "knowledge_base_data/faiss_db",
    "collection_name": "book_knowledge_base",
    "embedding_space": "cosine",  # Distance metric for vector similarity
}

# Embedding model settings
DEFAULT_EMBEDDING_SETTINGS = {
    "model_name": "all-MiniLM-L6-v2",
    "use_fallback": True,
}

# Text chunking settings
DEFAULT_CHUNKING_SETTINGS = {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "is_separator_regex": False,
    "separator": None,
}

# Database settings
DEFAULT_DB_SETTINGS = {
    "db_path": "book_manager.db",
    "table_name": "indexed_books",
}
