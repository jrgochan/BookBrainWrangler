"""
Chat interface component for interacting with the AI.
"""

import streamlit as st
import time

def initialize_chat_state():
    """
    Initialize the chat state in session state if not already present.
    """
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'context' not in st.session_state:
        st.session_state.context = ""

def add_message(role, content):
    """
    Add a message to the chat history.
    
    Args:
        role: 'user' or 'assistant'
        content: The message content
    """
    st.session_state.messages.append({"role": role, "content": content})

def clear_chat():
    """Clear the chat history."""
    st.session_state.messages = []

def render_chat_interface(on_submit=None):
    """
    Render the chat interface with message history and input.
    
    Args:
        on_submit: Callback function when a message is submitted
            Function signature: on_submit(user_input)
            
    Returns:
        User input if submitted, None otherwise
    """
    # Initialize chat state if needed
    initialize_chat_state()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if user_input := st.chat_input("Ask a question about the books in your knowledge base..."):
        # Add user message to chat
        add_message("user", user_input)
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Call the submission handler if provided
        if on_submit:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("Thinking...")
                
                # The on_submit function should return the assistant's response
                response = on_submit(user_input)
                
                # Update the placeholder with the response
                message_placeholder.markdown(response)
                
                # Add assistant message to chat
                add_message("assistant", response)
        
        return user_input
    
    return None

def render_context_display(context, show_context=True):
    """
    Render the context display with an expandable section.
    
    Args:
        context: The context text to display
        show_context: Whether to display the context section
    """
    if show_context and context:
        with st.expander("📚 AI Context (click to expand)", expanded=False):
            st.markdown(context)
    elif show_context:
        with st.expander("📚 AI Context (click to expand)", expanded=False):
            st.info("No context available. Try adding books to your knowledge base.")

def simulate_typing(placeholder, text, speed=0.01):
    """
    Simulate typing effect for assistant responses.
    
    Args:
        placeholder: Streamlit placeholder object
        text: Text to display
        speed: Delay between characters in seconds
    """
    full_text = ""
    for char in text:
        full_text += char
        placeholder.markdown(full_text + "▌")
        time.sleep(speed)
    placeholder.markdown(full_text)