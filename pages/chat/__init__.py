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
    
    # Render chat history
    chat_interface.render_chat_history()
    
    # Input for new message
    from pages.chat.utils import get_current_model
    current_model = get_current_model()
    user_query = st.chat_input(f"Ask {current_model} about your books...")
    
    if user_query:
        chat_interface.process_user_query(user_query, context_strategy)
    
    # Chat action buttons
    render_action_buttons(
        on_clear=chat_interface.clear_conversation,
        on_export=chat_interface.export_conversation
    )