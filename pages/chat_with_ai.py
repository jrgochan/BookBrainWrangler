"""
Chat with AI page for the application.
This page provides an enhanced interface to chat with AI about book content
with advanced Ollama integration and knowledge base features.
"""

import streamlit as st
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union

def render_chat_with_ai_page(ollama_client, knowledge_base):
    """
    Render the Chat with AI page.
    
    Args:
        ollama_client: The OllamaClient instance
        knowledge_base: The KnowledgeBase instance
    """
    st.title("Chat with AI about Your Books")
    
    # Initialize session state variables if not present
    _initialize_session_state()
    
    # Check Ollama connection
    connection_status = ollama_client.check_connection()
    
    if not connection_status:
        _render_connection_error(ollama_client.server_url)
        return
    
    # Get model information for display
    current_model = _get_current_model()
    
    # Display available models
    st.sidebar.header("AI Configuration")
    
    # Safely initialize settings if needed
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
                except Exception:
                    st.sidebar.caption("Error retrieving model information")
    except Exception as e:
        # Handle any unexpected errors in the model display section
        st.sidebar.error(f"Error displaying model information: {str(e)}")
    
    # Get indexed books
    indexed_book_ids = knowledge_base.get_indexed_book_ids()
    
    if not indexed_book_ids:
        st.warning("""
            ⚠️ **No books added to the knowledge base**
            
            Please add books to your knowledge base in the Knowledge Base tab before chatting.
        """)
        return
    
    # Sidebar for chat controls
    with st.sidebar:
        st.header("Chat Controls")
        
        # Knowledge base integration toggle
        context_strategy = st.radio(
            "Knowledge Source",
            ["Book Knowledge", "Model Knowledge", "Combined"],
            help=("Book Knowledge: Use your book library as primary context. "
                  "Model Knowledge: Use only the model's built-in knowledge. "
                  "Combined: Use both sources together.")
        )
        
        # Display indexed books count
        if indexed_book_ids:
            st.success(f"✓ {len(indexed_book_ids)} books in knowledge base")
        else:
            st.warning("No books in knowledge base")
            if context_strategy != "Model Knowledge":
                st.info("Switching to 'Model Knowledge' mode since no books are available")
                context_strategy = "Model Knowledge"
    
    # Main chat display area
    chat_container = st.container(height=400, border=False)
    
    with chat_container:
        # Display chat history with avatars
        for message in st.session_state.chat_history:
            if message["role"] == "system":
                # System messages are displayed differently
                with st.chat_message("system", avatar="ℹ️"):
                    st.caption("System Instruction")
                    st.markdown(message["content"])
            elif message["role"] == "user":
                with st.chat_message("user", avatar="🧑‍💻"):
                    st.markdown(message["content"])
            else:  # assistant
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(message["content"])
    
    # Display current context if enabled
    if st.session_state.chat_config['show_context'] and st.session_state.current_context:
        with st.expander("📚 Current Context", expanded=False):
            st.markdown(st.session_state.current_context)
    
    # Input for new message
    user_query = st.chat_input(f"Ask {current_model} about your books...")
    
    if user_query:
        _process_user_query(user_query, ollama_client, knowledge_base, context_strategy)
    
    # Chat action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear conversation", use_container_width=True) and st.session_state.chat_history:
            st.session_state.chat_history = []
            st.session_state.current_context = None
            st.rerun()
    
    with col2:
        if st.button("Save conversation", use_container_width=True) and st.session_state.chat_history:
            _export_conversation()


def _initialize_session_state():
    """Initialize all required session state variables."""
    # Core chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Chat configuration
    if 'chat_config' not in st.session_state:
        st.session_state.chat_config = {
            'temperature': 0.7,
            'max_tokens': 1000,
            'top_p': 0.9,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0,
            'stream': True,
            'show_context': False,
            'context_window': 4096,
            'num_ctx_results': 5
        }
    
    # Custom instructions/system prompt
    if 'system_prompt' not in st.session_state:
        st.session_state.system_prompt = (
            "You are an AI assistant helping with knowledge about books in the user's library. "
            "Be concise, accurate, and helpful. When referencing information from books, "
            "mention the source if available. If you don't know something, say so honestly."
        )
    
    # Current context
    if 'current_context' not in st.session_state:
        st.session_state.current_context = None
    
    # Query stats for analytics
    if 'query_stats' not in st.session_state:
        st.session_state.query_stats = []


def _render_connection_error(host):
    """Display error message when Ollama connection fails."""
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


def _process_user_query(query, ollama_client, knowledge_base, context_strategy):
    """Process a user query and generate a response."""
    # Start timer for analytics
    start_time = time.time()
    
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": query})
    
    # Display user message
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(query)
    
    # Display typing indicator
    with st.chat_message("assistant", avatar="🤖"):
        typing_placeholder = st.empty()
        typing_placeholder.markdown("*Thinking...*")
        
        # Get context based on strategy
        context = None
        if context_strategy in ["Book Knowledge", "Combined"]:
            with st.spinner("Retrieving relevant information from your library..."):
                try:
                    context = knowledge_base.retrieve_relevant_context(query)
                except AttributeError:
                    # Fall back to search_engine if the method doesn't exist
                    if hasattr(knowledge_base, 'search_engine') and hasattr(knowledge_base.search_engine, 'retrieve_relevant_context'):
                        context = knowledge_base.search_engine.retrieve_relevant_context(
                            query=query,
                            num_results=st.session_state.chat_config['num_ctx_results']
                        )
                
                # Save the current context for display if enabled
                st.session_state.current_context = context
        
        # Generate AI response
        try:
            # Prepare model parameters
            model_to_use = _get_current_model()
            temperature = st.session_state.chat_config['temperature']
            max_tokens = st.session_state.chat_config['max_tokens']
            
            # Prepare the chat history in the format expected by the API
            formatted_messages = _prepare_chat_messages(context_strategy, context)
            
            # Generate response
            if context_strategy == "Model Knowledge":
                # Check if chat method exists
                if hasattr(ollama_client, 'chat'):
                    # Don't include context for Model Knowledge mode
                    ai_response = ollama_client.chat(
                        messages=formatted_messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    response_text = ai_response.get("content", "Error retrieving response")
                else:
                    # Fall back to generate_response
                    ai_response = ollama_client.generate_response(
                        prompt=query,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        model=model_to_use
                    )
                    response_text = ai_response
            else:
                # Include context for other modes
                if isinstance(formatted_messages, list) and formatted_messages:
                    last_message = formatted_messages[-1]
                    if isinstance(last_message, dict) and 'content' in last_message:
                        user_query = last_message['content']
                    else:
                        user_query = query
                else:
                    user_query = query
                
                ai_response = ollama_client.generate_response(
                    prompt=user_query,
                    context=context,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model=model_to_use
                )
                response_text = ai_response
            
            # Replace typing indicator with actual response
            typing_placeholder.markdown(response_text)
            
            # Add AI response to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": response_text})
            
            # Record analytics
            response_time = time.time() - start_time
            _record_query_stats(query, context_strategy, response_time)
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            typing_placeholder.markdown(error_msg)
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": error_msg
            })


def _prepare_chat_messages(context_strategy, context=None):
    """Prepare chat messages in the format expected by the API."""
    formatted_messages = []
    
    # Add system message
    formatted_messages.append({"role": "system", "content": st.session_state.system_prompt})
    
    # If we have context and we're using it, add a system message with the context
    if context and context_strategy in ["Book Knowledge", "Combined"]:
        context_prompt = (
            "The following information is extracted from the user's book library "
            "and may be relevant to their question. Use this context to inform your response:\n\n"
            f"{context}"
        )
        formatted_messages.append({"role": "system", "content": context_prompt})
    
    # Add conversation history (skip system messages as they're handled separately)
    for message in st.session_state.chat_history:
        if message["role"] != "system":
            formatted_messages.append(message)
    
    return formatted_messages


def _export_conversation():
    """Export the current conversation as a markdown file."""
    # Generate a timestamp for the filename
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    
    # Format chat history as markdown
    markdown_content = "# Book Knowledge AI Chat Export\n\n"
    markdown_content += f"*Exported on: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    markdown_content += f"**Model**: {_get_current_model()}\n\n"
    
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            markdown_content += f"## 🧑‍💻 User\n{message['content']}\n\n"
        elif message["role"] == "assistant":
            markdown_content += f"## 🤖 AI Assistant\n{message['content']}\n\n"
        elif message["role"] == "system":
            markdown_content += f"## ⚙️ System\n{message['content']}\n\n"
    
    # Create download button for the markdown content
    filename = f"book_ai_chat_{timestamp}.md"
    st.download_button(
        label="Download conversation",
        data=markdown_content,
        file_name=filename,
        mime="text/markdown"
    )
    
    st.success(f"Chat exported as '{filename}'")


def _record_query_stats(query, context_strategy, response_time):
    """Record query statistics for analytics."""
    stats = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "query_length": len(query),
        "context_strategy": context_strategy,
        "response_time": response_time,
        "model": _get_current_model()
    }
    
    st.session_state.query_stats.append(stats)
    
    # Limit the size of query stats to prevent session state bloat
    if len(st.session_state.query_stats) > 100:
        st.session_state.query_stats = st.session_state.query_stats[-100:]


def _get_current_model():
    """Get the current model name with fallback."""
    try:
        if isinstance(st.session_state.ollama_settings, dict):
            return st.session_state.ollama_settings.get('model', 'llama2')
        return 'llama2'
    except:
        return 'llama2'
