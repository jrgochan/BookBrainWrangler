"""
Book Knowledge AI - Taipy Application
A Taipy-powered book management and knowledge extraction application 
that transforms documents into an interactive, AI-enhanced knowledge base.
"""

import os
import time
from datetime import datetime
import taipy as tp
from taipy.gui import Gui, navigate, notify

from utils.logger import get_logger
from document_processing import DocumentProcessor
from knowledge_base import KnowledgeBase
from book_manager import BookManager

# Import page modules
from pages.taipy.layout import get_layout_template
from pages.taipy.home import get_template as get_home_template
from pages.taipy.book_management import get_template as get_book_management_template
from pages.taipy.knowledge_base import get_template as get_knowledge_base_template
from pages.taipy.chat import get_template as get_chat_template
from pages.taipy.archive_search import get_template as get_archive_search_template
from pages.taipy.settings import get_template as get_settings_template

# Import state initialization functions
from pages.taipy.book_management import init_state as init_book_management_state
from pages.taipy.knowledge_base import init_state as init_knowledge_base_state
from pages.taipy.chat import init_state as init_chat_state
from pages.taipy.archive_search import init_state as init_archive_search_state
from pages.taipy.settings import init_state as init_settings_state

# Initialize logger
logger = get_logger(__name__)

class BookKnowledgeApp:
    """Main application class for Book Knowledge AI."""
    
    def __init__(self):
        """Initialize the application."""
        logger.info("Initializing Book Knowledge AI application")
        
        # Initialize core components
        self.document_processor = DocumentProcessor()
        self.knowledge_base = KnowledgeBase()
        self.book_manager = BookManager()
        
        # Initialize AI client
        from ai import get_default_client
        self.ai_client = get_default_client()
        
        # Create layout template
        self.layout_template = get_layout_template()
        
        # Get page templates
        self.page_templates = {
            "home": get_home_template(),
            "book_management": get_book_management_template(),
            "knowledge_base": get_knowledge_base_template(),
            "chat": get_chat_template(),
            "archive_search": get_archive_search_template(),
            "settings": get_settings_template()
        }
        
        # Create the Gui object with the main template
        self.gui = self._create_gui()
        
        # Register callbacks
        self._register_callbacks()
    
    def _create_gui(self):
        """Create the Taipy Gui object."""
        # Get the combined template
        template = self._get_combined_template()
        
        # Create the Gui object
        gui = Gui(template)
        
        # Configure Gui settings
        gui.title = "Book Knowledge AI"
        gui.favicon = "📚"
        
        # Add pages
        gui.add_page("home", title="Home")
        gui.add_page("book_management", title="Book Management")
        gui.add_page("knowledge_base", title="Knowledge Base")
        gui.add_page("chat", title="Chat with AI")
        gui.add_page("archive_search", title="Archive Search")
        gui.add_page("settings", title="Settings")
        
        return gui
    
    def _get_combined_template(self):
        """Get the combined template with layout and content."""
        # Define a template function that selects the appropriate page content
        # based on the current_page state variable
        def get_content(state):
            page = getattr(state, "current_page", "home")
            return self.page_templates.get(page, self.page_templates["home"])
        
        # Return a template that includes the layout and dynamic content
        return self.layout_template.replace("{current_page_content}", "{content}")
    
    def _register_callbacks(self):
        """Register callback functions for the Gui."""
        # Global navigation callback
        self.gui.add_callback("on_navigate", self.on_navigate)
        
        # Book management callbacks
        self.gui.add_callback("on_process_book", self.on_process_book)
        self.gui.add_callback("on_search_books", self.on_search_books)
        
        # Knowledge base callbacks
        self.gui.add_callback("on_search_knowledge_base", self.on_search_knowledge_base)
        self.gui.add_callback("on_filter_documents", self.on_filter_documents)
        
        # Chat callbacks
        self.gui.add_callback("on_send_message", self.on_send_message)
        self.gui.add_callback("on_new_chat", self.on_new_chat)
        
        # Archive search callbacks
        self.gui.add_callback("on_search_archive", self.on_search_archive)
        self.gui.add_callback("on_download_book", self.on_download_book)
        self.gui.add_callback("on_download_all", self.on_download_all)
        self.gui.add_callback("on_clear_logs", self.on_clear_logs)
        
        # Settings callbacks
        self.gui.add_callback("on_save_ai_settings", self.on_save_ai_settings)
        self.gui.add_callback("on_save_kb_settings", self.on_save_kb_settings)
        self.gui.add_callback("on_save_doc_settings", self.on_save_doc_settings)
        self.gui.add_callback("on_save_ui_settings", self.on_save_ui_settings)
        self.gui.add_callback("on_save_advanced_settings", self.on_save_advanced_settings)
        self.gui.add_callback("on_rebuild_index", self.on_rebuild_index)
        self.gui.add_callback("on_export_kb", self.on_export_kb)
        self.gui.add_callback("on_clear_logs", self.on_clear_logs)
        self.gui.add_callback("on_reset_settings", self.on_reset_settings)
        self.gui.add_callback("on_delete_all_data", self.on_delete_all_data)
    
    def on_init(self, state):
        """Initialize the application state when the GUI starts."""
        logger.info("Initializing application state")
        
        # Set initial current page
        state.current_page = "home"
        
        # Add core components to state
        state.document_processor = self.document_processor
        state.knowledge_base = self.knowledge_base
        state.book_manager = self.book_manager
        state.ai_client = self.ai_client
        
        # Function to get dynamic page content
        state.content = None
        
        # Initialize page-specific state
        init_book_management_state(state)
        init_knowledge_base_state(state)
        init_chat_state(state)
        init_archive_search_state(state)
        init_settings_state(state)
    
    # Navigation callback
    def on_navigate(self, state, page):
        """Handle navigation between pages."""
        logger.info(f"Navigating to page: {page}")
        state.current_page = page
        navigate(state, page)
    
    # Book management callbacks
    def on_process_book(self, state):
        """Process a book upload."""
        from pages.taipy.book_management import on_process_book
        on_process_book(state)
    
    def on_search_books(self, state):
        """Search for books."""
        from pages.taipy.book_management import on_search_books
        on_search_books(state)
    
    # Knowledge base callbacks
    def on_search_knowledge_base(self, state):
        """Search the knowledge base."""
        from pages.taipy.knowledge_base import on_search_knowledge_base
        on_search_knowledge_base(state)
    
    def on_filter_documents(self, state):
        """Filter documents in the knowledge base."""
        from pages.taipy.knowledge_base import on_filter_documents
        on_filter_documents(state)
    
    # Chat callbacks
    def on_send_message(self, state):
        """Send a message in the chat."""
        from pages.taipy.chat import on_send_message
        on_send_message(state)
    
    def on_new_chat(self, state):
        """Start a new chat session."""
        from pages.taipy.chat import on_new_chat
        on_new_chat(state)
    
    # Archive search callbacks
    def on_search_archive(self, state):
        """Search the Internet Archive."""
        from pages.taipy.archive_search import on_search_archive
        on_search_archive(state)
    
    def on_download_book(self, state, book_id):
        """Download a book from the Internet Archive."""
        from pages.taipy.archive_search import on_download_book
        on_download_book(state, book_id)
    
    def on_download_all(self, state):
        """Download all books from search results."""
        from pages.taipy.archive_search import on_download_all
        on_download_all(state)
    
    def on_clear_logs(self, state):
        """Clear logs."""
        from pages.taipy.archive_search import on_clear_logs
        on_clear_logs(state)
    
    # Settings callbacks
    def on_save_ai_settings(self, state):
        """Save AI settings."""
        from pages.taipy.settings import on_save_ai_settings
        on_save_ai_settings(state)
    
    def on_save_kb_settings(self, state):
        """Save knowledge base settings."""
        from pages.taipy.settings import on_save_kb_settings
        on_save_kb_settings(state)
    
    def on_save_doc_settings(self, state):
        """Save document processing settings."""
        from pages.taipy.settings import on_save_doc_settings
        on_save_doc_settings(state)
    
    def on_save_ui_settings(self, state):
        """Save UI settings."""
        from pages.taipy.settings import on_save_ui_settings
        on_save_ui_settings(state)
    
    def on_save_advanced_settings(self, state):
        """Save advanced settings."""
        from pages.taipy.settings import on_save_advanced_settings
        on_save_advanced_settings(state)
    
    def on_rebuild_index(self, state):
        """Rebuild the knowledge base index."""
        from pages.taipy.settings import on_rebuild_index
        on_rebuild_index(state)
    
    def on_export_kb(self, state):
        """Export the knowledge base."""
        from pages.taipy.settings import on_export_kb
        on_export_kb(state)
    
    def on_reset_settings(self, state):
        """Reset settings to defaults."""
        from pages.taipy.settings import on_reset_settings
        on_reset_settings(state)
    
    def on_delete_all_data(self, state):
        """Delete all application data."""
        from pages.taipy.settings import on_delete_all_data
        on_delete_all_data(state)
    
    def run(self):
        """Run the application."""
        logger.info("Starting Book Knowledge AI application")
        self.gui.run(debug=True, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    # Create and run the application
    app = BookKnowledgeApp()
    app.run()