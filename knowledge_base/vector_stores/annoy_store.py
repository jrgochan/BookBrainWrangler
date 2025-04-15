"""
Annoy vector store implementation for Book Knowledge AI.
"""

import os
import importlib.util
import numpy as np
from typing import List, Dict, Any, Optional, Callable
import pickle

from utils.logger import get_logger
from knowledge_base.vector_stores.base import BaseVectorStore
from knowledge_base.vector_stores import register_vector_store

logger = get_logger(__name__)

# Check if Annoy is available
ANNOY_AVAILABLE = importlib.util.find_spec("annoy") is not None

if ANNOY_AVAILABLE:
    from annoy import AnnoyIndex

class AnnoyVectorStore(BaseVectorStore):
    """Vector store with Annoy."""
    
    def __init__(
        self,
        collection_name: str = "book_knowledge",
        base_path: str = "./knowledge_base_data/vectors",
        data_path: str = "./knowledge_base_data/knowledge_base_data",
        embedding_function: Optional[Callable] = None,
        distance_func: str = "cosine",
        n_trees: int = 100  # Number of trees for Annoy index
    ):
        """
        Initialize the Annoy vector store.
        
        Args:
            collection_name: Name of the collection
            base_path: Path to store vector database
            data_path: Path to store document data
            embedding_function: Function to create embeddings
            distance_func: Distance function ('cosine', 'l2', 'ip')
            n_trees: Number of trees for Annoy index (more = better accuracy but slower)
        """
        if not ANNOY_AVAILABLE:
            raise ImportError("Annoy is not installed. Please install it with 'pip install annoy'.")
            
        self.n_trees = n_trees
        
        # Map distance functions to Annoy metric types
        self.metric_map = {
            "cosine": "angular",
            "l2": "euclidean",
            "ip": "dot"
        }
        
        super().__init__(
            collection_name=collection_name,
            base_path=base_path,
            data_path=data_path,
            embedding_function=embedding_function,
            distance_func=distance_func
        )
    
    def _init_store(self):
        """Initialize the Annoy vector store."""
        # Paths for storing index and metadata
        self.index_path = os.path.join(self.base_path, f"{self.collection_name}.annoy")
        self.metadata_path = os.path.join(self.base_path, f"{self.collection_name}_metadata.pickle")
        
        # Get embedding dimensions by creating a sample embedding
        sample_embedding = self.embedding_function("sample text")
        self.embedding_dim = len(sample_embedding)
        
        # Get Annoy metric type
        self.metric = self.metric_map.get(self.distance_func, "angular")
        
        # Initialize index
        self.index = AnnoyIndex(self.embedding_dim, self.metric)
        
        # Check if index and metadata exist
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            # Load existing index and metadata
            self.index.load(self.index_path)
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
        else:
            # Create new metadata
            self.metadata = {
                "documents": [],
                "metadatas": [],
                "ids": [],
                "index_map": {}  # Maps ID to index in the Annoy index
            }
        
        logger.info(f"Annoy index initialized with dimension {self.embedding_dim} and metric {self.metric}")
    
    def _save_index(self):
        """Save Annoy index and metadata to disk."""
        try:
            # Save index
            self.index.save(self.index_path)
            
            # Save metadata
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
                
            logger.debug(f"Annoy index saved to {self.index_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving Annoy index: {str(e)}")
            return False
    
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
        
        # Generate IDs if not provided
        if ids is None:
            ids = [self.generate_id() for _ in range(len(texts))]
        
        # Create metadata if not provided
        if metadatas is None:
            metadatas = [{} for _ in range(len(texts))]
        
        # Start with current index size
        current_index = len(self.metadata["documents"])
        
        # Add embeddings to index
        for i, text in enumerate(texts):
            # Generate embedding
            embedding = self.embedding_function(text)
            
            # Add to Annoy index
            self.index.add_item(current_index + i, embedding)
            
            # Update index map
            self.metadata["index_map"][ids[i]] = current_index + i
        
        # Add to metadata
        self.metadata["documents"].extend(texts)
        self.metadata["metadatas"].extend(metadatas)
        self.metadata["ids"].extend(ids)
        
        # Build index if it's the first time
        if current_index == 0:
            self.index.build(self.n_trees)
        
        # Save index and metadata
        self._save_index()
        
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
        if self.count() == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_function(query)
        
        # Find n nearest neighbors, get more to allow for filtering
        search_limit = min(self.count(), max(100, limit * 10))
        indices, distances = self.index.get_nns_by_vector(
            query_embedding, 
            search_limit, 
            include_distances=True
        )
        
        # Get results
        results = []
        for i, idx in enumerate(indices):
            # Get metadata and document text
            doc_index = self.metadata["ids"].index(self._get_id_from_index(idx))
            metadata = self.metadata["metadatas"][doc_index]
            document = self.metadata["documents"][doc_index]
            doc_id = self.metadata["ids"][doc_index]
            
            # Filter by metadata if where condition is provided
            if where and not self._matches_filter(metadata, where):
                continue
            
            # Add to results
            if self.metric == "angular":
                # Convert angular distance to cosine similarity
                score = 1.0 - (distances[i] / 2.0)
            elif self.metric == "dot":
                # Dot product is already a similarity
                score = float(distances[i])
            else:
                # For euclidean distance, invert and normalize to a similarity
                score = 1.0 / (1.0 + float(distances[i]))
            
            result = {
                "id": doc_id,
                "text": document,
                "metadata": metadata,
                "score": score
            }
            
            results.append(result)
            
            # Limit results
            if len(results) >= limit:
                break
        
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
        for i, doc_id in enumerate(self.metadata["ids"]):
            # Filter by ID if provided
            if ids and doc_id not in ids:
                continue
                
            # Filter by metadata if provided
            if where and not self._matches_filter(self.metadata["metadatas"][i], where):
                continue
                
            # Add to results
            result_documents.append(self.metadata["documents"][i])
            result_metadatas.append(self.metadata["metadatas"][i])
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
        return len(self.metadata["documents"])
    
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
        # Find indices to keep
        indices_to_keep = []
        
        for i, doc_id in enumerate(self.metadata["ids"]):
            should_delete = False
            
            # Check if ID matches
            if ids and doc_id in ids:
                should_delete = True
            
            # Check if metadata matches
            if where and self._matches_filter(self.metadata["metadatas"][i], where):
                should_delete = True
            
            if not should_delete:
                indices_to_keep.append(i)
        
        # If no changes, return
        if len(indices_to_keep) == self.count():
            return True
        
        # Create new metadata
        new_documents = [self.metadata["documents"][i] for i in indices_to_keep]
        new_metadatas = [self.metadata["metadatas"][i] for i in indices_to_keep]
        new_ids = [self.metadata["ids"][i] for i in indices_to_keep]
        
        # For Annoy, we need to rebuild the entire index
        # since it doesn't support removing items
        if new_documents:
            # Create new index
            new_index = AnnoyIndex(self.embedding_dim, self.metric)
            
            # Add vectors to the new index
            new_index_map = {}
            
            for i, (text, doc_id) in enumerate(zip(new_documents, new_ids)):
                # Generate embedding
                embedding = self.embedding_function(text)
                
                # Add to index
                new_index.add_item(i, embedding)
                
                # Update index map
                new_index_map[doc_id] = i
            
            # Build the index
            new_index.build(self.n_trees)
            
            # Update the index and metadata
            self.index = new_index
            self.metadata = {
                "documents": new_documents,
                "metadatas": new_metadatas,
                "ids": new_ids,
                "index_map": new_index_map
            }
        else:
            # Reset if no documents left
            self.index = AnnoyIndex(self.embedding_dim, self.metric)
            self.metadata = {
                "documents": [],
                "metadatas": [],
                "ids": [],
                "index_map": {}
            }
        
        # Save index and metadata
        self._save_index()
        
        return True
    
    def reset(self) -> bool:
        """
        Reset the vector store.
        
        Returns:
            True if successful
        """
        try:
            # Create new index
            self.index = AnnoyIndex(self.embedding_dim, self.metric)
            
            # Reset metadata
            self.metadata = {
                "documents": [],
                "metadatas": [],
                "ids": [],
                "index_map": {}
            }
            
            # Save changes
            self._save_index()
            
            logger.info("Annoy vector store reset")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting vector store: {str(e)}")
            return False
    
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
    
    def _get_id_from_index(self, idx: int) -> str:
        """Get document ID from index."""
        for doc_id, index in self.metadata["index_map"].items():
            if index == idx:
                return doc_id
        
        # This should not happen, but just in case
        return self.metadata["ids"][0]

# Register the vector store if Annoy is available
if ANNOY_AVAILABLE:
    register_vector_store("annoy", AnnoyVectorStore)