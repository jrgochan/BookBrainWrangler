"""
Book Knowledge AI - Main Application
A Taipy-powered book management and knowledge extraction application 
that transforms documents into an interactive, AI-enhanced knowledge base.
"""

import os
from datetime import datetime
import taipy as tp
from taipy.gui import Gui, navigate, notify
from taipy.config import Config

from utils.logger import get_logger
from document_processing import DocumentProcessor
from knowledge_base import KnowledgeBase
from config.taipy.config import app_config

# Initialize logger
logger = get_logger(__name__)

class BookKnowledgeApp:
    """Main application class for Book Knowledge AI."""
    
    def __init__(self):
        """Initialize the application."""
        # Initialize core components
        self.document_processor = DocumentProcessor()
        self.knowledge_base = KnowledgeBase()
        
        # Initialize AI client
        from ai import get_default_client
        self.ai_client = get_default_client()
        self.chat_ai_client = self.ai_client  # For chat interface
        
        # Initialize state variables
        self.current_page = "home"
        self.theme = "light"
        self.uploaded_files = []
        self.processing_results = {}
        self.search_results = []
        self.selected_document = None
        self.chat_messages = []
        self.search_query = ""
        self.search_category = ""
        
        # Initialize Taipy data nodes
        self._init_data_nodes()
        
    def _init_data_nodes(self):
        """Initialize Taipy data nodes with default values."""
        # Implementation will depend on the taipy Config setup
        pass
    
    def on_init(self, state):
        """Initialize the application state when the GUI starts."""
        # Set initial state values
        state.current_page = "home"
        state.theme = "light"
        state.document_processor = self.document_processor
        state.knowledge_base = self.knowledge_base
        state.ai_client = self.ai_client
        state.chat_ai_client = self.chat_ai_client
        state.chat_messages = []
        state.search_query = ""
        state.search_category = ""
        state.processing_status = ""
        
        # Log initialization
        logger.info("Application state initialized")

    def on_navigate(self, state, page):
        """Handle page navigation."""
        logger.info(f"Navigating to page: {page}")
        state.current_page = page
        navigate(state, page)

# Define page templates
home_page = """
<|container|
# 📚 Book Knowledge AI

Welcome to Book Knowledge AI, your intelligent document management system.

<|layout|columns=1 1 1|gap=30px|
<|card|
## 📄 Book Management
Upload and manage your documents.

<|Navigate to Book Management|button|on_action=on_navigate|page=book_management|>
|>

<|card|
## 🧠 Knowledge Base
Explore your knowledge base.

<|Navigate to Knowledge Base|button|on_action=on_navigate|page=knowledge_base|>
|>

<|card|
## 💬 Chat with AI
Interact with your documents using AI.

<|Navigate to Chat|button|on_action=on_navigate|page=chat|>
|>
|>
|>
"""

# Define the main layout template
main_layout = """
<|part|render=True|class_name=sidebar|
# 📚 Book Knowledge AI

<|Navigate to Home|button|on_action=on_navigate|page=home|>
<|Navigate to Book Management|button|on_action=on_navigate|page=book_management|>
<|Navigate to Knowledge Base|button|on_action=on_navigate|page=knowledge_base|>
<|Navigate to Chat with AI|button|on_action=on_navigate|page=chat|>
<|Navigate to Archive Search|button|on_action=on_navigate|page=archive_search|>
<|Navigate to Settings|button|on_action=on_navigate|page=settings|>
|>

<|part|render={current_page == "home"}|
{home_page}
|>

<|part|render={current_page == "book_management"}|
# Book Management
*Implementation pending*
|>

<|part|render={current_page == "knowledge_base"}|
# Knowledge Base
*Implementation pending*
|>

<|part|render={current_page == "chat"}|
# Chat with AI
*Implementation pending*
|>

<|part|render={current_page == "archive_search"}|
# Archive Search
*Implementation pending*
|>

<|part|render={current_page == "settings"}|
# Settings
*Implementation pending*
|>
"""

# Create application instance
app = BookKnowledgeApp()

# Configure Taipy GUI settings
gui = Gui(main_layout)
gui.title = "Book Knowledge AI"
gui.favicon = "📚"
gui.theme = app_config.get("theme", {})

# Add callbacks
gui.add_page("home", title="Home")
gui.add_page("book_management", title="Book Management")
gui.add_page("knowledge_base", title="Knowledge Base")
gui.add_page("chat", title="Chat with AI")
gui.add_page("archive_search", title="Archive Search")
gui.add_page("settings", title="Settings")

# Map callbacks to the GUI
def on_navigate(state, page):
    """Handle navigation between pages."""
    app.on_navigate(state, page)

# Main application entry point
if __name__ == "__main__":
    # Initialize Taipy Core (if needed)
    # tp.Core().run()
    
    # Start the GUI on the specified port
    gui.run(debug=True, host="0.0.0.0", port=5000)