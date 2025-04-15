"""
Chat interface class for the Chat with AI feature.
"""

import logging
import time
import streamlit as st
from typing import Any, Dict, List, Optional, Tuple

from pages.chat.utils import (
    get_current_model,
    retrieve_context,
    initialize_session_state
)
from pages.chat.message_handling import (
    prepare_chat_messages,
    record_query_stats,
    generate_markdown_export
)
from pages.chat.ui_components import (
    render_chat_history,
    render_connection_error,
    render_sidebar
)
from pages.chat.constants import AVATARS, KNOWLEDGE_SOURCES

logger = logging.getLogger(__name__)

class ChatInterface:
    """
    Manages the chat interface and interactions with the Ollama client.
    """
    
    def __init__(self, ollama_client, knowledge_base):
        """
        Initialize the chat interface with necessary components.
        
        Args:
            ollama_client: The OllamaClient instance
            knowledge_base: The KnowledgeBase instance
        """
        self.ollama_client = ollama_client
        self.knowledge_base = knowledge_base
        initialize_session_state()
        
    def check_connection(self) -> bool:
        """
        Check if connected to Ollama server.
        
        Returns:
            True if connected, False otherwise
        """
        connection_status = self.ollama_client.check_connection()
        
        if not connection_status:
            render_connection_error(self.ollama_client.server_url)
            return False
        return True
    
    def render_sidebar(self) -> Tuple[str, List[int]]:
        """
        Render the sidebar with model info and chat controls.
        
        Returns:
            Tuple of (selected context strategy, list of indexed book IDs)
        """
        return render_sidebar(self.ollama_client, self.knowledge_base)
    
    def render_chat_history(self) -> None:
        """Render the chat history with message bubbles."""
        render_chat_history(
            st.session_state.chat_history,
            st.session_state.chat_config['show_context'],
            st.session_state.current_context
        )
                
    def process_user_query(self, query: str, context_strategy: str) -> None:
        """
        Process a user query and generate a response.
        
        Args:
            query: The user's query
            context_strategy: The context strategy to use
        """
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
            context = retrieve_context(
                self.knowledge_base, 
                query, 
                context_strategy,
                st.session_state.chat_config['num_ctx_results']
            )
            
            # Generate AI response
            try:
                response_text = self._generate_ai_response(query, context, context_strategy)
                
                # Replace typing indicator with actual response
                typing_placeholder.markdown(response_text)
                
                # Add AI response to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": response_text})
                
                # Record analytics
                response_time = time.time() - start_time
                record_query_stats(
                    query, 
                    context_strategy, 
                    response_time, 
                    get_current_model()
                )
                
            except Exception as e:
                logger.error(f"Error generating response: {str(e)}")
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                typing_placeholder.markdown(error_msg)
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": error_msg
                })
    
    def _generate_ai_response(self, query: str, context: Optional[str], context_strategy: str) -> str:
        """
        Generate a response from the AI model based on query and context.
        
        Args:
            query: The user's query
            context: Optional relevant context from knowledge base
            context_strategy: The context strategy to use
            
        Returns:
            Generated response text
        """
        # Prepare model parameters
        model_to_use = get_current_model()
        temperature = st.session_state.chat_config['temperature']
        max_tokens = st.session_state.chat_config['max_tokens']
        
        logger.debug(f"Generating response with model={model_to_use}, temperature={temperature}")
        
        # Prepare the chat history in the format expected by the API
        formatted_messages = prepare_chat_messages(
            st.session_state.system_prompt,
            st.session_state.chat_history,
            context_strategy,
            context
        )
        
        # Different handling based on knowledge source strategy
        if context_strategy == KNOWLEDGE_SOURCES["model_knowledge"]:
            # Use chat endpoint for model knowledge mode
            logger.debug("Using chat endpoint for model knowledge mode")
            ai_response = self.ollama_client.generate_chat_response(
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model_to_use
            )
            response_text = ai_response
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
    
    def export_conversation(self) -> None:
        """Export the current conversation as a markdown file."""
        # Generate markdown content
        markdown_content = generate_markdown_export(
            st.session_state.chat_history,
            get_current_model()
        )
        
        # Generate a timestamp for the filename
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"book_ai_chat_{timestamp}.md"
        
        # Create download button for the markdown content
        st.download_button(
            label="Download conversation",
            data=markdown_content,
            file_name=filename,
            mime="text/markdown"
        )
        
        st.success(f"Chat exported as '{filename}'")
        
    def clear_conversation(self) -> None:
        """Clear the current conversation history."""
        st.session_state.chat_history = []
        st.session_state.current_context = None
