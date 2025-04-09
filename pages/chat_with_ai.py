"""
Chat with AI page for the application.
This page provides an enhanced interface to chat with AI about book content
with advanced Ollama integration and knowledge base features.
"""

import logging
import streamlit as st
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Chat interface constants
AVATARS = {
    "user": "🧑‍💻",
    "assistant": "🤖",
    "system": "ℹ️"
}

KNOWLEDGE_SOURCES = {
    "book_knowledge": "Book Knowledge",
    "model_knowledge": "Model Knowledge", 
    "combined": "Combined"
}

DEFAULT_SYSTEM_PROMPT = (
    "You are an AI assistant helping with knowledge about books in the user's library. "
    "Be concise, accurate, and helpful. When referencing information from books, "
    "mention the source if available. If you don't know something, say so honestly."
)

class ChatInterface:
    """Manages the chat interface and interactions with the Ollama client."""
    
    def __init__(self, ollama_client, knowledge_base):
        """Initialize the chat interface with necessary components."""
        self.ollama_client = ollama_client
        self.knowledge_base = knowledge_base
        self._initialize_session_state()
        
    def _initialize_session_state(self):
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
            st.session_state.system_prompt = DEFAULT_SYSTEM_PROMPT
        
        # Current context
        if 'current_context' not in st.session_state:
            st.session_state.current_context = None
        
        # Query stats for analytics
        if 'query_stats' not in st.session_state:
            st.session_state.query_stats = []
            
    def get_current_model(self):
        """Get the current model name with fallback."""
        try:
            if isinstance(st.session_state.ollama_settings, dict):
                return st.session_state.ollama_settings.get('model', 'llama2')
            return 'llama2'
        except Exception as e:
            logger.warning(f"Error retrieving current model: {str(e)}")
            return 'llama2'
            
    def check_connection(self):
        """Check if connected to Ollama server."""
        connection_status = self.ollama_client.check_connection()
        
        if not connection_status:
            self._render_connection_error(self.ollama_client.server_url)
            return False
        return True
    
    def _render_connection_error(self, host):
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
    
    def render_sidebar(self):
        """Render the sidebar with model info and chat controls."""
        st.sidebar.header("AI Configuration")
        
        # Safely display model information
        current_model = self.get_current_model()
        try:
            # Get model details
            model_info = self.ollama_client.get_model_details(current_model)
            
            if model_info:
                st.sidebar.success(f"✓ Using model: **{current_model}**")
                if isinstance(model_info, dict) and "parameters" in model_info:
                    st.sidebar.caption(f"Model size: {model_info['parameters']/1_000_000_000:.1f}B parameters")
            else:
                st.sidebar.warning(f"⚠️ Model '{current_model}' not found on the server")
                available_models = self.ollama_client.list_models()
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
        indexed_book_ids = self.knowledge_base.get_indexed_book_ids()
        if indexed_book_ids:
            st.sidebar.success(f"✓ {len(indexed_book_ids)} books in knowledge base")
        else:
            st.sidebar.warning("No books in knowledge base")
            if context_strategy != KNOWLEDGE_SOURCES["model_knowledge"]:
                st.sidebar.info("Switching to 'Model Knowledge' mode since no books are available")
                context_strategy = KNOWLEDGE_SOURCES["model_knowledge"]
                
        return context_strategy, indexed_book_ids
    
    def render_chat_history(self):
        """Render the chat history with message bubbles."""
        # Main chat display area
        chat_container = st.container(height=400, border=False)
        
        with chat_container:
            # Display chat history with avatars
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"], avatar=AVATARS.get(message["role"], "💬")):
                    if message["role"] == "system":
                        st.caption("System Instruction")
                    st.markdown(message["content"])
        
        # Display current context if enabled
        if st.session_state.chat_config['show_context'] and st.session_state.current_context:
            with st.expander("📚 Current Context", expanded=False):
                st.markdown(st.session_state.current_context)
                
    def process_user_query(self, query, context_strategy):
        """Process a user query and generate a response."""
        logger.info(f"Processing user query: '{query}' with strategy: {context_strategy}")
        
        # Start timer for analytics
        start_time = time.time()
        
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": query})
        
        # Display user message
        with st.chat_message("user", avatar=AVATARS["user"]):
            st.markdown(query)
        
        # Display typing indicator
        with st.chat_message("assistant", avatar=AVATARS["assistant"]):
            typing_placeholder = st.empty()
            typing_placeholder.markdown("*Thinking...*")
            
            # Get context based on strategy
            context = self._retrieve_context(query, context_strategy)
            
            # Generate AI response
            try:
                response_text = self._generate_ai_response(query, context, context_strategy)
                
                # Replace typing indicator with actual response
                typing_placeholder.markdown(response_text)
                
                # Add AI response to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": response_text})
                
                # Record analytics
                response_time = time.time() - start_time
                self._record_query_stats(query, context_strategy, response_time)
                
            except Exception as e:
                logger.error(f"Error generating response: {str(e)}")
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                typing_placeholder.markdown(error_msg)
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": error_msg
                })
    
    def _retrieve_context(self, query, context_strategy):
        """Retrieve relevant context from knowledge base based on strategy."""
        context = None
        if context_strategy in [KNOWLEDGE_SOURCES["book_knowledge"], KNOWLEDGE_SOURCES["combined"]]:
            with st.spinner("Retrieving relevant information from your library..."):
                try:
                    logger.debug("Retrieving context from knowledge base")
                    context = self.knowledge_base.retrieve_relevant_context(query)
                    logger.debug(f"Retrieved context of length: {len(context) if context else 0}")
                except AttributeError as e:
                    logger.warning(f"AttributeError when retrieving context: {str(e)}")
                    # Fall back to search_engine if the method doesn't exist
                    if hasattr(self.knowledge_base, 'search_engine') and hasattr(self.knowledge_base.search_engine, 'retrieve_relevant_context'):
                        context = self.knowledge_base.search_engine.retrieve_relevant_context(
                            query=query,
                            num_results=st.session_state.chat_config['num_ctx_results']
                        )
                except Exception as e:
                    logger.error(f"Error retrieving context: {str(e)}")
                
                # Save the current context for display if enabled
                st.session_state.current_context = context
                
        return context
    
    def _generate_ai_response(self, query, context, context_strategy):
        """Generate a response from the AI model based on query and context."""
        # Prepare model parameters
        model_to_use = self.get_current_model()
        temperature = st.session_state.chat_config['temperature']
        max_tokens = st.session_state.chat_config['max_tokens']
        
        logger.debug(f"Generating response with model={model_to_use}, temperature={temperature}")
        
        # Prepare the chat history in the format expected by the API
        formatted_messages = self._prepare_chat_messages(context_strategy, context)
        
        # Different handling based on knowledge source strategy
        if context_strategy == KNOWLEDGE_SOURCES["model_knowledge"]:
            # Use chat endpoint for model knowledge mode
            logger.debug("Using chat endpoint for model knowledge mode")
            ai_response = self.ollama_client.chat(
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model_to_use
            )
            response_text = ai_response.get("content", "Error retrieving response")
        else:
            # For book knowledge or combined mode, use generate endpoint with context
            logger.debug("Using generate endpoint with context")
            
            # Extract the user query from the last message
            user_query = query
            if formatted_messages and isinstance(formatted_messages[-1], dict):
                user_query = formatted_messages[-1].get('content', query)
            
            ai_response = self.ollama_client.generate_response(
                prompt=user_query,
                context=context,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model_to_use
            )
            response_text = ai_response
            
        return response_text
    
    def _prepare_chat_messages(self, context_strategy, context=None):
        """Prepare chat messages in the format expected by the API."""
        formatted_messages = []
        
        # Add system message
        formatted_messages.append({"role": "system", "content": st.session_state.system_prompt})
        
        # If we have context and we're using it, add a system message with the context
        if context and context_strategy in [KNOWLEDGE_SOURCES["book_knowledge"], KNOWLEDGE_SOURCES["combined"]]:
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
    
    def _record_query_stats(self, query, context_strategy, response_time):
        """Record query statistics for analytics."""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "query_length": len(query),
            "context_strategy": context_strategy,
            "response_time": response_time,
            "model": self.get_current_model()
        }
        
        st.session_state.query_stats.append(stats)
        
        # Limit the size of query stats to prevent session state bloat
        if len(st.session_state.query_stats) > 100:
            st.session_state.query_stats = st.session_state.query_stats[-100:]
    
    def export_conversation(self):
        """Export the current conversation as a markdown file."""
        # Generate a timestamp for the filename
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        
        # Format chat history as markdown
        markdown_content = "# Book Knowledge AI Chat Export\n\n"
        markdown_content += f"*Exported on: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        markdown_content += f"**Model**: {self.get_current_model()}\n\n"
        
        for message in st.session_state.chat_history:
            role_icon = AVATARS.get(message["role"], "💬")
            role_name = message["role"].capitalize()
            
            markdown_content += f"## {role_icon} {role_name}\n{message['content']}\n\n"
        
        # Create download button for the markdown content
        filename = f"book_ai_chat_{timestamp}.md"
        st.download_button(
            label="Download conversation",
            data=markdown_content,
            file_name=filename,
            mime="text/markdown"
        )
        
        st.success(f"Chat exported as '{filename}'")
        
    def clear_conversation(self):
        """Clear the current conversation history."""
        st.session_state.chat_history = []
        st.session_state.current_context = None


def render_chat_with_ai_page(ollama_client, knowledge_base):
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
    current_model = chat_interface.get_current_model()
    user_query = st.chat_input(f"Ask {current_model} about your books...")
    
    if user_query:
        chat_interface.process_user_query(user_query, context_strategy)
    
    # Chat action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear conversation", use_container_width=True) and st.session_state.chat_history:
            chat_interface.clear_conversation()
            st.rerun()
    
    with col2:
        if st.button("Save conversation", use_container_width=True) and st.session_state.chat_history:
            chat_interface.export_conversation()
