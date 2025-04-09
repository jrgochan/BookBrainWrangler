"""
Chat interface component for interacting with the AI.
Provides a reusable chat interface with message history, context, and typing effects.
"""

import streamlit as st
import time
from typing import Optional, Callable, List, Dict, Any, Union

def initialize_chat_state():
    """
    Initialize the chat state in session state if not already present.
    """
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'context' not in st.session_state:
        st.session_state.context = ""
        
    if 'chat_error' not in st.session_state:
        st.session_state.chat_error = None
        
    if 'processing_message' not in st.session_state:
        st.session_state.processing_message = False

def add_message(role: str, content: str):
    """
    Add a message to the chat history.
    
    Args:
        role: 'user' or 'assistant' or 'system'
        content: The message content
    """
    st.session_state.messages.append({"role": role, "content": content})

def clear_chat():
    """Clear the chat history."""
    st.session_state.messages = []
    st.session_state.chat_error = None

def set_chat_error(error_message: str):
    """
    Set an error message for the chat interface.
    
    Args:
        error_message: Error message to display
    """
    st.session_state.chat_error = error_message

def clear_chat_error():
    """Clear any chat error message."""
    st.session_state.chat_error = None

def get_chat_messages() -> List[Dict[str, str]]:
    """
    Get the current chat messages.
    
    Returns:
        List of message dictionaries with 'role' and 'content' keys
    """
    initialize_chat_state()
    return st.session_state.messages

def render_chat_interface(
    on_submit: Optional[Callable[[str], str]] = None,
    placeholder_text: str = "Ask a question about the books in your knowledge base...",
    disabled: bool = False,
    key_prefix: str = "chat"
) -> Optional[str]:
    """
    Render the chat interface with message history and input.
    
    Args:
        on_submit: Callback function when a message is submitted
            Function signature: on_submit(user_input) -> str
        placeholder_text: Placeholder text for the chat input
        disabled: Whether the chat input is disabled
        key_prefix: Prefix for Streamlit keys to avoid conflicts
            
    Returns:
        User input if submitted, None otherwise
    """
    # Initialize chat state if needed
    initialize_chat_state()
    
    # Display error message if exists
    if st.session_state.chat_error:
        st.error(st.session_state.chat_error)
        # Add a button to clear the error
        if st.button("Dismiss Error", key=f"{key_prefix}_dismiss_error"):
            clear_chat_error()
    
    # Display chat messages
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Display the message processing indicator if applicable
    if st.session_state.processing_message:
        with st.chat_message("assistant"):
            st.write("Thinking...")
    
    # Chat input
    if not disabled and not st.session_state.processing_message:
        if user_input := st.chat_input(placeholder_text, key=f"{key_prefix}_chat_input"):
            # Add user message to chat
            add_message("user", user_input)
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(user_input)
            
            # Set processing flag
            st.session_state.processing_message = True
            
            # Call the submission handler if provided
            if on_submit:
                try:
                    with st.chat_message("assistant"):
                        message_placeholder = st.empty()
                        message_placeholder.markdown("Thinking...")
                        
                        # The on_submit function should return the assistant's response
                        response = on_submit(user_input)
                        
                        # Update the placeholder with the response
                        if response:
                            message_placeholder.markdown(response)
                            
                            # Add assistant message to chat
                            add_message("assistant", response)
                        else:
                            message_placeholder.markdown("I couldn't generate a response. Please try again.")
                except Exception as e:
                    set_chat_error(f"Error generating response: {str(e)}")
            
            # Clear processing flag
            st.session_state.processing_message = False
            
            return user_input
    
    return None

def render_context_display(
    context: str, 
    show_context: bool = True,
    title: str = "📚 AI Context (click to expand)"
):
    """
    Render the context display with an expandable section.
    
    Args:
        context: The context text to display
        show_context: Whether to display the context section
        title: Title for the expander
    """
    if show_context and context:
        with st.expander(title, expanded=False):
            st.markdown(context)
            
            # Add a divider
            st.divider()
            
            # Add information about the context
            st.caption("This represents the information retrieved from your knowledge base that the AI is using to answer your question.")
    elif show_context:
        with st.expander(title, expanded=False):
            st.info("No context available. Try adding books to your knowledge base.")
            st.caption("The AI needs information from your books to provide relevant answers.")

def simulate_typing(
    placeholder: Any, 
    text: str, 
    speed: float = 0.01,
    min_speed: float = 0.001,
    max_chars: int = 1000
):
    """
    Simulate typing effect for assistant responses.
    Adjusts speed based on text length for better performance.
    
    Args:
        placeholder: Streamlit placeholder object
        text: Text to display
        speed: Delay between characters in seconds
        min_speed: Minimum delay for very long texts
        max_chars: Maximum number of characters before reducing animation detail
    """
    # Adjust speed for long texts
    text_length = len(text)
    
    if text_length > max_chars:
        # For very long texts, reduce animation detail
        chunk_size = max(1, text_length // 100)
        reduced_speed = max(min_speed, speed * 0.5)
        
        full_text = ""
        for i in range(0, text_length, chunk_size):
            chunk = text[i:i+chunk_size]
            full_text += chunk
            placeholder.markdown(full_text + "▌")
            time.sleep(reduced_speed)
    else:
        # Full animation for shorter texts
        full_text = ""
        for char in text:
            full_text += char
            placeholder.markdown(full_text + "▌")
            time.sleep(speed)
            
    # Final display without cursor
    placeholder.markdown(text)