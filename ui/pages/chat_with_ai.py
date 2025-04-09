"""
Chat with AI page for the application.
This page provides an interface for users to chat with AI about their documents.
"""

import streamlit as st
import time
from typing import List, Dict, Any, Optional

from utils.logger import get_logger
from ui.components.chat_interface import (
    initialize_chat_state, 
    add_message, 
    clear_chat, 
    render_chat_interface, 
    render_context_display,
    simulate_typing
)

# Get a logger for this module
logger = get_logger(__name__)

def render_chat_with_ai_page(ai_client, knowledge_base):
    """
    Render the Chat with AI page.
    
    Args:
        ai_client: The AI client instance (e.g., OllamaClient)
        knowledge_base: The KnowledgeBase instance
    """
    logger.info("Rendering Chat with AI page")
    st.title("Chat with AI")
    
    # Initialize the chat session state
    initialize_chat_state()
    
    # Render settings sidebar
    render_chat_settings_sidebar(ai_client)
    
    # Render the chat interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Render the chat UI and get any new user input
        user_input = render_chat_interface(
            on_submit=lambda msg: process_user_message(msg, ai_client, knowledge_base)
        )
        
        # Process user input if submitted via the function
        if user_input:
            process_user_message(user_input, ai_client, knowledge_base)
    
    with col2:
        render_chat_sidebar(knowledge_base)

def render_chat_settings_sidebar(ai_client):
    """
    Render the chat settings in the sidebar.
    
    Args:
        ai_client: The AI client instance
    """
    with st.sidebar:
        st.subheader("Chat Settings")
        
        # Model selection
        try:
            available_models = ai_client.list_models()
            if available_models:
                selected_model = st.selectbox(
                    "AI Model", 
                    available_models,
                    index=available_models.index(st.session_state.ollama_settings.get('model', available_models[0])) if st.session_state.ollama_settings.get('model') in available_models else 0
                )
                
                # Update the AI client model if changed
                if selected_model != st.session_state.ollama_settings.get('model'):
                    st.session_state.ollama_settings['model'] = selected_model
                    ai_client.model_name = selected_model
                    logger.info(f"Changed AI model to {selected_model}")
            else:
                st.warning("No AI models available. Please check your Ollama server.")
                selected_model = st.session_state.ollama_settings.get('model', "llama2")
        except Exception as e:
            logger.error(f"Error loading AI models: {str(e)}")
            st.error(f"Error loading AI models: {str(e)}")
            selected_model = st.session_state.ollama_settings.get('model', "llama2")
        
        # Temperature setting
        temperature = st.slider(
            "Temperature", 
            min_value=0.0, 
            max_value=2.0, 
            value=st.session_state.ollama_settings.get('temperature', 0.7),
            step=0.1,
            help="Higher values make the output more random, lower values make it more deterministic."
        )
        
        # Update the session state if changed
        if temperature != st.session_state.ollama_settings.get('temperature'):
            st.session_state.ollama_settings['temperature'] = temperature
        
        # Context window setting
        context_window = st.slider(
            "Context Window", 
            min_value=1024, 
            max_value=8192, 
            value=st.session_state.ollama_settings.get('context_window', 4096),
            step=1024,
            help="Maximum number of tokens to consider for context."
        )
        
        # Update the session state if changed
        if context_window != st.session_state.ollama_settings.get('context_window'):
            st.session_state.ollama_settings['context_window'] = context_window
        
        # Chat controls
        st.divider()
        if st.button("Clear Chat History", use_container_width=True):
            clear_chat()
            st.rerun()

def render_chat_sidebar(knowledge_base):
    """
    Render the chat information sidebar.
    
    Args:
        knowledge_base: The KnowledgeBase instance
    """
    st.subheader("Knowledge Base")
    
    # Display KB stats
    try:
        kb_doc_ids = knowledge_base.get_document_ids()
        book_ids = [doc_id for doc_id in kb_doc_ids if doc_id.startswith("book_")]
        
        if book_ids:
            st.success(f"✅ {len(book_ids)} books available for context")
            
            with st.expander("Available Books", expanded=False):
                # This could be enhanced to show more details about the books
                for doc_id in book_ids:
                    book_id = doc_id.replace("book_", "")
                    st.write(f"• Book ID: {book_id}")
        else:
            st.warning("""
            ⚠️ No books in knowledge base
            
            Add books to the knowledge base in the 'Knowledge Base' tab to enable AI interactions with your documents.
            """)
    except Exception as e:
        logger.error(f"Error getting knowledge base stats: {str(e)}")
        st.error(f"Error retrieving knowledge base information: {str(e)}")
    
    # Display chat instructions
    with st.expander("Chat Instructions", expanded=False):
        st.markdown("""
        ### How to Chat with Your Books
        
        - Ask questions about the content in your knowledge base
        - Request summaries or explanations of concepts
        - Ask for comparisons between different books
        - Explore themes, characters, or arguments across your collection
        
        The AI will search your knowledge base for relevant information before answering questions.
        """)
        
        st.caption("Note: The AI's responses are based on the books you've added to the knowledge base.")

def process_user_message(message: str, ai_client, knowledge_base):
    """
    Process a user message and generate an AI response.
    
    Args:
        message: The user message
        ai_client: The AI client instance
        knowledge_base: The KnowledgeBase instance
    """
    if not message.strip():
        return
    
    logger.info(f"Processing user message: {message[:50]}{'...' if len(message) > 50 else ''}")
    
    # Add user message to chat
    add_message("user", message)
    
    # Create placeholders for response
    response_placeholder = st.empty()
    context_placeholder = st.empty()
    
    # Show a temporary "thinking" message
    with response_placeholder:
        status = st.status("Thinking...", expanded=False)
        search_results_container = st.empty()
    
    # Search the knowledge base
    try:
        search_results = knowledge_base.search(message, limit=5)
        
        if search_results:
            # Format search results for display
            with status:
                st.write("🔍 Searching knowledge base...")
                
                with search_results_container:
                    st.caption("Found relevant information in your books:")
                    for i, result in enumerate(search_results[:3], 1):
                        score = result.get('score', 0)
                        metadata = result.get('metadata', {})
                        source = f"{metadata.get('title', 'Unknown')} by {metadata.get('author', 'Unknown')}"
                        
                        st.write(f"{i}. Score: {score:.2f} - {source}")
            
            # Prepare context for the AI
            context_text = "\n\n".join([
                f"Source: {result.get('metadata', {}).get('title', 'Unknown')} by {result.get('metadata', {}).get('author', 'Unknown')}\n\n{result.get('text', '')}"
                for result in search_results
            ])
            
            # Generate system prompt with context
            system_prompt = f"""You are a helpful AI assistant that has knowledge about the user's books and documents. 
            Answer questions based on the following context from the user's knowledge base.
            If the context doesn't contain the answer, say so and provide general information if possible.
            Always cite the sources you use in your answer.
            
            Context:
            {context_text}
            """
            
            # Convert chat history to format expected by AI client
            messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in st.session_state.messages
                if msg["role"] != "system"  # Exclude previous system messages
            ]
            
            # Update status
            status.update(label="Generating response...", state="running")
            
            # Update our context display
            if context_text:
                with context_placeholder:
                    render_context_display(context_text)
            
            # Generate the response
            try:
                # Response with typing effect
                with status:
                    try:
                        response = ai_client.generate_chat_response(
                            messages=messages,
                            system_prompt=system_prompt,
                            temperature=st.session_state.ollama_settings.get('temperature', 0.7),
                            max_tokens=st.session_state.ollama_settings.get('context_window', 4096),
                        )
                        
                        status.update(label="Response ready", state="complete")
                        status.update(label="", state="complete")
                        
                        # Clear the search results display
                        search_results_container.empty()
                        
                        # Add AI response to chat history
                        add_message("assistant", response)
                        
                    except Exception as e:
                        logger.error(f"Error generating AI response: {str(e)}")
                        status.update(label=f"Error: {str(e)}", state="error")
                        add_message("assistant", f"I'm sorry, I encountered an error while generating a response: {str(e)}")
            
            except Exception as e:
                logger.error(f"Error displaying AI response: {str(e)}")
                status.update(label=f"Error: {str(e)}", state="error")
                add_message("assistant", f"I'm sorry, I encountered an error while displaying the response: {str(e)}")
        
        else:
            # No search results
            status.update(label="No relevant information found", state="complete")
            status.empty()
            
            # Generate a response without context
            system_prompt = """You are a helpful AI assistant that can answer questions about books and documents.
            The user has a document knowledge base, but no relevant information was found for their query.
            Let them know you don't have specific information about their documents related to this query,
            but you can still try to provide general information if applicable.
            """
            
            # Convert chat history to format expected by AI client
            messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in st.session_state.messages
                if msg["role"] != "system"  # Exclude previous system messages
            ]
            
            try:
                response = ai_client.generate_chat_response(
                    messages=messages,
                    system_prompt=system_prompt,
                    temperature=st.session_state.ollama_settings.get('temperature', 0.7),
                    max_tokens=st.session_state.ollama_settings.get('context_window', 4096),
                )
                
                # Add AI response to chat history
                add_message("assistant", response)
                
            except Exception as e:
                logger.error(f"Error generating AI response: {str(e)}")
                add_message("assistant", f"I'm sorry, I encountered an error while generating a response: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error searching knowledge base: {str(e)}")
        status.update(label=f"Error searching knowledge base: {str(e)}", state="error")
        status.empty()
        
        # Still try to generate a response
        add_message("assistant", f"I'm sorry, I encountered an error while searching the knowledge base: {str(e)}")
        
    # Check if we need to clear any remaining UI elements
    try:
        status.empty()
        search_results_container.empty()
    except:
        pass