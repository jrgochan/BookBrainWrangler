"""
Book Knowledge AI - Main Application
A Streamlit-powered book management and knowledge extraction application 
that transforms documents into an interactive, AI-enhanced knowledge base.
"""

import os
import streamlit as st
import time
import platform
import sys
from loguru import logger
from utils.logging_config import configure_logger

# Configure logger
logger = configure_logger()
logger.info(f"Starting Book Knowledge AI application - Python {sys.version} on {platform.system()} {platform.release()}")

from book_manager import BookManager
from document_processor import DocumentProcessor
from knowledge_base import KnowledgeBase
from ollama_client import OllamaClient

# Page imports
from pages.book_management import render_book_management_page
from pages.knowledge_base import render_knowledge_base_page
from pages.knowledge_base_explorer import render_knowledge_base_explorer_page
from pages.word_cloud_generator import render_word_cloud_generator_page
from pages.chat_with_ai import render_chat_with_ai_page
from pages.settings import render_settings_page

# Configure the Streamlit page
st.set_page_config(
    page_title="Book Knowledge AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Hide the default Streamlit nav menu above the title
hide_streamlit_nav = """
<style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Adjust spacing to compensate for hidden header */
    .main .block-container {padding-top: 2rem;}
</style>
"""
st.markdown(hide_streamlit_nav, unsafe_allow_html=True)

def initialize_components():
    """Initialize all major application components."""
    logger.info("Initializing application components")
    
    try:
        # Create instances of all major components
        logger.debug("Initializing BookManager")
        book_manager = BookManager()
        
        logger.debug("Initializing DocumentProcessor")
        document_processor = DocumentProcessor()
        
        logger.debug("Initializing KnowledgeBase")
        knowledge_base = KnowledgeBase()
        
        logger.debug("Initializing OllamaClient")
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
        st.session_state.app_mode = "Book Management"
        initialized_items.append("app_mode")
    
    # Thumbnail cache
    if 'thumbnail_cache' not in st.session_state:
        st.session_state.thumbnail_cache = {}
        initialized_items.append("thumbnail_cache")
    
    # OCR settings
    if 'ocr_settings' not in st.session_state:
        st.session_state.ocr_settings = {
            'show_current_image': True,
            'show_extracted_text': True,
            'confidence_threshold': 70.0,  # percentage
            'display_interval': 5,  # show every 5th page
        }
        initialized_items.append("ocr_settings")
    
    # Ollama settings
    if 'ollama_settings' not in st.session_state:
        st.session_state.ollama_settings = {
            'model': 'llama2',
            'server_url': 'http://localhost:11434',
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
        st.title("📚 Book Knowledge AI")
        
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

def main():
    """Main application entry point."""
    start_time = time.time()
    logger.info("Starting main application loop")
    
    try:
        # Initialize application state
        initialize_session_state()
        
        # Initialize components
        book_manager, document_processor, knowledge_base, ollama_client = initialize_components()
        
        # Define application modes/pages
        app_modes = [
            "Book Management",
            "Knowledge Base",
            "Chat with AI",
            "Knowledge Base Explorer",
            "Word Cloud Generator",
            "Settings",
        ]
        
        # Render sidebar navigation
        render_sidebar(app_modes)
        
        # Log current mode
        current_mode = st.session_state.app_mode
        logger.info(f"Rendering page: {current_mode}")
        
        # Render the selected page
        try:
            if current_mode == "Book Management":
                render_book_management_page(book_manager, document_processor, knowledge_base)
            
            elif current_mode == "Knowledge Base":
                render_knowledge_base_page(book_manager, knowledge_base)
            
            elif current_mode == "Chat with AI":
                render_chat_with_ai_page(ollama_client, knowledge_base)
            
            elif current_mode == "Knowledge Base Explorer":
                render_knowledge_base_explorer_page(knowledge_base)
            
            elif current_mode == "Word Cloud Generator":
                render_word_cloud_generator_page(book_manager)
                
            elif current_mode == "Settings":
                render_settings_page(ollama_client)
                
            else:
                logger.error(f"Unknown app mode: {current_mode}")
                st.error(f"Unknown application mode: {current_mode}")
                
            # Log page render time
            render_time = time.time() - start_time
            logger.debug(f"Page {current_mode} rendered in {render_time:.2f} seconds")
                
        except Exception as e:
            logger.exception(f"Error rendering page {current_mode}: {str(e)}")
            st.error(f"An error occurred while rendering the page: {str(e)}")
            
    except Exception as e:
        logger.exception(f"Critical application error: {str(e)}")
        st.error("A critical error occurred in the application. Please check the logs for details.")

if __name__ == "__main__":
    main()