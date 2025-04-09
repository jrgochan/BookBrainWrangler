"""
Book Knowledge AI - Main Application
A Streamlit-powered book management and knowledge extraction application 
that transforms documents into an interactive, AI-enhanced knowledge base.
"""

import streamlit as st
import os
import time
import platform
import sys
from loguru import logger
from utils.logging_config import configure_logger

# Apply Streamlit patches before importing streamlit
from utils.streamlit_patch import apply_patches
apply_patches()

# Configure logger
logger = configure_logger()
logger.info(f"Starting Book Knowledge AI application - Python {sys.version} on {platform.system()} {platform.release()}")

# Import module classes
from book_manager import BookManager
from document_processing import DocumentProcessor
from knowledge_base import KnowledgeBase
from ollama_client import OllamaClient

# Import pages
from pages.book_management import render_book_management_page
from pages.knowledge_base import render_knowledge_base_page
from pages.chat_with_ai import render_chat_with_ai_page
from pages.knowledge_base_explorer import render_knowledge_base_explorer_page
from pages.word_cloud_generator import render_word_cloud_generator_page
from pages.document_heatmap import render as render_document_heatmap_page
from pages.settings import render_settings_page

# Import UI helpers
from utils.ui_helpers import set_page_config

# Import configuration
from config.settings import (
    APP_TITLE, 
    APP_ICON, 
    APP_LAYOUT, 
    INITIAL_SIDEBAR_STATE,
    APP_MODES
)

# Initialize the components
@st.cache_resource
def initialize_components():
    """Initialize all major application components."""
    logger.info("Initializing application components")
    
    try:
        # Create instances of all major components
        logger.debug("Initializing BookManager")
        book_manager = BookManager()
        
        logger.debug("Initializing DocumentProcessor")
        # Get OCR settings from session state if available
        if 'ocr_settings' in st.session_state and isinstance(st.session_state.ocr_settings, dict):
            ocr_engine = st.session_state.ocr_settings.get('ocr_engine', 'pytesseract')
            logger.debug(f"Initializing DocumentProcessor with OCR engine: {ocr_engine}")
            document_processor = DocumentProcessor(
                ocr_engine=ocr_engine,
                ocr_settings=st.session_state.ocr_settings
            )
        else:
            logger.debug("Initializing DocumentProcessor with default settings")
            document_processor = DocumentProcessor()
        
        logger.debug("Initializing KnowledgeBase")
        knowledge_base = KnowledgeBase()
        
        # Initialize Ollama client with settings from session state if available
        if 'ollama_settings' in st.session_state and isinstance(st.session_state.ollama_settings, dict):
            server_url = st.session_state.ollama_settings.get('server_url', 'http://localhost:11434')
            model = st.session_state.ollama_settings.get('model', 'llama2')
            logger.debug(f"Initializing OllamaClient with server_url={server_url}, model={model}")
            ollama_client = OllamaClient(server_url=server_url, model=model)
        else:
            logger.debug("Initializing OllamaClient with default settings")
            ollama_client = OllamaClient()
        
        logger.success("All components initialized successfully")
        return book_manager, document_processor, knowledge_base, ollama_client
    except Exception as e:
        logger.error(f"Failed to initialize components: {str(e)}")
        raise

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    logger.info("Initializing session state")
    
    # Track what we're initializing
    initialized_items = []
    
    # App mode state
    if 'app_mode' not in st.session_state:
        st.session_state.app_mode = APP_MODES[0]
        initialized_items.append("app_mode")
    
    # Thumbnail cache
    if 'thumbnail_cache' not in st.session_state:
        st.session_state.thumbnail_cache = {}
        initialized_items.append("thumbnail_cache")
    
    # OCR settings
    if 'ocr_settings' not in st.session_state:
        # Detect the operating system
        import platform
        system = platform.system().lower()
        
        # Set a default Tesseract path based on the platform
        default_tesseract_path = ""
        if system == 'windows':
            default_tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        elif system == 'linux':
            default_tesseract_path = '/usr/bin/tesseract'
        elif system == 'darwin':  # macOS
            default_tesseract_path = '/usr/local/bin/tesseract'
            
        # Initialize OCR settings
        st.session_state.ocr_settings = {
            'show_current_image': True,
            'show_extracted_text': True,
            'confidence_threshold': 70.0,  # percentage
            'display_interval': 5,  # show every 5th page
            'ocr_engine': 'pytesseract',  # Default OCR engine
            'languages': ['en'],  # Default language for EasyOCR
            'tesseract_path': default_tesseract_path  # Platform-specific default path
        }
        initialized_items.append("ocr_settings")
    
    # Ollama settings
    if 'ollama_settings' not in st.session_state:
        st.session_state.ollama_settings = {
            'model': os.environ.get("OLLAMA_MODEL", "llama2"),
            'server_url': os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
            'temperature': 0.7,
            'context_window': 4096,
        }
        initialized_items.append("ollama_settings")
        
    if initialized_items:
        logger.debug(f"Initialized session state variables: {', '.join(initialized_items)}")
    else:
        logger.debug("Session state already initialized")

def render_sidebar(app_modes):
    """Render the sidebar for application navigation."""
    logger.debug("Rendering sidebar navigation")
    
    with st.sidebar:
        st.title(APP_TITLE)
        
        # Navigation
        st.subheader("Navigation")
        for mode in app_modes:
            if st.button(mode, key=f"nav_{mode}", use_container_width=True, 
                        help=f"Go to {mode} page",
                        type="primary" if st.session_state.app_mode == mode else "secondary"):
                previous_mode = st.session_state.app_mode
                st.session_state.app_mode = mode
                logger.info(f"Navigation: Changed from '{previous_mode}' to '{mode}' mode")
                st.rerun()
        
        # Display app information
        st.sidebar.divider()
        st.sidebar.info("""
        ### About
        Book Knowledge AI transforms your documents into an interactive, searchable knowledge base.
        
        Upload books, documents, and research papers to extract knowledge and chat with your documents using AI.
        """)
        
        # Version information
        app_version = "1.0.0"  # This could be stored in a config file or constants module
        st.sidebar.caption(f"v{app_version} | Built with Streamlit")
        logger.debug(f"App version: {app_version}")
    
    return st.session_state.app_mode

def main():
    """Main application entry point."""
    start_time = time.time()
    logger.info("Starting main application loop")
    
    try:
        # Set the page configuration
        set_page_config(APP_TITLE, APP_ICON, APP_LAYOUT, INITIAL_SIDEBAR_STATE)
        
        # Initialize application state
        initialize_session_state()
        
        # Initialize components
        book_manager, document_processor, knowledge_base, ollama_client = initialize_components()
        
        # Render sidebar and get selected mode
        selected_mode = render_sidebar(APP_MODES)
        
        # Log current mode
        logger.info(f"Rendering page: {selected_mode}")
        
        # Render the selected page
        try:
            if selected_mode == "Book Management":
                render_book_management_page(book_manager, document_processor, knowledge_base)
            
            elif selected_mode == "Knowledge Base":
                render_knowledge_base_page(book_manager, knowledge_base)
            
            elif selected_mode == "Chat with AI":
                render_chat_with_ai_page(ollama_client, knowledge_base)
            
            elif selected_mode == "Knowledge Base Explorer":
                render_knowledge_base_explorer_page(knowledge_base)
            
            elif selected_mode == "Word Cloud Generator":
                render_word_cloud_generator_page(book_manager)
                
            elif selected_mode == "Document Heatmap":
                render_document_heatmap_page()
                
            elif selected_mode == "Settings":
                render_settings_page(ollama_client)
                
            else:
                logger.error(f"Unknown app mode: {selected_mode}")
                st.error(f"Unknown application mode: {selected_mode}")
                
            # Log page render time
            render_time = time.time() - start_time
            logger.debug(f"Page {selected_mode} rendered in {render_time:.2f} seconds")
                
        except Exception as e:
            logger.exception(f"Error rendering page {selected_mode}: {str(e)}")
            st.error(f"An error occurred while rendering the page: {str(e)}")
            
    except Exception as e:
        logger.exception(f"Critical application error: {str(e)}")
        st.error("A critical error occurred in the application. Please check the logs for details.")

# Run the application
if __name__ == "__main__":
    main()
