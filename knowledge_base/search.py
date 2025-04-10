"""
Search module for Book Knowledge AI.
Handles searching the knowledge base.
"""

from typing import List, Dict, Any, Optional, Union
import re

from utils.logger import get_logger
from knowledge_base.config import (
    DEFAULT_SEARCH_LIMIT, DEFAULT_SEARCH_THRESHOLD
)
from knowledge_base import KnowledgeBase

# Get a logger for this module
logger = get_logger(__name__)

def search_knowledge_base(
    query: str,
    kb: KnowledgeBase,
    limit: int = DEFAULT_SEARCH_LIMIT,
    threshold: float = DEFAULT_SEARCH_THRESHOLD,
    filters: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Search the knowledge base.
    
    Args:
        query: Search query
        kb: KnowledgeBase instance
        limit: Maximum number of results
        threshold: Minimum score threshold
        filters: Optional search filters
        
    Returns:
        List of search results
    """
    try:
        # Clean query
        query = clean_query(query)
        
        # Check if query is valid
        if not query:
            logger.warning("Empty query provided for search")
            return []
        
        # Convert filters to vector store where clause if provided
        where = filters or {}
        
        # Perform search
        results = kb.search(query, limit=limit, where=where)
        
        # Apply threshold filter
        results = [r for r in results if r.get("score", 0) >= threshold]
        
        logger.info(f"Search for '{query}' returned {len(results)} results")
        
        return results
    
    except Exception as e:
        logger.error(f"Error searching knowledge base: {str(e)}")
        return []

def clean_query(query: str) -> str:
    """
    Clean a search query.
    
    Args:
        query: Query to clean
        
    Returns:
        Cleaned query
    """
    if not query:
        return ""
    
    # Convert to string if needed
    query = str(query)
    
    # Remove excessive whitespace
    query = re.sub(r'\s+', ' ', query)
    
    # Remove special characters that might cause issues
    query = re.sub(r'[^\w\s\-\.,;:!?]', '', query)
    
    # Trim whitespace
    query = query.strip()
    
    return query

def get_document_by_id(
    document_id: str,
    kb: KnowledgeBase
) -> Optional[Dict[str, Any]]:
    """
    Get a document by its ID.
    
    Args:
        document_id: Document ID
        kb: KnowledgeBase instance
        
    Returns:
        Document data or None if not found
    """
    try:
        return kb.get_document(document_id)
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {str(e)}")
        return None

def format_result_for_display(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a search result for display.
    
    Args:
        result: Search result
        
    Returns:
        Formatted result
    """
    # Clone result to avoid modifying the original
    formatted = result.copy()
    
    # Format score as percentage
    if "score" in formatted:
        formatted["score_pct"] = f"{formatted['score'] * 100:.1f}%"
    
    # Truncate long text fields
    if "text" in formatted and len(formatted["text"]) > 500:
        formatted["text_preview"] = formatted["text"][:500] + "..."
    else:
        formatted["text_preview"] = formatted.get("text", "")
    
    # Ensure metadata is a dictionary
    if "metadata" not in formatted or not formatted["metadata"]:
        formatted["metadata"] = {}
    
    return formatted
