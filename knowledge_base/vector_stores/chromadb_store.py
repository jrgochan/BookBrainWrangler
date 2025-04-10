"""
ChromaDB vector store implementation for Book Knowledge AI.
"""

import os
import importlib.util
from typing import List, Dict, Any, Optional, Callable

from utils.logger import get_logger
from knowledge_base.vector_stores.base import BaseVectorStore
from knowledge_base.vector_stores import register_vector_store

logger = get_logger(__name__)

# Check if ChromaDB is available
CHROMADB_AVAILABLE = importlib.util.find_spec("chromadb") is not None

if CHROMADB_AVAILABLE:
    import chromadb
    from chromadb.config import Settings
    import chromadb.utils.embedding_functions as embedding_functions

class ChromaEmbeddingFunction(embedding_functions.EmbeddingFunction):
    """
    Wrapper class to adapt our embedding functions to ChromaDB's expected interface.
    ChromaDB expects embedding functions to have a specific signature.
    """
    
    def __init__(self, embedding_func: Callable):
        """
        Initialize with our embedding function.
        
        Args:
            embedding_func: The function to wrap
        """
        self.embedding_func = embedding_func
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            input: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not input:
            return []
            
        # Generate embeddings
        embeddings = []
        for text in input:
            # Get the embedding vector
            embedding_obj = self.embedding_func(text)
            # Extract the actual embedding array
            if hasattr(embedding_obj, 'embedding'):
                embeddings.append(embedding_obj.embedding)
            elif isinstance(embedding_obj, list):
                embeddings.append(embedding_obj)
            else:
                # Try to access as a dict
                try:
                    embeddings.append(embedding_obj.get('embedding', embedding_obj))
                except:
                    # If all else fails, use the object directly
                    embeddings.append(embedding_obj)
        
        return embeddings

class ChromaDBVectorStore(BaseVectorStore):
    """Vector store with ChromaDB."""
    
    def __init__(
        self,
        collection_name: str = "book_knowledge",
        base_path: str = "./knowledge_base_data/vectors",
        data_path: str = "./knowledge_base_data/knowledge_base_data",
        embedding_function: Optional[Callable] = None,
        distance_func: str = "cosine"
    ):
        """
        Initialize the ChromaDB vector store.
        
        Args:
            collection_name: Name of the collection
            base_path: Path to store vector database
            data_path: Path to store document data
            embedding_function: Function to create embeddings
            distance_func: Distance function ('cosine', 'l2', 'ip')
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB is not installed. Please install it with 'pip install chromadb'.")
            
        super().__init__(
            collection_name=collection_name,
            base_path=base_path,
            data_path=data_path,
            embedding_function=embedding_function,
            distance_func=distance_func
        )
    
    def _init_store(self):
        """Initialize the ChromaDB vector store."""
        # Set persistence path
        db_path = os.path.join(self.base_path, "chromadb")
        os.makedirs(db_path, exist_ok=True)
        
        # Create ChromaDB client
        self.client = chromadb.PersistentClient(path=db_path, settings=Settings(allow_reset=True))
        
        # Create ChromaDB embedding function wrapper
        chroma_ef = ChromaEmbeddingFunction(self.embedding_function)
        
        # Create or get collection
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=chroma_ef
            )
            logger.info(f"ChromaDB collection '{self.collection_name}' loaded")
        except Exception:
            # Collection doesn't exist, create it
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": self.distance_func},
                embedding_function=chroma_ef
            )
            logger.info(f"ChromaDB collection '{self.collection_name}' created")
    
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
        
        # Add to collection
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
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
        try:
            # Search collection
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=where
            )
            
            # Format results
            formatted_results = []
            
            if results and "documents" in results and results["documents"]:
                for i, document in enumerate(results["documents"][0]):
                    doc_id = results["ids"][0][i]
                    metadata = results["metadatas"][0][i]
                    score = float(results["distances"][0][i]) if "distances" in results else 0.0
                    
                    result = {
                        "id": doc_id,
                        "text": document,
                        "metadata": metadata,
                        "score": 1.0 - score  # Convert distance to similarity score
                    }
                    
                    formatted_results.append(result)
                    
            return formatted_results
                
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {str(e)}")
            return []
    
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
        try:
            # Query collection
            kwargs = {}
            if ids:
                kwargs["ids"] = ids
            if where:
                kwargs["where"] = where
                
            return self.collection.get(**kwargs)
                
        except Exception as e:
            logger.error(f"Error getting documents from ChromaDB: {str(e)}")
            return {
                "documents": [],
                "metadatas": [],
                "ids": []
            }
    
    def count(self) -> int:
        """
        Get the number of entries in the vector store.
        
        Returns:
            Number of entries
        """
        try:
            # Count method in newer versions of ChromaDB
            try:
                return self.collection.count()
            except AttributeError:
                # Fall back to get() method for older versions
                results = self.collection.get(include=["ids"])
                return len(results["ids"]) if "ids" in results else 0
                
        except Exception as e:
            logger.error(f"Error counting entries in ChromaDB: {str(e)}")
            return 0
    
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
        try:
            # Delete entries
            kwargs = {}
            if ids:
                kwargs["ids"] = ids
            if where:
                kwargs["where"] = where
                
            self.collection.delete(**kwargs)
            return True
                
        except Exception as e:
            logger.error(f"Error deleting entries from ChromaDB: {str(e)}")
            return False
    
    def reset(self) -> bool:
        """
        Reset the vector store.
        
        Returns:
            True if successful
        """
        try:
            # Delete collection
            try:
                self.client.delete_collection(self.collection_name)
            except Exception:
                pass
                
            # Re-create collection
            chroma_ef = ChromaEmbeddingFunction(self.embedding_function)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": self.distance_func},
                embedding_function=chroma_ef
            )
            
            logger.info("ChromaDB vector store reset")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting ChromaDB vector store: {str(e)}")
            return False

# Register the vector store if ChromaDB is available
if CHROMADB_AVAILABLE:
    register_vector_store("chromadb", ChromaDBVectorStore)