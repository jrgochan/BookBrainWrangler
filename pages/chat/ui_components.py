"""
UI components for the Chat with AI feature.
"""

import streamlit as st
import logging
from typing import Any, Tuple, List, Dict, Optional

logger = logging.getLogger(__name__)

def render_chat_history(chat_history: List[Dict[str, str]], show_context: bool, current_context: Optional[str] = None) -> None:
    """
    Render the chat history with message bubbles.
    
    Args:
        chat_history: List of chat message dictionaries
        show_context: Whether to show context
        current_context: Current context to display if show_context is True
    """
    from pages.chat.constants import AVATARS
    
    # Main chat display area
    chat_container = st.container(height=400, border=False)
    
    with chat_container:
        # Display chat history with avatars
        for message in chat_history:
            with st.chat_message(message["role"], avatar=AVATARS.get(message["role"], "💬")):
                if message["role"] == "system":
                    st.caption("System Instruction")
                st.markdown(message["content"])
    
    # Display current context if enabled
    if show_context and current_context:
        with st.expander("📚 Current Context", expanded=False):
            st.markdown(current_context)

def render_connection_error(host: str) -> None:
    """
    Display error message when Ollama connection fails.
    
    Args:
        host: The Ollama server host URL
    """
    st.error(f"""
        🚫 **Cannot connect to Ollama server**
        
        Ensure Ollama is running and properly configured in Settings.
        Current host: {host}
    """)
    
    st.info("""
        ### How to set up Ollama:
        1. Install Ollama from [ollama.ai](https://ollama.ai)
        2. Start the Ollama server with `ollama serve`
        3. Pull a model with `ollama pull llama2` or another model
        4. Configure the connection in the Settings tab
    """)

def render_sidebar(
    ollama_client: Any, 
    knowledge_base: Any
) -> Tuple[str, List[int]]:
    """
    Render the sidebar with model info and chat controls.
    
    Args:
        ollama_client: The OllamaClient instance
        knowledge_base: The KnowledgeBase instance
        
    Returns:
        Tuple of (selected context strategy, list of indexed book IDs)
    """
    from pages.chat.constants import KNOWLEDGE_SOURCES
    from pages.chat.utils import get_current_model
    
    st.sidebar.header("AI Configuration")
    
    # Safely display model information
    current_model = get_current_model()
    try:
        # Get model details
        model_info = ollama_client.get_model_details(current_model)
        
        if model_info:
            st.sidebar.success(f"✓ Using model: **{current_model}**")
            if isinstance(model_info, dict) and "parameters" in model_info:
                st.sidebar.caption(f"Model size: {model_info['parameters']/1_000_000_000:.1f}B parameters")
        else:
            st.sidebar.warning(f"⚠️ Model '{current_model}' not found on the server")
            available_models = ollama_client.list_models()
            if available_models:
                # Extract model names safely
                try:
                    model_names = [m.get('name', 'unknown') if isinstance(m, dict) else 'unknown' 
                                  for m in available_models]
                    st.sidebar.caption(f"Available models: {', '.join(model_names)}")
                except Exception as e:
                    logger.error(f"Error extracting model names: {str(e)}")
                    st.sidebar.caption("Error retrieving model information")
    except Exception as e:
        # Handle any unexpected errors in the model display section
        logger.error(f"Error displaying model information: {str(e)}")
        st.sidebar.error(f"Error displaying model information: {str(e)}")
    
    # Chat controls
    st.sidebar.header("Chat Controls")
    
    # Knowledge base integration toggle
    context_strategy = st.sidebar.radio(
        "Knowledge Source",
        list(KNOWLEDGE_SOURCES.values()),
        help=("Book Knowledge: Use your book library as primary context. "
              "Model Knowledge: Use only the model's built-in knowledge. "
              "Combined: Use both sources together.")
    )
    
    # Display indexed books count
    indexed_book_ids = knowledge_base.get_indexed_book_ids()
    if indexed_book_ids:
        st.sidebar.success(f"✓ {len(indexed_book_ids)} books in knowledge base")
    else:
        st.sidebar.warning("No books in knowledge base")
        if context_strategy != KNOWLEDGE_SOURCES["model_knowledge"]:
            st.sidebar.info("Switching to 'Model Knowledge' mode since no books are available")
            context_strategy = KNOWLEDGE_SOURCES["model_knowledge"]
            
    return context_strategy, indexed_book_ids

def render_action_buttons(on_clear: callable, on_export: callable) -> None:
    """
    Render chat action buttons.
    
    Args:
        on_clear: Callback for clear conversation button
        on_export: Callback for export conversation button
    """
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear conversation", use_container_width=True) and st.session_state.chat_history:
            on_clear()
            st.rerun()
    
    with col2:
        if st.button("Save conversation", use_container_width=True) and st.session_state.chat_history:
            on_export()