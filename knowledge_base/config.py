"""
Configuration module for Knowledge Base.
Contains default settings for knowledge base operations.
"""

import os
from typing import Dict, Any

# Directory paths
DEFAULT_KB_DIR = os.environ.get("KB_DIR", "knowledge_base_data")
DEFAULT_VECTOR_DIR = os.path.join(DEFAULT_KB_DIR, "vectors")
DEFAULT_DATA_DIR = os.path.join(DEFAULT_KB_DIR, "knowledge_base_data")

# Collection settings
DEFAULT_COLLECTION_NAME = "book_knowledge"
DEFAULT_DISTANCE_FUNC = "cosine"

# Embedding settings
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_EMBEDDING_DIMENSION = 384

# Chunking settings
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_SPLIT_BY = "paragraph"

# Search settings
DEFAULT_SEARCH_LIMIT = 5
DEFAULT_SEARCH_THRESHOLD = 0.6

# Analytics settings
DEFAULT_KEYWORD_MIN_COUNT = 2
DEFAULT_KEYWORD_MAX_WORDS = 3
DEFAULT_STOPWORDS_LANGUAGE = "english"

# Create required directories
os.makedirs(DEFAULT_KB_DIR, exist_ok=True)
os.makedirs(DEFAULT_VECTOR_DIR, exist_ok=True)
os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)

def get_default_config() -> Dict[str, Any]:
    """
    Get default knowledge base configuration.
    
    Returns:
        Dictionary with default configuration
    """
    return {
        "kb_dir": DEFAULT_KB_DIR,
        "vector_dir": DEFAULT_VECTOR_DIR,
        "data_dir": DEFAULT_DATA_DIR,
        "collection_name": DEFAULT_COLLECTION_NAME,
        "distance_func": DEFAULT_DISTANCE_FUNC,
        "embedding_model": DEFAULT_EMBEDDING_MODEL,
        "embedding_dimension": DEFAULT_EMBEDDING_DIMENSION,
        "chunk_size": DEFAULT_CHUNK_SIZE,
        "chunk_overlap": DEFAULT_CHUNK_OVERLAP,
        "split_by": DEFAULT_SPLIT_BY,
        "search_limit": DEFAULT_SEARCH_LIMIT,
        "search_threshold": DEFAULT_SEARCH_THRESHOLD,
        "keyword_min_count": DEFAULT_KEYWORD_MIN_COUNT,
        "keyword_max_words": DEFAULT_KEYWORD_MAX_WORDS,
        "stopwords_language": DEFAULT_STOPWORDS_LANGUAGE
    }