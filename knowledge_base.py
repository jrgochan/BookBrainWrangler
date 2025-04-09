"""
Knowledge Base module for vectorizing and retrieving document content.
Proxy module that imports from the refactored knowledge_base package.
"""

from utils.logger import get_logger
from knowledge_base import KnowledgeBase as NewKnowledgeBase

# Get logger
logger = get_logger(__name__)

class KnowledgeBase(NewKnowledgeBase):
    """
    Knowledge Base for document storage, retrieval, and querying.
    This class extends the refactored KnowledgeBase to maintain backward compatibility.
    """
    def __init__(self):
        """Initialize the knowledge base with default settings."""
        logger.info("Initializing Knowledge Base (proxy)")
        
        # Call parent constructor with default settings
        super().__init__()
        
        logger.info("Knowledge Base proxy initialized successfully")
    
    def is_document_indexed(self, book_id):
        """
        Check if a book is indexed in the knowledge base.
        
        Args:
            book_id: The ID of the book to check
            
        Returns:
            bool: True if the book is in the knowledge base, False otherwise
        """
        try:
            indexed_books = self.get_indexed_book_ids()
            return book_id in indexed_books
        except Exception as e:
            logger.error(f"Error checking if book {book_id} is indexed: {str(e)}")
            return False
    
    def get_document_chunks(self, book_id):
        """
        Get all chunks for a specific book from the vector store.
        
        Args:
            book_id: The ID of the book to retrieve chunks for
            
        Returns:
            list: List of document chunks with metadata
        """
        try:
            # Use search engine to fetch all documents with the given book_id
            # Since we just want to fetch and not search, we'll use a dummy query
            # with a high limit, filtered by book_id
            results = self.search_engine.get_raw_documents_with_query(
                query="",  # Empty query to match everything
                filter={"book_id": str(book_id)},
                num_results=1000  # Large number to get all chunks
            )
            
            # Extract the documents from the results
            chunks = []
            for result in results:
                # Include score and metadata in the chunk info
                chunk_info = {
                    "text": result["document"],
                    "metadata": result["metadata"],
                    "score": result.get("score", 1.0)
                }
                chunks.append(chunk_info)
            
            logger.info(f"Retrieved {len(chunks)} chunks for book {book_id}")
            return chunks
        except Exception as e:
            logger.error(f"Error retrieving chunks for book {book_id}: {str(e)}")
            return []
    
    def add_document(self, book_id, book_manager):
        """
        Add a book to the knowledge base.
        This method adds the book's content to the vector store.
        
        Args:
            book_id: The ID of the book to add
            book_manager: Instance of BookManager to retrieve book content
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get book content from the book manager
            content = book_manager.get_book_content(book_id)
            
            if not content:
                logger.warning(f"No content found for book {book_id}")
                return False
            
            # Add the book to the knowledge base
            self.toggle_book_in_knowledge_base(book_id, content, add_to_kb=True)
            
            logger.info(f"Successfully added book {book_id} to knowledge base")
            return True
        except Exception as e:
            logger.error(f"Error adding book {book_id} to knowledge base: {str(e)}")
            return False
    
    def remove_document(self, book_id):
        """
        Remove a book from the knowledge base.
        This method removes the book's content from the vector store.
        
        Args:
            book_id: The ID of the book to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Remove the book from the knowledge base
            self.toggle_book_in_knowledge_base(book_id, None, add_to_kb=False)
            
            logger.info(f"Successfully removed book {book_id} from knowledge base")
            return True
        except Exception as e:
            logger.error(f"Error removing book {book_id} from knowledge base: {str(e)}")
            return False
