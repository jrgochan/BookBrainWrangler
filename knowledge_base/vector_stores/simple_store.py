"""
Simple in-memory vector store implementation for Book Knowledge AI.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Callable, Tuple

from utils.logger import get_logger
from knowledge_base.vector_stores.base import BaseVectorStore
from knowledge_base.vector_stores import register_vector_store

logger = get_logger(__name__)

class SimpleVectorStore(BaseVectorStore):
    """Simple in-memory vector store."""
    
    def __init__(
        self,
        collection_name: str = "book_knowledge",
        base_path: str = "./knowledge_base_data/vectors",
        data_path: str = "./knowledge_base_data/knowledge_base_data",
        embedding_function: Optional[Callable] = None,
        distance_func: str = "cosine"
    ):
        """
        Initialize the simple vector store.
        
        Args:
            collection_name: Name of the collection
            base_path: Path to store vector database
            data_path: Path to store document data
            embedding_function: Function to create embeddings
            distance_func: Distance function ('cosine', 'l2', 'ip')
        """
        super().__init__(
            collection_name=collection_name,
            base_path=base_path,
            data_path=data_path,
            embedding_function=embedding_function,
            distance_func=distance_func
        )
    
    def _init_store(self):
        """Initialize the simple vector store."""
        # Simple in-memory collection
        self.collection = {
            "documents": [],
            "embeddings": [],
            "metadatas": [],
            "ids": []
        }
        
        logger.info("Simple vector store initialized")
    
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
        if not texts:
            return []
        
        # Generate embeddings
        embeddings = [self.embedding_function(text) for text in texts]
        
        # Generate IDs if not provided
        if ids is None:
            ids = [self.generate_id() for _ in range(len(texts))]
        
        # Create metadata if not provided
        if metadatas is None:
            metadatas = [{} for _ in range(len(texts))]
        
        # Add to collection
        self.collection["documents"].extend(texts)
        self.collection["embeddings"].extend(embeddings)
        self.collection["metadatas"].extend(metadatas)
        self.collection["ids"].extend(ids)
        
        return ids
    
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
        if not self.collection["embeddings"]:
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_function(query)
        
        # Calculate similarities
        scores = []
        for embedding in self.collection["embeddings"]:
            # Calculate similarity based on distance function
            if self.distance_func == "cosine":
                score = self._cosine_similarity(query_embedding, embedding)
            elif self.distance_func == "ip":  # Inner product
                score = np.dot(query_embedding, embedding)
            else:  # L2 distance
                score = 1.0 / (1.0 + np.linalg.norm(np.array(query_embedding) - np.array(embedding)))
            
            scores.append(score)
        
        # Create results with indices
        indexed_scores = [(i, score) for i, score in enumerate(scores)]
        
        # Filter by metadata if provided
        if where:
            indexed_scores = [
                (i, score) for i, score in indexed_scores
                if self._matches_filter(self.collection["metadatas"][i], where)
            ]
        
        # Sort by score in descending order
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Limit results
        indexed_scores = indexed_scores[:limit]
        
        # Format results
        results = []
        for i, score in indexed_scores:
            result = {
                "id": self.collection["ids"][i],
                "text": self.collection["documents"][i],
                "metadata": self.collection["metadatas"][i],
                "score": float(score)
            }
            results.append(result)
        
        return results
    
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
        # Initialize result lists
        result_documents = []
        result_metadatas = []
        result_ids = []
        
        # Filter by IDs and/or metadata
        for i, doc_id in enumerate(self.collection["ids"]):
            # Filter by ID if provided
            if ids and doc_id not in ids:
                continue
                
            # Filter by metadata if provided
            if where and not self._matches_filter(self.collection["metadatas"][i], where):
                continue
                
            # Add to results
            result_documents.append(self.collection["documents"][i])
            result_metadatas.append(self.collection["metadatas"][i])
            result_ids.append(doc_id)
        
        return {
            "documents": result_documents,
            "metadatas": result_metadatas,
            "ids": result_ids
        }
    
    def count(self) -> int:
        """
        Get the number of entries in the vector store.
        
        Returns:
            Number of entries
        """
        return len(self.collection["documents"])
    
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
        # Find indices to delete
        indices_to_delete = []
        
        for i, doc_id in enumerate(self.collection["ids"]):
            should_delete = False
            
            # Check if ID matches
            if ids and doc_id in ids:
                should_delete = True
            
            # Check if metadata matches
            if where and self._matches_filter(self.collection["metadatas"][i], where):
                should_delete = True
            
            if should_delete:
                indices_to_delete.append(i)
        
        # Sort indices in reverse order to avoid index issues
        indices_to_delete.sort(reverse=True)
        
        # Delete entries
        for idx in indices_to_delete:
            self.collection["documents"].pop(idx)
            self.collection["embeddings"].pop(idx)
            self.collection["metadatas"].pop(idx)
            self.collection["ids"].pop(idx)
        
        return True
    
    def reset(self) -> bool:
        """
        Reset the vector store.
        
        Returns:
            True if successful
        """
        # Reset collection
        self.collection = {
            "documents": [],
            "embeddings": [],
            "metadatas": [],
            "ids": []
        }
        
        logger.info("Simple vector store reset")
        return True
    
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            v1: First vector
            v2: Second vector
            
        Returns:
            Cosine similarity (0-1)
        """
        v1_array = np.array(v1)
        v2_array = np.array(v2)
        
        # Check for zero vectors
        if np.all(v1_array == 0) or np.all(v2_array == 0):
            return 0.0
            
        dot_product = np.dot(v1_array, v2_array)
        norm_v1 = np.linalg.norm(v1_array)
        norm_v2 = np.linalg.norm(v2_array)
        
        return dot_product / (norm_v1 * norm_v2)
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """
        Check if metadata matches filter.
        
        Args:
            metadata: Metadata to check
            filter_dict: Filter dictionary
            
        Returns:
            True if metadata matches filter
        """
        for key, value in filter_dict.items():
            if key not in metadata or metadata[key] != value:
                return False
        
        return True

# Register the vector store
register_vector_store("simple", SimpleVectorStore)