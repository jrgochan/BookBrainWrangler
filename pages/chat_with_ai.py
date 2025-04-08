"""
Chat with AI page for the application.
This page provides an interface to chat with AI about book content.
"""

import streamlit as st
import time
from typing import List, Dict, Any, Optional

def render_chat_with_ai_page(ollama_client, knowledge_base):
    """
    Render the Chat with AI page.
    
    Args:
        ollama_client: The OllamaClient instance
        knowledge_base: The KnowledgeBase instance
    """
    st.title("Chat with AI about Your Books")
    
    # Initialize chat history if not present
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Check Ollama connection
    connection_status = ollama_client.check_connection()
    
    if not connection_status:
        st.error("""
            🚫 **Cannot connect to Ollama server**
            
            Ensure Ollama is running and properly configured in Settings.
            Current host: {}
        """.format(ollama_client.host))
        
        st.info("""
            ### How to set up Ollama:
            1. Install Ollama from [ollama.ai](https://ollama.ai)
            2. Start the Ollama server
            3. Pull a model like 'llama2'
            4. Configure the connection in the Settings tab
        """)
        return
    
    # Display available models
    st.sidebar.header("AI Configuration")
    
    # Check loaded model - initialize settings if needed
    if 'ollama_settings' not in st.session_state:
        st.session_state.ollama_settings = {
            'model': 'llama2',  # Default model
            'server_url': 'http://localhost:11434',
            'temperature': 0.7,
            'context_window': 4096,
        }
    current_model = st.session_state.ollama_settings['model']
    model_info = ollama_client.get_model_details(current_model)
    
    if model_info:
        st.sidebar.success(f"✓ Using model: **{current_model}**")
        if "parameters" in model_info:
            st.sidebar.caption(f"Model size: {model_info['parameters']/1_000_000_000:.1f}B parameters")
    else:
        st.sidebar.warning(f"⚠️ Model '{current_model}' not found on the server")
        available_models = ollama_client.list_models()
        if available_models:
            model_names = [m['name'] for m in available_models]
            st.sidebar.caption(f"Available models: {', '.join(model_names)}")
    
    # Get indexed books
    indexed_book_ids = knowledge_base.get_indexed_book_ids()
    
    if not indexed_book_ids:
        st.warning("""
            ⚠️ **No books added to the knowledge base**
            
            Please add books to your knowledge base in the Knowledge Base tab before chatting.
        """)
        return
    
    # Chat interface
    st.sidebar.header("Chat Settings")
    
    # Choose context behavior
    context_strategy = st.sidebar.radio(
        "Context retrieval strategy",
        ["Automatic", "Direct questioning"],
        help="Automatic: Find relevant content from your books for each question. Direct: Only use the AI model knowledge."
    )
    
    # Display chat history with avatars
    chat_container = st.container(height=400, border=False)
    
    with chat_container:
        for i, message in enumerate(st.session_state.chat_history):
            if message["role"] == "user":
                with st.chat_message("user", avatar="🧑‍💻"):
                    st.markdown(message["content"])
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(message["content"])
    
    # Input for new message
    user_query = st.chat_input("Ask a question about your books...")
    
    if user_query:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        
        # Display user message
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_query)
        
        # Display typing indicator
        with st.chat_message("assistant", avatar="🤖"):
            typing_placeholder = st.empty()
            typing_placeholder.markdown("*Thinking...*")
            
            # Get context if using automatic mode
            context = None
            if context_strategy == "Automatic":
                with st.spinner("Retrieving relevant information from your library..."):
                    context = knowledge_base.retrieve_relevant_context(user_query)
            
            # Generate AI response
            try:
                # Ensure we're using the correct model
                model_to_use = st.session_state.ollama_settings.get('model', 'llama2')
                ai_response = ollama_client.generate_response(
                    prompt=user_query,
                    context=context,
                    model=model_to_use
                )
                
                # Replace typing indicator with actual response
                typing_placeholder.markdown(ai_response)
                
                # Add AI response to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                
            except Exception as e:
                typing_placeholder.markdown(f"Sorry, I encountered an error: {str(e)}")
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": f"Sorry, I encountered an error: {str(e)}"
                })
    
    # Add buttons to clear chat or save conversation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear conversation") and st.session_state.chat_history:
            st.session_state.chat_history = []
            st.rerun()
    
    with col2:
        if st.button("Save conversation") and st.session_state.chat_history:
            # Generate a timestamp for the filename
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            
            # Format chat history as markdown
            markdown_content = "# Book Knowledge AI Chat Export\n\n"
            markdown_content += f"*Exported on: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
            
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    markdown_content += f"## 🧑‍💻 User\n{message['content']}\n\n"
                else:
                    markdown_content += f"## 🤖 AI Assistant\n{message['content']}\n\n"
            
            # Create download link
            filename = f"book_ai_chat_{timestamp}.md"
            
            # Create a download button for the markdown content
            st.download_button(
                label="Download conversation",
                data=markdown_content,
                file_name=filename,
                mime="text/markdown"
            )
            
            st.success(f"Chat exported as '{filename}'")
