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
