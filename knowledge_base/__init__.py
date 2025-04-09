"""
Knowledge base module for Book Knowledge AI application.
"""

from knowledge_base.vector_store import KnowledgeBase
from knowledge_base.chunking import chunk_text, chunk_document
from knowledge_base.embedding import get_embedding_function, get_embeddings