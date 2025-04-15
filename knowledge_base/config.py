"""
Configuration for the knowledge base.
"""

import os

# Default vector store settings
DEFAULT_COLLECTION_NAME = "book_knowledge"
DEFAULT_VECTOR_DIR = "./knowledge_base_data/vectors"
DEFAULT_DATA_DIR = "./knowledge_base_data/knowledge_base_data"
DEFAULT_DISTANCE_FUNC = "cosine"
DEFAULT_VECTOR_STORE = "faiss"

# Vector store options
VECTOR_STORE_OPTIONS = ["faiss", "chromadb", "annoy", "simple"]

# Embedding settings
DEFAULT_EMBEDDING_DIMENSION = 384  # Default embedding dimension
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Default sentence-transformers model

# Chunking settings
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50

# Search settings
DEFAULT_SEARCH_LIMIT = 5
DEFAULT_SEARCH_THRESHOLD = 0.2

# Analytics settings
DEFAULT_KEYWORD_MIN_COUNT = 2
DEFAULT_KEYWORD_MAX_WORDS = 100
DEFAULT_STOPWORDS_LANGUAGE = "english"

# Splitting settings
DEFAULT_SPLIT_BY = "paragraph"

# Create directories if they don't exist
os.makedirs(DEFAULT_VECTOR_DIR, exist_ok=True)
os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)