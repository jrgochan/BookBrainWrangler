"""
Initializer module for the Taipy application.
Handles initialization of all required components.
"""

import os
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class AppInitializer:
    """Application initializer for Taipy."""
    
    @staticmethod
    def load_css() -> str:
        """
        Load the CSS styles for the application.
        
        Returns:
            CSS styles as a string
        """
        try:
            css_path = os.path.join(os.path.dirname(__file__), "styles.css")
            with open(css_path, "r") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load CSS: {str(e)}")
            return ""
    
    @staticmethod
    def init_core_components() -> Dict[str, Any]:
        """
        Initialize core application components.
        
        Returns:
            Dictionary with initialized components
        """
        logger.info("Initializing core components")
        
        from document_processing import DocumentProcessor
        from knowledge_base import KnowledgeBase
        from book_manager import BookManager
        
        try:
            document_processor = DocumentProcessor()
            knowledge_base = KnowledgeBase()
            book_manager = BookManager()
            
            # Initialize AI client
            from ai import get_default_client
            ai_client = get_default_client()
            
            return {
                "document_processor": document_processor,
                "knowledge_base": knowledge_base,
                "book_manager": book_manager,
                "ai_client": ai_client
            }
        except Exception as e:
            logger.error(f"Failed to initialize core components: {str(e)}")
            raise
    
    @staticmethod
    def init_state(state) -> None:
        """
        Initialize the application state.
        
        Args:
            state: The application state object
        """
        logger.info("Initializing application state")
        
        try:
            # Initialize page-specific state
            from pages.taipy.book_management import init_state as init_book_management_state
            from pages.taipy.knowledge_base import init_state as init_knowledge_base_state
            from pages.taipy.chat import init_state as init_chat_state
            from pages.taipy.archive_search import init_state as init_archive_search_state
            from pages.taipy.settings import init_state as init_settings_state
            
            # Set initial current page
            state.current_page = "home"
            
            # Initialize components
            components = AppInitializer.init_core_components()
            for name, component in components.items():
                setattr(state, name, component)
            
            # Function to get dynamic page content
            state.content = None
            
            # Initialize page-specific state
            init_book_management_state(state)
            init_knowledge_base_state(state)
            init_chat_state(state)
            init_archive_search_state(state)
            init_settings_state(state)
            
            logger.info("Application state initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize application state: {str(e)}")
            raise
    
    @staticmethod
    def init_data_nodes() -> Dict[str, Any]:
        """
        Initialize data nodes for the application.
        
        Returns:
            Dictionary with initialized data nodes
        """
        logger.info("Initializing data nodes")
        
        try:
            # Import Taipy data node configuration
            from config.taipy.config import config
            
            # Get data nodes
            books_data = config.data_nodes["books_data"]
            knowledge_base_data = config.data_nodes["knowledge_base_data"]
            chat_history = config.data_nodes["chat_history"]
            
            return {
                "books_data": books_data,
                "knowledge_base_data": knowledge_base_data,
                "chat_history": chat_history
            }
        except Exception as e:
            logger.error(f"Failed to initialize data nodes: {str(e)}")
            raise
    
    @staticmethod
    def init_gui_settings() -> Dict[str, Any]:
        """
        Initialize GUI settings for the application.
        
        Returns:
            Dictionary with GUI settings
        """
        logger.info("Initializing GUI settings")
        
        try:
            return {
                "title": "Book Knowledge AI",
                "favicon": "📚",
                "dark_mode": False,
                "theme": "light",
                "debug": True,
                "host": "0.0.0.0",
                "port": 5000
            }
        except Exception as e:
            logger.error(f"Failed to initialize GUI settings: {str(e)}")
            raise