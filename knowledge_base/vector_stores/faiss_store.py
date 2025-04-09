"""
FAISS vector store implementation for Book Knowledge AI.
"""

import os
import faiss
import numpy as np
from typing import List, Dict, Any, Optional, Callable, Tuple
import pickle

from utils.logger import get_logger
from knowledge_base.vector_stores.base import BaseVectorStore
from knowledge_base.vector_stores import register_vector_store

logger = get_logger(__name__)

class FAISSVectorStore(BaseVectorStore):
    """Vector store with FAISS."""
    
    def __init__(
        self,
        collection_name: str = "book_knowledge",
        base_path: str = "./knowledge_base_data/vectors",
        data_path: str = "./knowledge_base_data/knowledge_base_data",
        embedding_function: Optional[Callable] = None,
        distance_func: str = "cosine"
    ):
        """
        Initialize the FAISS vector store.
        
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
        """Initialize the FAISS vector store."""
        # Path to store FAISS index and metadata
        self.index_path = os.path.join(self.base_path, f"{self.collection_name}.index")
        self.metadata_path = os.path.join(self.base_path, f"{self.collection_name}.pickle")
        
        # Get embedding dimensions by creating a sample embedding
        sample_embedding = self.embedding_function("sample text")
        self.embedding_dim = len(sample_embedding)
        
        # Check if index and metadata exist
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            # Load existing index and metadata
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
        else:
            # Create new index and metadata
            if self.distance_func == "cosine" or self.distance_func == "ip":
                # Inner product for cosine similarity (vectors should be normalized)
                self.index = faiss.IndexFlatIP(self.embedding_dim)
            else:
                # L2 distance
                self.index = faiss.IndexFlatL2(self.embedding_dim)
            
            self.metadata = {
                "documents": [],
                "metadatas": [],
                "ids": []
            }
        
        logger.info(f"FAISS index initialized with dimension {self.embedding_dim}")
    
    def _save_index(self):
        """Save FAISS index and metadata to disk."""
        try:
            # Save index
            faiss.write_index(self.index, self.index_path)
            
            # Save metadata
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
                
            logger.debug(f"FAISS index saved to {self.index_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving FAISS index: {str(e)}")
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
        
        # Generate embeddings
        embeddings = [self.embedding_function(text) for text in texts]
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Normalize vectors for cosine similarity
        if self.distance_func == "cosine":
            faiss.normalize_L2(embeddings_array)
        
        # Generate IDs if not provided
        if ids is None:
            ids = [self.generate_id() for _ in range(len(texts))]
        
        # Create metadata if not provided
        if metadatas is None:
            metadatas = [{} for _ in range(len(texts))]
        
        # Add to index
        self.index.add(embeddings_array)
        
        # Add to metadata
        self.metadata["documents"].extend(texts)
        self.metadata["metadatas"].extend(metadatas)
        self.metadata["ids"].extend(ids)
        
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
        
        # Convert to numpy array
        query_array = np.array([query_embedding]).astype('float32')
        
        # Normalize for cosine similarity
        if self.distance_func == "cosine":
            faiss.normalize_L2(query_array)
        
        # Search index
        scores, indices = self.index.search(query_array, self.count())
        
        # Get results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:  # FAISS returns -1 if there are not enough results
                break
                
            # Get metadata and document text
            metadata = self.metadata["metadatas"][idx]
            document = self.metadata["documents"][idx]
            doc_id = self.metadata["ids"][idx]
            
            # Filter by metadata if where condition is provided
            if where and not self._matches_filter(metadata, where):
                continue
            
            # Add to results
            result = {
                "id": doc_id,
                "text": document,
                "metadata": metadata,
                "score": float(scores[0][i])
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
        return self.index.ntotal
    
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
        indices_to_keep = []
        indices_to_remove = []
        
        for i, doc_id in enumerate(self.metadata["ids"]):
            should_delete = False
            
            # Check if ID matches
            if ids and doc_id in ids:
                should_delete = True
            
            # Check if metadata matches
            if where and self._matches_filter(self.metadata["metadatas"][i], where):
                should_delete = True
            
            if should_delete:
                indices_to_remove.append(i)
            else:
                indices_to_keep.append(i)
        
        if not indices_to_remove:
            return True  # Nothing to delete
        
        # Create a new index without the removed vectors
        if self.distance_func == "cosine" or self.distance_func == "ip":
            new_index = faiss.IndexFlatIP(self.embedding_dim)
        else:
            new_index = faiss.IndexFlatL2(self.embedding_dim)
        
        # Get vectors to keep
        keep_docs = [self.metadata["documents"][i] for i in indices_to_keep]
        keep_metadatas = [self.metadata["metadatas"][i] for i in indices_to_keep]
        keep_ids = [self.metadata["ids"][i] for i in indices_to_keep]
        
        # Create a new metadata dict
        new_metadata = {
            "documents": keep_docs,
            "metadatas": keep_metadatas,
            "ids": keep_ids
        }
        
        # If no documents left, just reset the index
        if not keep_docs:
            self.index = new_index
            self.metadata = new_metadata
            self._save_index()
            return True
        
        # Otherwise, add the kept vectors to the new index
        kept_embeddings = []
        for text in keep_docs:
            embedding = self.embedding_function(text)
            kept_embeddings.append(embedding)
        
        # Convert to numpy array
        embeddings_array = np.array(kept_embeddings).astype('float32')
        
        # Normalize vectors for cosine similarity
        if self.distance_func == "cosine":
            faiss.normalize_L2(embeddings_array)
        
        # Add vectors to the new index
        new_index.add(embeddings_array)
        
        # Update index and metadata
        self.index = new_index
        self.metadata = new_metadata
        
        # Save changes
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
            if self.distance_func == "cosine" or self.distance_func == "ip":
                self.index = faiss.IndexFlatIP(self.embedding_dim)
            else:
                self.index = faiss.IndexFlatL2(self.embedding_dim)
            
            # Reset metadata
            self.metadata = {
                "documents": [],
                "metadatas": [],
                "ids": []
            }
            
            # Save changes
            self._save_index()
            
            logger.info("FAISS vector store reset")
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

# Register the vector store
register_vector_store("faiss", FAISSVectorStore)