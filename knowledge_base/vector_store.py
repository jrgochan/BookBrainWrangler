"""
Vector store module for the Knowledge Base.
Handles interactions with ChromaDB for vector storage and retrieval.
"""

import os
import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from utils.logger import get_logger

# Get logger
logger = get_logger(__name__)

class VectorStore:
    """
    Handles vector storage and retrieval operations with ChromaDB.
    """
    def __init__(self, embedding_function, 
                 persist_directory=None, 
                 collection_name="book_knowledge_base",
                 distance_function="cosine"):
        """
        Initialize the vector store.
        
        Args:
            embedding_function: The embedding function to use
            persist_directory: Directory to persist the database (None for in-memory)
            collection_name: Name of the collection to use
            distance_function: Distance function for similarity search (cosine, l2, ip)
        """
        self.embedding_function = embedding_function
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.distance_function = distance_function
        
        # Initialize the vector store
        self._initialize_vector_store()
        
    def _get_writable_directory(self, base_dir="knowledge_base_data"):
        """
        Get a writable directory for the vector store data.
        
        Args:
            base_dir: Base directory name
            
        Returns:
            Path to the writable directory
        """
        # If a persist directory is already set, use that
        if self.persist_directory:
            os.makedirs(self.persist_directory, exist_ok=True)
            return self.persist_directory
        
        # Otherwise, create a default directory
        kb_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", base_dir)
        os.makedirs(kb_dir, exist_ok=True)
        
        # Create the chroma directory
        chroma_dir = os.path.join(kb_dir, "chroma_db")
        os.makedirs(chroma_dir, exist_ok=True)
        
        return chroma_dir
        
    def _initialize_vector_store(self):
        """Initialize the vector store with ChromaDB."""
        try:
            # Get a writable directory
            if self.persist_directory is None:
                self.persist_directory = self._get_writable_directory()
                
            logger.info(f"Initializing vector store at {self.persist_directory}")
                
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Create or get the collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": self.distance_function}
            )
            
            # Create LangChain Chroma instance for higher-level operations
            self.vector_store = Chroma(
                client=self.chroma_client,
                collection_name=self.collection_name,
                embedding_function=self.embedding_function
            )
            
            logger.info(f"Vector store initialized with collection '{self.collection_name}'")
            
        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            raise
    
    def add_texts(self, texts, metadatas=None, ids=None):
        """
        Add texts to the vector store.
        
        Args:
            texts: List of texts to add
            metadatas: List of metadata dictionaries
            ids: List of IDs for the texts
            
        Returns:
            List of IDs of the added texts
        """
        try:
            result = self.vector_store.add_texts(
                texts=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            count = len(texts) if texts else 0
            logger.info(f"Added {count} documents to vector store")
            return result
            
        except Exception as e:
            logger.error(f"Error adding texts to vector store: {str(e)}")
            raise
    
    def similarity_search(self, query, k=5, filter=None):
        """
        Search for similar documents.
        
        Args:
            query: Query text
            k: Number of results to return
            filter: Dictionary of metadata field/value pairs to filter by
            
        Returns:
            List of documents
        """
        try:
            docs = self.vector_store.similarity_search(
                query=query,
                k=k,
                filter=filter
            )
            
            logger.info(f"Retrieved {len(docs)} documents for query: {query[:50]}...")
            return docs
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            raise
    
    def similarity_search_with_relevance_scores(self, query, k=5, filter=None):
        """
        Search for similar documents with relevance scores.
        
        Args:
            query: Query text
            k: Number of results to return
            filter: Dictionary of metadata field/value pairs to filter by
            
        Returns:
            List of (document, score) tuples
        """
        try:
            results = self.vector_store.similarity_search_with_relevance_scores(
                query=query,
                k=k,
                filter=filter
            )
            
            logger.info(f"Retrieved {len(results)} scored documents for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store with scores: {str(e)}")
            raise
    
    def delete(self, filter=None, ids=None):
        """
        Delete documents from the vector store.
        
        Args:
            filter: Dictionary of metadata field/value pairs to filter by
            ids: List of IDs to delete
            
        Returns:
            Success status
        """
        try:
            if ids:
                logger.info(f"Deleting {len(ids)} documents by ID from vector store")
                return self.vector_store.delete(ids=ids)
            elif filter:
                logger.info(f"Deleting documents with filter {filter} from vector store")
                return self.vector_store.delete(filter=filter)
            else:
                logger.warning("No filter or IDs provided for deletion")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting from vector store: {str(e)}")
            raise
    
    def clear(self):
        """
        Clear all documents from the vector store.
        
        Returns:
            Success status
        """
        try:
            # Get all existing IDs first
            result = self.collection.get(limit=10000)
            if result and 'ids' in result and result['ids']:
                ids = result['ids']
                # Delete by IDs
                self.collection.delete(ids=ids)
                logger.info(f"Cleared {len(ids)} documents from vector store")
            else:
                # No documents to delete
                logger.info("No documents to clear from vector store")
                
            return True
            
        except Exception as e:
            logger.error(f"Error clearing vector store: {str(e)}")
            # Attempt to recreate the collection if deletion fails
            try:
                logger.info("Attempting to recreate the collection as fallback")
                # Delete and recreate the collection
                self.chroma_client.delete_collection(name=self.collection_name)
                self.collection = self.chroma_client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": self.distance_function}
                )
                # Recreate the LangChain wrapper
                self.vector_store = Chroma(
                    client=self.chroma_client,
                    collection_name=self.collection_name,
                    embedding_function=self.embedding_function
                )
                logger.info("Successfully recreated collection")
                return True
            except Exception as recreation_error:
                logger.error(f"Failed to recreate collection: {str(recreation_error)}")
                raise
            
    def count(self):
        """
        Get the number of documents in the vector store.
        
        Returns:
            Document count
        """
        try:
            count = self.collection.count()
            logger.debug(f"Vector store contains {count} documents")
            return count
            
        except Exception as e:
            logger.error(f"Error counting documents in vector store: {str(e)}")
            raise
            
    def get_stats(self):
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary of statistics
        """
        try:
            count = self.collection.count()
            
            # Extract content types from collection if available
            content_types = set()
            try:
                # Try to get a sample of documents to extract content types
                results = self.collection.get(limit=100)
                if results and 'metadatas' in results and results['metadatas']:
                    for metadata in results['metadatas']:
                        if metadata and 'content_type' in metadata:
                            content_types.add(metadata['content_type'])
            except Exception as e:
                logger.error(f"Error getting content types: {str(e)}")
                # Default to typical content types
                content_types = set(['text', 'image_caption'])
            
            stats = {
                'document_count': count,
                'document_types': list(content_types),
                'collection_name': self.collection_name,
                'persist_directory': self.persist_directory,
            }
            
            logger.debug(f"Retrieved vector store stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting vector store stats: {str(e)}")
            raise
