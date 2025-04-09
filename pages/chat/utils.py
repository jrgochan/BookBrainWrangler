"""
Utility functions for the Chat with AI feature.
"""

import logging
import streamlit as st
from typing import Optional, Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

def get_current_model() -> str:
    """
    Get the current model name with fallback.
    
    Returns:
        The current model name from session state or default
    """
    try:
        if isinstance(st.session_state.ollama_settings, dict):
            return st.session_state.ollama_settings.get('model', 'llama2')
        return 'llama2'
    except Exception as e:
        logger.warning(f"Error retrieving current model: {str(e)}")
        return 'llama2'
        
def retrieve_context(
    knowledge_base: Any, 
    query: str, 
    context_strategy: str, 
    num_results: int
) -> Optional[str]:
    """
    Retrieve relevant context from knowledge base based on strategy.
    
    Args:
        knowledge_base: The knowledge base instance
        query: The user's query
        context_strategy: The context strategy to use
        num_results: Number of context results to retrieve
        
    Returns:
        Retrieved context as a string or None if no context was retrieved
    """
    from pages.chat.constants import KNOWLEDGE_SOURCES
    
    context = None
    if context_strategy in [KNOWLEDGE_SOURCES["book_knowledge"], KNOWLEDGE_SOURCES["combined"]]:
        with st.spinner("Retrieving relevant information from your library..."):
            try:
                logger.debug("Retrieving context from knowledge base")
                context = knowledge_base.retrieve_relevant_context(query)
                logger.debug(f"Retrieved context of length: {len(context) if context else 0}")
            except AttributeError as e:
                logger.warning(f"AttributeError when retrieving context: {str(e)}")
                # Fall back to search_engine if the method doesn't exist
                if hasattr(knowledge_base, 'search_engine') and hasattr(knowledge_base.search_engine, 'retrieve_relevant_context'):
                    context = knowledge_base.search_engine.retrieve_relevant_context(
                        query=query,
                        num_results=num_results
                    )
            except Exception as e:
                logger.error(f"Error retrieving context: {str(e)}")
            
            # Save the current context for display if enabled
            st.session_state.current_context = context
            
    return context

def initialize_session_state() -> None:
    """
    Initialize all required session state variables for chat.
    """
    from pages.chat.constants import DEFAULT_SYSTEM_PROMPT, DEFAULT_CHAT_CONFIG
    
    # Core chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Chat configuration
    if 'chat_config' not in st.session_state:
        st.session_state.chat_config = DEFAULT_CHAT_CONFIG
    
    # Custom instructions/system prompt
    if 'system_prompt' not in st.session_state:
        st.session_state.system_prompt = DEFAULT_SYSTEM_PROMPT
    
    # Current context
    if 'current_context' not in st.session_state:
        st.session_state.current_context = None
    
    # Query stats for analytics
    if 'query_stats' not in st.session_state:
        st.session_state.query_stats = []