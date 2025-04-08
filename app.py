"""
Book Knowledge AI - Main Application
A Streamlit-powered book management and knowledge extraction application 
that transforms documents into an interactive, AI-enhanced knowledge base.
"""

import os
import streamlit as st
import time
from book_manager import BookManager
from document_processor import DocumentProcessor
from knowledge_base import KnowledgeBase
from ollama_client import OllamaClient

# Page imports
from pages.book_management import render_book_management_page
from pages.knowledge_base import render_knowledge_base_page
from pages.knowledge_base_explorer import render_knowledge_base_explorer_page
from pages.word_cloud_generator import render_word_cloud_generator_page

# Configure the Streamlit page
st.set_page_config(
    page_title="Book Knowledge AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

def initialize_components():
    """Initialize all major application components."""
    # Create instances of all major components
    book_manager = BookManager()
    document_processor = DocumentProcessor()
    knowledge_base = KnowledgeBase()
    ollama_client = OllamaClient()
    
    return book_manager, document_processor, knowledge_base, ollama_client

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    # App mode state
    if 'app_mode' not in st.session_state:
        st.session_state.app_mode = "Book Management"
    
    # Thumbnail cache
    if 'thumbnail_cache' not in st.session_state:
        st.session_state.thumbnail_cache = {}
    
    # OCR settings
    if 'ocr_settings' not in st.session_state:
        st.session_state.ocr_settings = {
            'show_current_image': True,
            'show_extracted_text': True,
            'confidence_threshold': 70.0,  # percentage
            'display_interval': 5,  # show every 5th page
        }
    
    # Ollama settings
    if 'ollama_settings' not in st.session_state:
        st.session_state.ollama_settings = {
            'model': 'llama2',
            'server_url': 'http://localhost:11434',
            'temperature': 0.7,
            'context_window': 4096,
        }

def render_sidebar(app_modes):
    """Render the sidebar for application navigation."""
    with st.sidebar:
        st.title("📚 Book Knowledge AI")
        
        # Navigation
        st.subheader("Navigation")
        for mode in app_modes:
            if st.button(mode, key=f"nav_{mode}", use_container_width=True, 
                        help=f"Go to {mode} page",
                        type="primary" if st.session_state.app_mode == mode else "secondary"):
                st.session_state.app_mode = mode
                st.rerun()
        
        # Display app information
        st.sidebar.divider()
        st.sidebar.info("""
        ### About
        Book Knowledge AI transforms your documents into an interactive, searchable knowledge base.
        
        Upload books, documents, and research papers to extract knowledge and chat with your documents using AI.
        """)
        
        # Version information
        st.sidebar.caption("v1.0.0 | Built with Streamlit")

def main():
    """Main application entry point."""
    # Initialize application state
    initialize_session_state()
    
    # Initialize components
    book_manager, document_processor, knowledge_base, ollama_client = initialize_components()
    
    # Define application modes/pages
    app_modes = [
        "Book Management",
        "Knowledge Base",
        "Knowledge Base Explorer",
        "Word Cloud Generator",
    ]
    
    # Render sidebar navigation
    render_sidebar(app_modes)
    
    # Render the selected page
    if st.session_state.app_mode == "Book Management":
        render_book_management_page(book_manager, document_processor, knowledge_base)
    
    elif st.session_state.app_mode == "Knowledge Base":
        render_knowledge_base_page(book_manager, knowledge_base)
    
    elif st.session_state.app_mode == "Knowledge Base Explorer":
        render_knowledge_base_explorer_page(knowledge_base)
    
    elif st.session_state.app_mode == "Word Cloud Generator":
        render_word_cloud_generator_page(book_manager)

if __name__ == "__main__":
    main()