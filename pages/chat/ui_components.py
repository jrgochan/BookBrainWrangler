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
    
    # Add a small padding at the top if needed
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    
    # Use a larger height for better chat experience
    # Set up a layout with two containers:
    # 1. Main container for all messages
    # 2. A scrollable inner container for the messages
    chat_container = st.container(height=600, border=False)
    
    # Calculate available height for proper scroll positioning
    available_height = 600  # Should match the container height
    
    with chat_container:
        # Create a flexible container to hold all messages
        # This will automatically expand as messages are added
        for message in chat_history:
            with st.chat_message(message["role"], avatar=AVATARS.get(message["role"], "💬")):
                if message["role"] == "system":
                    st.caption("System Instruction")
                st.markdown(message["content"])
        
        # Add automatic scroll to bottom with custom HTML/JS
        if chat_history:
            # Add an invisible element at the bottom
            st.markdown("""
            <div id="chat-bottom-anchor"></div>
            <script>
                // Function to scroll to the bottom of the chat
                function scrollToBottom() {
                    const bottomAnchor = document.getElementById('chat-bottom-anchor');
                    if (bottomAnchor) {
                        bottomAnchor.scrollIntoView();
                    }
                }
                
                // Scroll to bottom when content loads
                window.addEventListener('load', scrollToBottom);
                
                // Also try scrolling after a short delay to ensure all content is rendered
                setTimeout(scrollToBottom, 500);
            </script>
            """, unsafe_allow_html=True)
    
    # Display current context if enabled (below the chat)
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
    # Create a cleaner, more compact button layout
    col1, col2, col3 = st.columns([1, 1, 2])  # Giving more space to the right column
    
    with col1:
        # Only enable the button if there's chat history
        disabled = not bool(st.session_state.chat_history)
        if st.button("🗑️ Clear", 
                   use_container_width=True, 
                   disabled=disabled,
                   help="Clear the current conversation history"):
            on_clear()
            st.rerun()
    
    with col2:
        # Only enable the button if there's chat history
        disabled = not bool(st.session_state.chat_history)
        if st.button("💾 Save", 
                   use_container_width=True, 
                   disabled=disabled,
                   help="Save the conversation as a markdown file"):
            on_export()
    
    # Leave the third column empty for balance
    with col3:
        # Optional placeholder if we want to add another control in the future
        pass