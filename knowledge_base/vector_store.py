"""
Vector store module for Book Knowledge AI.
Provides vector database functionality for the knowledge base.
"""

import os
import json
import uuid
from typing import List, Dict, Any, Optional, Union, Callable, Tuple

from utils.logger import get_logger
from core.exceptions import VectorStoreError, EmbeddingError
from knowledge_base.config import (
    DEFAULT_VECTOR_DIR, DEFAULT_DATA_DIR, DEFAULT_COLLECTION_NAME,
    DEFAULT_DISTANCE_FUNC, DEFAULT_EMBEDDING_DIMENSION
)
from knowledge_base.utils import (
    generate_id, 
    save_document_to_disk, 
    load_document_from_disk,
    delete_document_from_disk,
    list_documents_on_disk,
    clean_knowledge_base
)
from knowledge_base.embedding import (
    get_embedding_function,
    get_embeddings,
    default_embedding_function
)
from knowledge_base.chunking import chunk_document

# Try to import chromadb
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

# Initialize logger
logger = get_logger(__name__)

class KnowledgeBase:
    """
    Knowledge base with vector search capabilities.
    Uses ChromaDB if available, otherwise falls back to a simpler implementation.
    """
    
    def __init__(
        self,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        base_path: str = DEFAULT_VECTOR_DIR,
        data_path: str = DEFAULT_DATA_DIR,
        embedding_function: Optional[Callable] = None,
        distance_func: str = DEFAULT_DISTANCE_FUNC
    ):
        """
        Initialize the knowledge base.
        
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
        self.embedding_function = embedding_function or default_embedding_function
        
        # Initialize vector store
        self._init_vector_store()
        
        logger.info(f"Knowledge base initialized with collection '{collection_name}'")
    
    def _init_vector_store(self):
        """Initialize the vector store."""
        if CHROMADB_AVAILABLE:
            self._init_chromadb()
        else:
            self._init_simple_store()
    
    def _init_chromadb(self):
        """Initialize ChromaDB."""
        try:
            # Configure persistent client
            self.client = chromadb.PersistentClient(
                path=self.base_path,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": self.distance_func},
                embedding_function=self.embedding_function
            )
            
            logger.info(f"ChromaDB collection '{self.collection_name}' initialized")
        
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {str(e)}")
            # Fall back to simple store
            self._init_simple_store()
    
    def _init_simple_store(self):
        """Initialize simple vector store."""
        logger.warning("ChromaDB not available, using simple in-memory store")
        
        # Create a simple in-memory collection
        self.client = None
        self.collection = {
            "documents": [],
            "embeddings": [],
            "metadatas": [],
            "ids": []
        }
    
    def add_document(
        self,
        document_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> str:
        """
        Add a document to the knowledge base.
        
        Args:
            document_id: Document ID
            text: Document text content
            metadata: Optional document metadata
            chunk_size: Optional custom chunk size
            chunk_overlap: Optional custom chunk overlap
            
        Returns:
            Document ID
        """
        try:
            if not text:
                logger.warning("Empty document text, not adding to knowledge base")
                return document_id
            
            # Create document
            document = {
                "id": document_id,
                "text": text,
                "metadata": metadata or {}
            }
            
            # Save document to disk
            save_document_to_disk(document, self.data_path)
            
            # Chunk document
            chunks = chunk_document(document, chunk_size, chunk_overlap)
            
            # Add chunks to vector store
            self._add_chunks(chunks)
            
            logger.info(f"Added document '{document_id}' to knowledge base")
            return document_id
            
        except Exception as e:
            logger.error(f"Error adding document to knowledge base: {str(e)}")
            raise VectorStoreError(f"Failed to add document: {str(e)}")
    
    def _add_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Add chunks to the vector store.
        
        Args:
            chunks: Document chunks to add
        """
        if not chunks:
            return
        
        try:
            # Extract data
            ids = [chunk["id"] for chunk in chunks]
            texts = [chunk["text"] for chunk in chunks]
            metadatas = [chunk["metadata"] for chunk in chunks]
            
            if CHROMADB_AVAILABLE:
                # Add to ChromaDB
                self.collection.add(
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
            else:
                # Add to simple store
                embeddings = [get_embeddings(text) for text in texts]
                
                # Extend the lists
                self.collection["documents"].extend(texts)
                self.collection["embeddings"].extend(embeddings)
                self.collection["metadatas"].extend(metadatas)
                self.collection["ids"].extend(ids)
                
            logger.info(f"Added {len(chunks)} chunks to vector store")
                
        except Exception as e:
            logger.error(f"Error adding chunks to vector store: {str(e)}")
            raise VectorStoreError(f"Failed to add chunks: {str(e)}")
    
    def search(
        self,
        query: str,
        limit: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge base.
        
        Args:
            query: Search query
            limit: Maximum number of results
            where: Filter condition
            
        Returns:
            List of search results
        """
        try:
            if not query:
                return []
            
            if CHROMADB_AVAILABLE:
                # Search ChromaDB
                results = self.collection.query(
                    query_texts=[query],
                    n_results=limit,
                    where=where
                )
                
                # Format results
                formatted_results = []
                
                if results and "documents" in results and results["documents"]:
                    for i, doc in enumerate(results["documents"][0]):
                        if i < len(results["ids"][0]) and i < len(results["metadatas"][0]) and i < len(results["distances"][0]):
                            result = {
                                "id": results["ids"][0][i],
                                "text": doc,
                                "metadata": results["metadatas"][0][i],
                                "score": 1.0 - min(results["distances"][0][i], 1.0)  # Convert distance to score
                            }
                            formatted_results.append(result)
                
                return formatted_results
                
            else:
                # Search simple store
                if not self.collection["documents"]:
                    return []
                
                # Get embedding for query
                query_embedding = get_embeddings(query)
                
                # Calculate scores
                scores = []
                for i, doc_embedding in enumerate(self.collection["embeddings"]):
                    # Filter by metadata if where is provided
                    if where and not self._matches_filter(self.collection["metadatas"][i], where):
                        continue
                    
                    # Calculate cosine similarity
                    similarity = self._cosine_similarity(query_embedding, doc_embedding)
                    scores.append((i, similarity))
                
                # Sort by score
                scores.sort(key=lambda x: x[1], reverse=True)
                
                # Format results
                formatted_results = []
                for i, score in scores[:limit]:
                    result = {
                        "id": self.collection["ids"][i],
                        "text": self.collection["documents"][i],
                        "metadata": self.collection["metadatas"][i],
                        "score": score
                    }
                    formatted_results.append(result)
                
                return formatted_results
                
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            return []
    
    def _cosine_similarity(self, v1, v2) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            v1: First vector
            v2: Second vector
            
        Returns:
            Cosine similarity (0-1)
        """
        import numpy as np
        
        v1 = np.array(v1)
        v2 = np.array(v2)
        
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
        
        cos_sim = dot_product / (norm_v1 * norm_v2)
        
        # Ensure result is between 0 and 1
        return max(0.0, min(cos_sim, 1.0))
    
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
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document from the knowledge base.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document or None if not found
        """
        try:
            # Load document from disk
            document = load_document_from_disk(document_id, self.data_path)
            
            if not document:
                return None
            
            # Get chunks for this document
            if CHROMADB_AVAILABLE:
                chunks = self.collection.get(
                    where={"document_id": document_id}
                )
                
                if chunks and "documents" in chunks and chunks["documents"]:
                    document["chunks"] = chunks["documents"]
            else:
                # Search in simple store
                chunks = []
                for i, metadata in enumerate(self.collection["metadatas"]):
                    if metadata.get("document_id") == document_id:
                        chunks.append(self.collection["documents"][i])
                
                document["chunks"] = chunks
            
            return document
            
        except Exception as e:
            logger.error(f"Error getting document '{document_id}': {str(e)}")
            return None
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the knowledge base.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            # Delete chunks from vector store
            if CHROMADB_AVAILABLE:
                self.collection.delete(
                    where={"document_id": document_id}
                )
            else:
                # Find chunks to delete in simple store
                to_delete = []
                for i, metadata in enumerate(self.collection["metadatas"]):
                    if metadata.get("document_id") == document_id:
                        to_delete.append(i)
                
                # Delete in reverse order to avoid index issues
                for i in sorted(to_delete, reverse=True):
                    self.collection["documents"].pop(i)
                    self.collection["embeddings"].pop(i)
                    self.collection["metadatas"].pop(i)
                    self.collection["ids"].pop(i)
            
            # Delete from disk
            deleted = delete_document_from_disk(document_id, self.data_path)
            
            logger.info(f"Deleted document '{document_id}' from knowledge base")
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting document '{document_id}': {str(e)}")
            return False
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents in the knowledge base.
        
        Returns:
            List of documents
        """
        try:
            # Get documents from disk
            return list_documents_on_disk(self.data_path)
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return []
    
    def reset(self) -> bool:
        """
        Reset the knowledge base.
        
        Returns:
            True if reset, False otherwise
        """
        try:
            # Reset vector store
            if CHROMADB_AVAILABLE:
                try:
                    self.client.delete_collection(self.collection_name)
                except Exception:
                    pass
                
                # Re-create collection
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": self.distance_func},
                    embedding_function=self.embedding_function
                )
            else:
                # Reset simple store
                self.collection = {
                    "documents": [],
                    "embeddings": [],
                    "metadatas": [],
                    "ids": []
                }
            
            # Clean files
            clean_knowledge_base(
                kb_dir=self.base_path,
                vector_dir=self.base_path,
                data_dir=self.data_path
            )
            
            logger.info("Knowledge base reset")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting knowledge base: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get knowledge base statistics.
        
        Returns:
            Dictionary of statistics
        """
        try:
            stats = {}
            
            # Count documents
            documents = self.list_documents()
            stats["document_count"] = len(documents)
            
            # Count chunks
            if CHROMADB_AVAILABLE:
                chunk_count = self.collection.count()
            else:
                chunk_count = len(self.collection["documents"])
            
            stats["chunk_count"] = chunk_count
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting knowledge base stats: {str(e)}")
            return {
                "document_count": 0,
                "chunk_count": 0
            }
    
    def generate_id(self) -> str:
        """
        Generate a unique document ID.
        
        Returns:
            Unique ID
        """
        return generate_id()