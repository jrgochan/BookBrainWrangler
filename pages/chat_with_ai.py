"""
Chat with AI page for the application.
This page provides an enhanced interface to chat with AI about book content
with advanced Ollama integration and knowledge base features.
"""

import streamlit as st

def render_chat_with_ai_page(ollama_client, knowledge_base):
    """
    Render the Chat with AI page.
    
    Args:
        ollama_client: The OllamaClient instance
        knowledge_base: The KnowledgeBase instance
    """
    # Call the refactored version
    from pages.chat import render_chat_with_ai_page as render_refactored
    render_refactored(ollama_client, knowledge_base)