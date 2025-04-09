"""
Vector store implementation for knowledge base.
This module is maintained for backward compatibility.
New code should use the vector_stores module.
"""

import os
from typing import List, Dict, Any, Optional, Callable, Type, Union, Tuple

from utils.logger import get_logger
from knowledge_base.embedding import get_embedding_function
from knowledge_base.chunking import chunk_document
from knowledge_base.vector_stores import get_vector_store, get_available_vector_stores
from knowledge_base.config import (
    DEFAULT_COLLECTION_NAME,
    DEFAULT_VECTOR_DIR,
    DEFAULT_DATA_DIR,
    DEFAULT_DISTANCE_FUNC,
    DEFAULT_VECTOR_STORE
)

logger = get_logger(__name__)

class VectorStore:
    """
    Vector store for the knowledge base.
    This class provides backward compatibility with the old vector store API.
    It delegates to the new vector store implementations.
    """
    
    def __init__(
        self,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        base_path: str = DEFAULT_VECTOR_DIR,
        data_path: str = DEFAULT_DATA_DIR,
        embedding_function: Optional[Callable] = None,
        distance_func: str = DEFAULT_DISTANCE_FUNC,
        vector_store_type: str = DEFAULT_VECTOR_STORE
    ):
        """
        Initialize the vector store.
        
        Args:
            collection_name: Name of the collection
            base_path: Path to store vector database files
            data_path: Path to store document data
            embedding_function: Optional function to use for embeddings
            distance_func: Distance function to use ('cosine', 'l2', 'ip')
            vector_store_type: Type of vector store to use
        """
        self.collection_name = collection_name
        self.base_path = base_path
        self.data_path = data_path
        self.distance_func = distance_func
        self.vector_store_type = vector_store_type
        
        # Set embedding function
        if embedding_function is None:
            self.embedding_function = get_embedding_function()
        else:
            self.embedding_function = embedding_function
            
        # Create the underlying vector store
        self.vector_store = get_vector_store(
            store_type=vector_store_type,
            collection_name=collection_name,
            base_path=base_path,
            data_path=data_path,
            embedding_function=self.embedding_function,
            distance_func=distance_func
        )
        
        logger.info(f"Vector store initialized with type '{vector_store_type}' and collection '{collection_name}'")
    
    def add_document(
        self,
        document_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> str:
        """
        Add a document to the vector store.
        
        Args:
            document_id: Document ID
            text: Document text content
            metadata: Optional document metadata
            chunk_size: Optional custom chunk size
            chunk_overlap: Optional custom chunk overlap
            
        Returns:
            Document ID
        """
        return self.vector_store.add_document(
            document_id=document_id,
            text=text,
            metadata=metadata,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    def search(
        self,
        query: str,
        limit: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search the vector store.
        
        Args:
            query: Search query
            limit: Maximum number of results
            where: Filter condition
            
        Returns:
            List of search results
        """
        return self.vector_store.search(
            query=query,
            limit=limit,
            where=where
        )
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document from the vector store.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document or None if not found
        """
        return self.vector_store.get_document(document_id)
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the vector store.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deleted, False otherwise
        """
        return self.vector_store.delete_document(document_id)
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents in the vector store.
        
        Returns:
            List of documents
        """
        return self.vector_store.list_documents()
    
    def get(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get entries from the vector store.
        
        Args:
            ids: List of IDs to get
            where: Filter condition
            
        Returns:
            Dictionary with documents, metadatas, and ids
        """
        return self.vector_store.get(ids=ids, where=where)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get vector store statistics.
        
        Returns:
            Dictionary of statistics
        """
        return self.vector_store.get_stats()
    
    def count(self) -> int:
        """
        Get the number of entries in the vector store.
        
        Returns:
            Number of entries
        """
        return self.vector_store.count()
    
    def reset(self) -> bool:
        """
        Reset the vector store.
        
        Returns:
            True if successful
        """
        return self.vector_store.reset()