"""
Knowledge Base module for vectorizing and retrieving document content.
This is the main entry point for the knowledge base functionality.
"""

import os
import sqlite3
import time
from typing import Dict, List, Any, Optional, Union, Tuple, Callable

from utils.logger import get_logger
from knowledge_base.config import (
    DEFAULT_EMBEDDING_SETTINGS,
    DEFAULT_CHUNKING_SETTINGS,
    DEFAULT_VECTOR_STORE_SETTINGS,
    DEFAULT_DB_SETTINGS
)
from knowledge_base.embedding import EmbeddingModel
from knowledge_base.chunking import TextChunker
from knowledge_base.vector_store import VectorStore
from knowledge_base.search import VectorSearch
from knowledge_base.analytics import KnowledgeBaseAnalytics

# Get logger
logger = get_logger(__name__)

class KnowledgeBase:
    """
    Knowledge Base for document storage, retrieval, and querying.
    This class orchestrates the various components of the knowledge base.
    """
    def __init__(self, 
                 embedding_settings=None, 
                 chunking_settings=None,
                 vector_store_settings=None,
                 db_settings=None):
        """
        Initialize the knowledge base with modular components.
        
        Args:
            embedding_settings: Dictionary of embedding model settings
            chunking_settings: Dictionary of text chunking settings
            vector_store_settings: Dictionary of vector store settings
            db_settings: Dictionary of database settings
        """
        logger.info("Initializing Knowledge Base")
        
        # Apply default settings with any overrides
        self.embedding_settings = {**DEFAULT_EMBEDDING_SETTINGS, **(embedding_settings or {})}
        self.chunking_settings = {**DEFAULT_CHUNKING_SETTINGS, **(chunking_settings or {})}
        self.vector_store_settings = {**DEFAULT_VECTOR_STORE_SETTINGS, **(vector_store_settings or {})}
        self.db_settings = {**DEFAULT_DB_SETTINGS, **(db_settings or {})}
        
        # Initialize components
        self._init_components()
        self._init_database()
        
    def _init_components(self):
        """Initialize the knowledge base components."""
        try:
            # Initialize embedding model
            logger.debug("Initializing embedding model")
            self.embedding_model = EmbeddingModel(
                model_name=self.embedding_settings["model_name"],
                use_fallback=self.embedding_settings["use_fallback"]
            )
            
            # Initialize text chunker
            logger.debug("Initializing text chunker")
            self.text_chunker = TextChunker(
                chunk_size=self.chunking_settings["chunk_size"],
                chunk_overlap=self.chunking_settings["chunk_overlap"],
                is_separator_regex=self.chunking_settings["is_separator_regex"],
                separator=self.chunking_settings["separator"]
            )
            
            # Initialize vector store with embedding model
            logger.debug("Initializing vector store")
            self.vector_store = VectorStore(
                embedding_function=self.embedding_model,
                persist_directory=self._get_writable_data_dir(self.vector_store_settings["persist_directory"]),
                collection_name=self.vector_store_settings["collection_name"],
                distance_function=self.vector_store_settings["embedding_space"]
            )
            
            # Initialize search engine
            logger.debug("Initializing search engine")
            self.search_engine = VectorSearch(
                vector_store=self.vector_store
            )
            
            # Initialize analytics
            logger.debug("Initializing analytics")
            self.analytics = KnowledgeBaseAnalytics(
                vector_store=self.vector_store,
                db_path=self.db_settings["db_path"]
            )
            
            logger.info("Knowledge base components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing knowledge base components: {str(e)}")
            raise
    
    def _init_database(self):
        """Initialize the knowledge base database tables if they don't exist."""
        try:
            conn = sqlite3.connect(self.db_settings["db_path"])
            cursor = conn.cursor()
            
            # Create indexed_books table to track which books are in the KB
            cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.db_settings["table_name"]} (
                book_id INTEGER PRIMARY KEY,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Knowledge base SQL database initialized")
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def _get_writable_data_dir(self, subdir=None):
        """
        Get a writable directory for knowledge base data.
        
        Args:
            subdir: Subdirectory to create
            
        Returns:
            Path to a writable directory
        """
        # Create base dir relative to the knowledge_base module
        kb_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "knowledge_base_data")
        os.makedirs(kb_dir, exist_ok=True)
        
        # Create subdirectory if specified
        if subdir:
            full_path = os.path.join(kb_dir, subdir)
            os.makedirs(full_path, exist_ok=True)
            return full_path
            
        return kb_dir
    
    def toggle_book_in_knowledge_base(self, book_id, book_content, add_to_kb=True, progress_callback=None):
        """
        Add or remove a book from the knowledge base.
        
        Args:
            book_id: The ID of the book
            book_content: The book content - can be a string (text only) or a dictionary with 'text' and 'images' keys
            add_to_kb: If True, add to KB; if False, remove from KB
            progress_callback: Optional callback function for progress updates
        """
        conn = sqlite3.connect(self.db_settings["db_path"])
        cursor = conn.cursor()
        
        try:
            if add_to_kb:
                # Update progress if callback provided
                if progress_callback:
                    progress_callback(0, 100, "Adding book to knowledge base...")
                
                # Extract text content
                if isinstance(book_content, dict):
                    text_content = book_content.get('text', '')
                else:
                    text_content = book_content
                
                # Add text content to vector store
                if text_content:
                    if progress_callback:
                        progress_callback(30, 100, "Creating text embeddings...")
                    
                    self._add_to_vector_store(book_id, text_content)
                
                # Add images to vector store if available
                if isinstance(book_content, dict) and 'images' in book_content and book_content['images']:
                    if progress_callback:
                        progress_callback(80, 100, "Processing image content...")
                    
                    self._add_images_to_vector_store(book_id, book_content['images'])
                
                # Add to indexed_books table
                cursor.execute(
                    f"INSERT OR REPLACE INTO {self.db_settings['table_name']} (book_id) VALUES (?)",
                    (book_id,)
                )
                
                logger.info(f"Book {book_id} added to knowledge base")
                if progress_callback:
                    progress_callback(100, 100, "Book added to knowledge base")
            else:
                # Remove from knowledge base
                if progress_callback:
                    progress_callback(0, 100, "Removing book from knowledge base...")
                
                # Remove from vector store
                self._remove_from_vector_store(book_id)
                
                # Remove from indexed_books table
                cursor.execute(
                    f"DELETE FROM {self.db_settings['table_name']} WHERE book_id = ?",
                    (book_id,)
                )
                
                logger.info(f"Book {book_id} removed from knowledge base")
                if progress_callback:
                    progress_callback(100, 100, "Book removed from knowledge base")
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error toggling book {book_id} in knowledge base: {str(e)}")
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _add_to_vector_store(self, book_id, content):
        """
        Add a book's text content to the vector store.
        
        Args:
            book_id: The ID of the book
            content: The text content to add
        """
        try:
            # Split the text into manageable chunks
            chunks = self.text_chunker.split_text(content)
            
            # Track total chunks for this book
            total_chunks = len(chunks)
            logger.info(f"Processing {total_chunks} chunks for book {book_id}")
            
            # Prepare document metadata and IDs
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                # Create a unique ID for this chunk
                chunk_id = f"book_{book_id}_chunk_{i}"
                
                # Create metadata for this chunk
                metadata = {
                    "book_id": str(book_id),
                    "chunk_index": i,
                    "chunk_count": total_chunks,
                    "content_type": "text",
                    "source": f"Book {book_id}",
                    "page": i // 2 + 1,  # Rough estimate: 2 chunks per page
                }
                
                ids.append(chunk_id)
                metadatas.append(metadata)
            
            # Add documents to the vector store
            self.vector_store.add_texts(
                texts=chunks,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(chunks)} text chunks to vector store for book {book_id}")
            
        except Exception as e:
            logger.error(f"Error adding book {book_id} content to vector store: {str(e)}")
            raise
    
    def _add_images_to_vector_store(self, book_id, images):
        """
        Add a book's image content to the vector store.
        Each image is processed and added as a separate document with text description.
        
        Args:
            book_id: The ID of the book
            images: List of image dictionaries with 'page', 'index', 'description', and 'data' keys
        """
        try:
            # Prepare lists for batch processing
            texts = []
            metadatas = []
            ids = []
            
            for i, image in enumerate(images):
                # Extract image metadata
                page = image.get('page', 0)
                description = image.get('description', f"Image from book {book_id}")
                
                # Create a unique ID for this image
                image_id = f"book_{book_id}_image_{i}_page_{page}"
                
                # Create metadata for this image
                metadata = {
                    "book_id": str(book_id),
                    "content_type": "image_caption",
                    "image_index": i,
                    "page": page,
                    "source": f"Book {book_id}"
                }
                
                texts.append(description)
                metadatas.append(metadata)
                ids.append(image_id)
            
            # Add image descriptions to the vector store
            if texts:
                self.vector_store.add_texts(
                    texts=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                
                logger.info(f"Added {len(texts)} image descriptions to vector store for book {book_id}")
        
        except Exception as e:
            logger.error(f"Error adding book {book_id} images to vector store: {str(e)}")
            raise
    
    def _remove_from_vector_store(self, book_id):
        """
        Remove a book's content from the vector store.
        
        Args:
            book_id: The ID of the book to remove
        """
        try:
            # Use the filter parameter to delete all documents for this book
            self.vector_store.delete(
                filter={"book_id": str(book_id)}
            )
            
            logger.info(f"Removed all content for book {book_id} from vector store")
            
        except Exception as e:
            logger.error(f"Error removing book {book_id} from vector store: {str(e)}")
            raise
    
    def get_indexed_book_ids(self):
        """
        Get the IDs of all books in the knowledge base.
        
        Returns:
            List of book IDs
        """
        return self.analytics.get_indexed_book_ids()
        
    def search(self, query, limit=5, filter=None):
        """
        Search the knowledge base for relevant documents.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            filter: Optional metadata filters
            
        Returns:
            List of dictionaries with search results including score and document
        """
        try:
            # Use the search engine to get raw documents with scores
            results = self.search_engine.get_raw_documents_with_query(
                query=query,
                num_results=limit,
                filter=filter
            )
            
            logger.info(f"Search for '{query[:30]}...' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            return []
    
    def rebuild_knowledge_base(self, book_manager, progress_callback=None):
        """
        Rebuild the entire knowledge base from the books in the database.
        
        Args:
            book_manager: An instance of BookManager to get book content
            progress_callback: Optional callback function for progress updates
        """
        try:
            # Get all indexed book IDs
            book_ids = self.get_indexed_book_ids()
            
            if not book_ids:
                logger.info("No books to rebuild in knowledge base")
                if progress_callback:
                    progress_callback(0, 1, "No books to rebuild")
                return
            
            # Call the rebuild method with book_manager to handle content retrieval
            self._rebuild_vector_store(book_ids, book_manager, progress_callback)
            
            logger.info(f"Knowledge base rebuilt with {len(book_ids)} books")
            
        except Exception as e:
            logger.error(f"Error rebuilding knowledge base: {str(e)}")
            raise
    
    def _rebuild_vector_store(self, book_ids, book_manager=None, progress_callback=None):
        """
        Rebuild the vector store with only the specified books.
        
        Args:
            book_ids: List of book IDs to include
            book_manager: BookManager instance to get book content
            progress_callback: Optional callback function for progress updates
        """
        try:
            if progress_callback:
                progress_callback(0, 1, "Clearing vector store...")
            
            # Clear the existing collection
            self.vector_store.clear()
            logger.info("Vector store cleared for rebuild")
            
            # If no book manager is provided, we can only clear the store
            if not book_manager:
                logger.warning("No book manager provided for rebuild, only clearing store")
                if progress_callback:
                    progress_callback(1, 1, "Vector store cleared (no book manager to rebuild)")
                return
            
            # Process each book
            total_books = len(book_ids)
            for i, book_id in enumerate(book_ids):
                if progress_callback:
                    progress_callback(
                        i, 
                        total_books, 
                        f"Rebuilding vector store: {i+1}/{total_books} books"
                    )
                
                try:
                    # Get book content
                    book_content = book_manager.get_book_content(book_id)
                    
                    if book_content:
                        # Add text content to vector store
                        if isinstance(book_content, dict):
                            text_content = book_content.get('text', '')
                        else:
                            text_content = book_content
                            
                        if text_content:
                            self._add_to_vector_store(book_id, text_content)
                        
                        # Add images to vector store if available
                        if isinstance(book_content, dict) and 'images' in book_content and book_content['images']:
                            self._add_images_to_vector_store(book_id, book_content['images'])
                    
                    logger.info(f"Book {book_id} added to vector store during rebuild")
                except Exception as e:
                    logger.error(f"Error adding book {book_id} during rebuild: {str(e)}")
                    # Continue with other books even if one fails
            
            if progress_callback:
                progress_callback(total_books, total_books, "Knowledge base rebuild complete")
                
            logger.info("Vector store rebuild complete")
            
        except Exception as e:
            logger.error(f"Error rebuilding vector store: {str(e)}")
            raise
    
    def retrieve_relevant_context(self, query, num_results=5):
        """
        Retrieve relevant context from the knowledge base for a query.
        
        Args:
            query: The search query
            num_results: Number of top results to return
            
        Returns:
            A string with the combined relevant text passages
        """
        return self.search_engine.retrieve_relevant_context(query, num_results)
    
    def get_raw_documents_with_query(self, query, num_results=5):
        """
        Retrieve raw document objects with similarity scores for a query.
        This method is used by the knowledge base explorer to analyze results.
        
        Args:
            query: The search query
            num_results: Number of top results to return
            
        Returns:
            list: List of dictionaries with document data and similarity score
        """
        return self.search_engine.get_raw_documents_with_query(query, num_results)
    
    def get_vector_store_stats(self):
        """
        Get statistics about the vector store including document count, fields, etc.
        
        Returns:
            dict: Statistics about the vector store
        """
        return self.analytics.get_vector_store_stats()
