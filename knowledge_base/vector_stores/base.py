"""
Base vector store class for Book Knowledge AI.
"""

import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable, Tuple
import uuid
import json
import shutil

from utils.logger import get_logger
from knowledge_base.chunking import chunk_document
from knowledge_base.embedding import get_embedding_function

logger = get_logger(__name__)

class BaseVectorStore(ABC):
    """
    Abstract base class for vector stores.
    Provides a common interface for different vector store implementations.
    """
    
    def __init__(
        self,
        collection_name: str,
        base_path: str,
        data_path: str,
        embedding_function: Optional[Callable] = None,
        distance_func: str = "cosine"
    ):
        """
        Initialize the vector store.
        
        Args:
            collection_name: Name of the collection
            base_path: Path to store vector database
            data_path: Path to store document data
            embedding_function: Function to create embeddings
            distance_func: Distance function ('cosine', 'l2', 'ip')
        """
        self.collection_name = collection_name
        self.base_path = base_path
        self.data_path = data_path
        self.distance_func = distance_func
        
        # Create directories if they don't exist
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(self.data_path, exist_ok=True)
        
        # Set embedding function
        if embedding_function is None:
            self.embedding_function = get_embedding_function()
        else:
            self.embedding_function = embedding_function
            
        # Initialize the vector store
        self._init_store()
        
        logger.info(f"Vector store initialized with collection '{collection_name}'")
    
    @abstractmethod
    def _init_store(self):
        """Initialize the vector store."""
        pass
        
    @abstractmethod
    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add texts to the vector store.
        
        Args:
            texts: List of texts to add
            metadatas: Optional list of metadata dictionaries
            ids: Optional list of IDs
            
        Returns:
            List of IDs of added texts
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
            Dictionary with documents, embeddings, metadatas, and ids
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """
        Get the number of entries in the vector store.
        
        Returns:
            Number of entries
        """
        pass
        
    @abstractmethod
    def delete(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Delete entries from the vector store.
        
        Args:
            ids: List of IDs to delete
            where: Filter condition
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def reset(self) -> bool:
        """
        Reset the vector store.
        
        Returns:
            True if successful
        """
        pass
    
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
        # Initialize metadata if None
        if metadata is None:
            metadata = {}
            
        # Create document metadata
        document_metadata = {
            "document_id": document_id,
            "is_document": True
        }
        document_metadata.update(metadata)
        
        # Save document metadata to disk
        self._save_document_to_disk(document_id, text, document_metadata)
        
        # Chunk the document
        chunks = chunk_document(
            text,
            document_id,
            metadata,
            chunk_size=chunk_size or 500,
            chunk_overlap=chunk_overlap or 50
        )
        
        # Add chunks to vector store
        chunk_texts = [chunk["text"] for chunk in chunks]
        chunk_metadatas = [chunk["metadata"] for chunk in chunks]
        
        # Generate IDs for chunks
        chunk_ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        
        # Add chunks to vector store
        self.add_texts(chunk_texts, chunk_metadatas, chunk_ids)
        
        logger.info(f"Added document '{document_id}' with {len(chunks)} chunks")
        
        return document_id
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document from the vector store.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document or None if not found
        """
        try:
            # Get document from disk
            document = self._get_document_from_disk(document_id)
            
            if not document:
                return None
            
            # Get chunks for this document
            chunks = self.get(where={"document_id": document_id})
            
            if chunks and "documents" in chunks and chunks["documents"]:
                document["chunks"] = chunks["documents"]
            else:
                document["chunks"] = []
            
            return document
            
        except Exception as e:
            logger.error(f"Error getting document '{document_id}': {str(e)}")
            return None
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the vector store.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            # Delete chunks from vector store
            self.delete(where={"document_id": document_id})
            
            # Delete from disk
            self._delete_document_from_disk(document_id)
            
            logger.info(f"Deleted document '{document_id}' from vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document '{document_id}': {str(e)}")
            return False
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents in the vector store.
        
        Returns:
            List of documents
        """
        try:
            return self._list_documents_on_disk()
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get vector store statistics.
        
        Returns:
            Dictionary of statistics
        """
        try:
            stats = {}
            
            # Count documents
            documents = self.list_documents()
            stats["document_count"] = len(documents)
            
            # Count chunks
            stats["chunk_count"] = self.count()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting vector store stats: {str(e)}")
            return {
                "document_count": 0,
                "chunk_count": 0
            }
    
    def _save_document_to_disk(self, document_id: str, text: str, metadata: Dict[str, Any]) -> bool:
        """Save document to disk."""
        try:
            # Create document data
            document_data = {
                "id": document_id,
                "text": text,
                "metadata": metadata
            }
            
            # Save to disk
            file_path = os.path.join(self.data_path, f"{document_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(document_data, f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Error saving document to disk: {str(e)}")
            return False
    
    def _get_document_from_disk(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document from disk."""
        try:
            file_path = os.path.join(self.data_path, f"{document_id}.json")
            
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                document_data = json.load(f)
                
            return document_data
            
        except Exception as e:
            logger.error(f"Error getting document from disk: {str(e)}")
            return None
    
    def _delete_document_from_disk(self, document_id: str) -> bool:
        """Delete document from disk."""
        try:
            file_path = os.path.join(self.data_path, f"{document_id}.json")
            
            if os.path.exists(file_path):
                os.remove(file_path)
                
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document from disk: {str(e)}")
            return False
    
    def _list_documents_on_disk(self) -> List[Dict[str, Any]]:
        """List documents on disk."""
        try:
            documents = []
            
            for filename in os.listdir(self.data_path):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.data_path, filename)
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        document_data = json.load(f)
                        documents.append(document_data)
                        
            return documents
            
        except Exception as e:
            logger.error(f"Error listing documents on disk: {str(e)}")
            return []
        
    @staticmethod
    def generate_id() -> str:
        """Generate a unique ID."""
        return str(uuid.uuid4())
        
    @property
    def use_gpu(self) -> bool:
        """
        Get the use_gpu setting.
        This property is implementation-specific - default is False.
        
        Returns:
            True if GPU use is enabled, False otherwise
        """
        return False
        
    @property
    def using_gpu(self) -> bool:
        """
        Check if the vector store is actually using GPU acceleration.
        This property is implementation-specific - default is False.
        
        Returns:
            True if GPU is being used, False otherwise
        """
        return False