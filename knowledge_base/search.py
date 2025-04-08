"""
Search module for the Knowledge Base.
Handles searching and retrieving documents from the vector database.
"""

from utils.logger import get_logger

# Get logger
logger = get_logger(__name__)

class VectorSearch:
    """
    Handles search operations against the vector database.
    """
    def __init__(self, vector_store):
        """
        Initialize the search engine.
        
        Args:
            vector_store: The VectorStore instance to use for searching
        """
        self.vector_store = vector_store
    
    def retrieve_documents(self, query, num_results=5, filter=None):
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: The search query
            num_results: Number of top results to return
            filter: Dictionary of metadata field/value pairs to filter by
            
        Returns:
            List of documents
        """
        try:
            # Check if the vector store has documents
            count = self.vector_store.count()
            if count == 0:
                logger.warning("Empty vector store, no results can be retrieved")
                return []
            
            # Retrieve documents from the vector store
            docs = self.vector_store.similarity_search(
                query=query,
                k=num_results,
                filter=filter
            )
            
            logger.info(f"Retrieved {len(docs)} documents for query: {query[:50]}...")
            return docs
            
        except Exception as e:
            logger.error(f"Error retrieving documents for query '{query}': {str(e)}")
            return []
    
    def retrieve_documents_with_scores(self, query, num_results=5, filter=None):
        """
        Retrieve relevant documents with similarity scores.
        
        Args:
            query: The search query
            num_results: Number of top results to return
            filter: Dictionary of metadata field/value pairs to filter by
            
        Returns:
            List of (document, score) tuples
        """
        try:
            # Check if the vector store has documents
            count = self.vector_store.count()
            if count == 0:
                logger.warning("Empty vector store, no results can be retrieved")
                return []
            
            # Retrieve documents from the vector store
            results = self.vector_store.similarity_search_with_relevance_scores(
                query=query,
                k=num_results,
                filter=filter
            )
            
            logger.info(f"Retrieved {len(results)} scored documents for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving scored documents for query '{query}': {str(e)}")
            return []
    
    def get_raw_documents_with_query(self, query, num_results=5, filter=None):
        """
        Retrieve documents with scores in a structured format for UI display.
        
        Args:
            query: The search query
            num_results: Number of top results to return
            filter: Dictionary of metadata field/value pairs to filter by
            
        Returns:
            List of dictionaries with document data and similarity score
        """
        try:
            # Check if the vector store has documents
            count = self.vector_store.count()
            if count == 0:
                logger.warning("Empty vector store, no results can be retrieved")
                return []
            
            # Retrieve documents from the vector store
            results = self.vector_store.similarity_search_with_relevance_scores(
                query=query,
                k=num_results,
                filter=filter
            )
            
            if not results:
                return []
            
            # Format the results
            formatted_results = []
            
            for doc, score in results:
                formatted_results.append({
                    'similarity': float(score),  # Ensure score is a Python float
                    'document': {
                        'page_content': doc.page_content,
                        'metadata': doc.metadata
                    }
                })
            
            logger.info(f"Retrieved {len(formatted_results)} raw documents for query: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error retrieving raw documents for query '{query}': {str(e)}")
            return []
    
    def retrieve_relevant_context(self, query, num_results=5, filter=None):
        """
        Retrieve relevant context as formatted text for a query.
        
        Args:
            query: The search query
            num_results: Number of top results to return
            filter: Dictionary of metadata field/value pairs to filter by
            
        Returns:
            A string with the combined relevant text passages
        """
        try:
            # Check if the vector store has documents
            count = self.vector_store.count()
            if count == 0:
                logger.warning("Empty vector store, no results can be retrieved")
                return "No documents found in the knowledge base."
            
            # Retrieve documents from the vector store
            results = self.vector_store.similarity_search_with_relevance_scores(
                query=query,
                k=num_results,
                filter=filter
            )
            
            if not results:
                return "No relevant documents found for this query."
            
            # Format the results into a readable context
            context_parts = []
            
            for i, (doc, score) in enumerate(results):
                # Extract content and metadata
                content = doc.page_content
                metadata = doc.metadata
                
                # Format document with source information
                source_info = f"[Source: {metadata.get('source', 'Unknown')}]"
                if 'page' in metadata:
                    source_info += f" [Page: {metadata.get('page', '?')}]"
                    
                formatted_doc = f"--- Document {i+1} ({score:.2f} relevance) ---\n{source_info}\n{content}\n"
                context_parts.append(formatted_doc)
            
            # Combine all context parts
            combined_context = "\n".join(context_parts)
            
            logger.info(f"Retrieved formatted context with {len(results)} documents for query: {query[:50]}...")
            return combined_context
            
        except Exception as e:
            logger.error(f"Error retrieving context for query '{query}': {str(e)}")
            return f"Error retrieving documents: {str(e)}"
