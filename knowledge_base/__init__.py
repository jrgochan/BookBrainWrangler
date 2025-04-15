"""
Knowledge base module for Book Knowledge AI application.
"""

from knowledge_base.vector_store import VectorStore
from knowledge_base.chunking import chunk_document
from knowledge_base.embedding import get_embedding_function, get_embeddings
from knowledge_base.config import (
    DEFAULT_COLLECTION_NAME,
    DEFAULT_VECTOR_DIR,
    DEFAULT_DATA_DIR,
    DEFAULT_DISTANCE_FUNC,
    DEFAULT_VECTOR_STORE
)
from knowledge_base.vector_stores import get_available_vector_stores

# Alias for backward compatibility
KnowledgeBase = VectorStore