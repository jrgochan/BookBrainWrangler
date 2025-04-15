"""
Chat with AI module - Main entry point.
This module provides the main entry point for the Chat with AI feature.
"""

import streamlit as st
import logging
from typing import Any

from pages.chat.interface import ChatInterface
from pages.chat.ui_components import render_action_buttons

logger = logging.getLogger(__name__)

def render_chat_with_ai_page(ollama_client: Any, knowledge_base: Any) -> None:
    """
    Render the Chat with AI page.
    
    Args:
        ollama_client: The OllamaClient instance
        knowledge_base: The KnowledgeBase instance
    """
    # Set up page layout with proper structure
    st.title("Chat with AI about Your Books")
    
    # Initialize chat interface
    chat_interface = ChatInterface(ollama_client, knowledge_base)
    
    # Check connection to Ollama server
    if not chat_interface.check_connection():
        return
    
    # Render sidebar and get context strategy
    context_strategy, indexed_book_ids = chat_interface.render_sidebar()
    
    # Check if there are indexed books
    if not indexed_book_ids:
        st.warning("""
            ⚠️ **No books added to the knowledge base**
            
            Please add books to your knowledge base in the Knowledge Base tab before chatting.
        """)
        return
    
    # Create a proper layout with main area for chat and a fixed bottom section for input
    # This helps ensure the chat input is always visible at the bottom
    
    # 1. Main container for chat history
    chat_area = st.container()
    
    # 2. Create a container for action buttons and chat input
    # Using columns to separate the elements
    input_area = st.container()
    
    # First render the chat history in the main area
    with chat_area:
        chat_interface.render_chat_history()
    
    # Then render the input area with action buttons and chat input
    with input_area:
        # Chat action buttons in a separate row above the input
        render_action_buttons(
            on_clear=chat_interface.clear_conversation,
            on_export=chat_interface.export_conversation
        )
        
        # Add a small separator
        st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
        
        # Input for new message - always at the bottom
        from pages.chat.utils import get_current_model
        current_model = get_current_model()
        user_query = st.chat_input(f"Ask {current_model} about your books...")
        
        if user_query:
            chat_interface.process_user_query(user_query, context_strategy)
            # Force a rerun to update the UI immediately
            st.rerun()