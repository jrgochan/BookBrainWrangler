"""
Vector store implementations for the knowledge base.
This module provides various vector store implementations for the knowledge base.
"""

from typing import Dict, Type, List, Optional
from .base import BaseVectorStore

# Dictionary of available vector stores - will be populated by imports
VECTOR_STORES: Dict[str, Type[BaseVectorStore]] = {}

# Default vector store type
DEFAULT_VECTOR_STORE = "faiss"

def register_vector_store(name: str, vector_store_class: Type[BaseVectorStore]):
    """Register a vector store implementation."""
    VECTOR_STORES[name] = vector_store_class

def get_available_vector_stores() -> List[str]:
    """Get a list of available vector store types."""
    return list(VECTOR_STORES.keys())

def get_vector_store(store_type: str = DEFAULT_VECTOR_STORE, **kwargs) -> BaseVectorStore:
    """
    Create a vector store of the specified type.
    
    Args:
        store_type: Type of vector store to create (defaults to faiss)
        **kwargs: Additional arguments to pass to the vector store constructor
        
    Returns:
        Vector store instance
    """
    if not VECTOR_STORES:
        # Import implementations to register them
        from .faiss_store import FAISSVectorStore
        from .simple_store import SimpleVectorStore
        
        # Try to import optional implementations
        try:
            from .chromadb_store import ChromaDBVectorStore
        except ImportError:
            pass
            
        try:
            from .annoy_store import AnnoyVectorStore
        except ImportError:
            pass
    
    if store_type not in VECTOR_STORES:
        raise ValueError(f"Unsupported vector store type: {store_type}. Available types: {', '.join(VECTOR_STORES.keys())}")
    
    return VECTOR_STORES[store_type](**kwargs)