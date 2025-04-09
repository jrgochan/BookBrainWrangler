"""
Message preparation and processing for the Chat with AI feature.
"""

import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

import streamlit as st

from pages.chat.constants import KNOWLEDGE_SOURCES

logger = logging.getLogger(__name__)

def prepare_chat_messages(
    system_prompt: str, 
    chat_history: List[Dict[str, str]], 
    context_strategy: str, 
    context: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Prepare chat messages in the format expected by the API.
    
    Args:
        system_prompt: The system prompt to use
        chat_history: The current chat history
        context_strategy: The context strategy being used
        context: Optional relevant context from knowledge base
        
    Returns:
        List of formatted message dictionaries
    """
    formatted_messages = []
    
    # Add system message
    formatted_messages.append({"role": "system", "content": system_prompt})
    
    # If we have context and we're using it, add a system message with the context
    if context and context_strategy in [KNOWLEDGE_SOURCES["book_knowledge"], KNOWLEDGE_SOURCES["combined"]]:
        context_prompt = (
            "The following information is extracted from the user's book library "
            "and may be relevant to their question. Use this context to inform your response:\n\n"
            f"{context}"
        )
        formatted_messages.append({"role": "system", "content": context_prompt})
    
    # Add conversation history (skip system messages as they're handled separately)
    for message in chat_history:
        if message["role"] != "system":
            formatted_messages.append(message)
    
    return formatted_messages

def record_query_stats(query: str, context_strategy: str, response_time: float, model: str) -> None:
    """
    Record query statistics for analytics.
    
    Args:
        query: The user's query
        context_strategy: The context strategy used
        response_time: The time taken to generate a response
        model: The model used for the response
    """
    stats = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "query_length": len(query),
        "context_strategy": context_strategy,
        "response_time": response_time,
        "model": model
    }
    
    if 'query_stats' not in st.session_state:
        st.session_state.query_stats = []
        
    st.session_state.query_stats.append(stats)
    
    # Limit the size of query stats to prevent session state bloat
    if len(st.session_state.query_stats) > 100:
        st.session_state.query_stats = st.session_state.query_stats[-100:]

def generate_markdown_export(chat_history: List[Dict[str, str]], model: str) -> str:
    """
    Generate a markdown export of the current conversation.
    
    Args:
        chat_history: The current chat history
        model: The model used for the conversation
        
    Returns:
        Markdown string representation of the conversation
    """
    from pages.chat.constants import AVATARS
    
    # Generate a timestamp for the filename
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    
    # Format chat history as markdown
    markdown_content = "# Book Knowledge AI Chat Export\n\n"
    markdown_content += f"*Exported on: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    markdown_content += f"**Model**: {model}\n\n"
    
    for message in chat_history:
        role_icon = AVATARS.get(message["role"], "💬")
        role_name = message["role"].capitalize()
        
        markdown_content += f"## {role_icon} {role_name}\n{message['content']}\n\n"
    
    return markdown_content