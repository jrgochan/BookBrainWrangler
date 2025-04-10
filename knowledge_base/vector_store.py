"""
Vector store implementation for knowledge base.
This module is maintained for backward compatibility.
New code should use the vector_stores module.
"""

import os
import uuid
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
        vector_store_type: str = DEFAULT_VECTOR_STORE,
        use_gpu: bool = True
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
            use_gpu: Whether to use GPU acceleration for FAISS (if available)
        """
        self.collection_name = collection_name
        self.base_path = base_path
        self.data_path = data_path
        self.distance_func = distance_func
        self.vector_store_type = vector_store_type
        # Store the GPU preference for later use in property accessors
        self.gpu_enabled = use_gpu
        
        # Set embedding function
        if embedding_function is None:
            self.embedding_function = get_embedding_function()
        else:
            self.embedding_function = embedding_function
            
        # Create kwargs for vector store initialization
        kwargs = {
            'collection_name': collection_name,
            'base_path': base_path,
            'data_path': data_path,
            'embedding_function': self.embedding_function,
            'distance_func': distance_func
        }
        
        # Add use_gpu parameter for FAISS
        if vector_store_type == 'faiss':
            kwargs['use_gpu'] = use_gpu
            
        # Create the underlying vector store
        self.vector_store = get_vector_store(
            store_type=vector_store_type,
            **kwargs
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
        
    def generate_id(self) -> str:
        """
        Generate a unique ID for a document.
        
        Returns:
            A unique string ID
        """
        return str(uuid.uuid4())
        
    @property
    def using_gpu(self) -> bool:
        """
        Check if the vector store is using GPU acceleration.
        
        Returns:
            True if using GPU, False otherwise
        """
        if hasattr(self.vector_store, 'using_gpu'):
            return self.vector_store.using_gpu
        return False
        
    @property
    def use_gpu(self) -> bool:
        """
        Get the use_gpu setting.
        
        Returns:
            True if GPU use is enabled, False otherwise
        """
        # First check if the underlying vector store has this property
        if hasattr(self.vector_store, 'use_gpu'):
            return self.vector_store.use_gpu
        # Fall back to the stored attribute if the vector store doesn't have the property
        return getattr(self, 'gpu_enabled', True)
        
    def get_indexed_book_ids(self) -> List[str]:
        """
        Get the IDs of all books/documents indexed in the knowledge base.
        
        Returns:
            List of document IDs
        """
        documents = self.list_documents()
        # Extract unique document IDs from the documents
        book_ids = []
        seen_ids = set()
        
        for doc in documents:
            doc_id = doc.get('id')
            if doc_id and doc_id not in seen_ids:
                book_ids.append(doc_id)
                seen_ids.add(doc_id)
        
        return book_ids
        
    def get_document_chunks(self, document_id: str) -> List[Any]:
        """
        Get all chunks for a specific document.
        
        Args:
            document_id: Document ID
            
        Returns:
            List of chunks for the document
        """
        # Get all chunks where the document_id matches
        results = self.get(where={"document_id": document_id})
        
        # Extract chunks from results
        chunks = []
        if results and "documents" in results:
            for i, doc in enumerate(results["documents"]):
                # Create a chunk object with page_content
                chunk = type('Chunk', (), {})()
                chunk.page_content = doc
                
                # Add metadata if available
                if "metadatas" in results and i < len(results["metadatas"]):
                    for key, value in results["metadatas"][i].items():
                        setattr(chunk, key, value)
                
                # Add ID if available
                if "ids" in results and i < len(results["ids"]):
                    chunk.id = results["ids"][i]
                
                chunks.append(chunk)
        
        return chunks
        
    def toggle_book_in_knowledge_base(
        self, 
        book_id: str, 
        content: Optional[str] = None, 
        add_to_kb: bool = True,
        progress_callback: Optional[Callable[[float, int, str], None]] = None
    ) -> bool:
        """
        Toggle a book's inclusion in the knowledge base.
        
        Args:
            book_id: Book ID
            content: Book content (required if adding to KB)
            add_to_kb: True to add to KB, False to remove
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if operation was successful
        """
        if add_to_kb:
            if not content:
                logger.error(f"Cannot add book {book_id} to knowledge base: no content provided")
                return False
                
            # Add document to knowledge base
            try:
                self.add_document(
                    document_id=book_id,
                    text=content
                )
                logger.info(f"Added book {book_id} to knowledge base")
                return True
            except Exception as e:
                logger.error(f"Error adding book {book_id} to knowledge base: {str(e)}")
                return False
        else:
            # Remove document from knowledge base
            try:
                success = self.delete_document(book_id)
                if success:
                    logger.info(f"Removed book {book_id} from knowledge base")
                else:
                    logger.error(f"Failed to remove book {book_id} from knowledge base")
                return success
            except Exception as e:
                logger.error(f"Error removing book {book_id} from knowledge base: {str(e)}")
                return False
                
    def rebuild_knowledge_base(
        self, 
        book_manager: Any,
        progress_callback: Optional[Callable[[float, int, str], None]] = None
    ) -> bool:
        """
        Rebuild the knowledge base from scratch.
        
        Args:
            book_manager: BookManager instance
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if successful
        """
        try:
            # Reset the vector store
            self.reset()
            logger.info("Vector store reset")
            
            # Get all books
            indexed_book_ids = self.get_indexed_book_ids()
            
            # Re-add each book
            total_books = len(indexed_book_ids)
            for i, book_id in enumerate(indexed_book_ids):
                # Get book details
                book = book_manager.get_book(book_id)
                
                if not book:
                    logger.warning(f"Book {book_id} not found in book manager")
                    continue
                
                # Get book content
                content = book_manager.get_book_content(book_id)
                
                if not content:
                    logger.warning(f"No content found for book {book_id}")
                    continue
                
                # Update progress
                if progress_callback:
                    progress = (i / total_books)
                    progress_callback(progress, i, f"Processing book {i+1}/{total_books}: {book['title']}")
                
                # Add to vector store
                self.add_document(
                    document_id=book_id,
                    text=content,
                    metadata=book
                )
                
                logger.info(f"Re-added book {book_id} to knowledge base")
            
            # Final progress update
            if progress_callback:
                progress_callback(1.0, total_books, "Knowledge base rebuild complete")
                
            logger.info("Knowledge base rebuilt successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error rebuilding knowledge base: {str(e)}")
            return False
            
    def get_vector_store_stats(self) -> Dict[str, Any]:
        """
        Get vector store statistics.
        
        Returns:
            Dictionary of statistics
        """
        return self.get_stats()
        
    def retrieve_relevant_context(self, query: str, num_results: int = 5) -> str:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: The query string
            num_results: Maximum number of results to return
            
        Returns:
            A string containing the relevant context
        """
        try:
            results = self.search(query, limit=num_results)
            
            # Concatenate the results into a single context string
            context_parts = []
            for result in results:
                context_parts.append(result.get('text', ''))
                
            return '\n\n'.join(context_parts)
        except Exception as e:
            logger.error(f"Error retrieving context for query '{query}': {str(e)}")
            return ""
