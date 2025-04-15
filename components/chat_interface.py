"""
Chat interface component for Book Knowledge AI application.
"""

import streamlit as st
from typing import List, Dict, Any, Optional, Tuple

from utils.logger import get_logger
from ai import AIClient, get_default_client
from knowledge_base import KnowledgeBase

logger = get_logger(__name__)

def initialize_chat_state():
    """Initialize the chat-related session state variables."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "chat_context" not in st.session_state:
        st.session_state.chat_context = ""
    
    if "context_docs" not in st.session_state:
        st.session_state.context_docs = []
    
    if "chat_ai_client" not in st.session_state:
        # Initialize with default client
        st.session_state.chat_ai_client = get_default_client()
    
    if "chat_settings" not in st.session_state:
        st.session_state.chat_settings = {
            "temperature": 0.7,
            "max_tokens": 1000,
            "use_context": True,
            "context_strategy": "relevant",  # 'relevant' or 'recent'
            "model": "llama2"  # Default model
        }

def render_chat_sidebar(knowledge_base: KnowledgeBase) -> None:
    """
    Render the sidebar for the chat interface.
    
    Args:
        knowledge_base: The application's knowledge base
    """
    st.sidebar.header("Chat Settings")
    
    # Model selection
    ai_client = st.session_state.chat_ai_client
    
    # Check if AI client is available
    if not ai_client.is_available():
        st.sidebar.warning("⚠️ AI service is not available. Please check your settings.")
    else:
        # Try to get available models
        try:
            available_models = ai_client.list_models()
            if available_models:
                selected_model = st.sidebar.selectbox(
                    "Model",
                    options=available_models,
                    index=available_models.index(st.session_state.chat_settings["model"]) if st.session_state.chat_settings["model"] in available_models else 0
                )
                
                if selected_model != st.session_state.chat_settings["model"]:
                    st.session_state.chat_settings["model"] = selected_model
                    st.rerun()
            else:
                st.sidebar.info("No models available from the AI service.")
        except Exception as e:
            logger.error(f"Error getting models: {str(e)}")
            st.sidebar.warning(f"Failed to retrieve models: {str(e)}")
    
    # Temperature setting
    temperature = st.sidebar.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.chat_settings["temperature"],
        step=0.1,
        help="Higher values make output more random, lower values more deterministic"
    )
    if temperature != st.session_state.chat_settings["temperature"]:
        st.session_state.chat_settings["temperature"] = temperature
    
    # Context settings
    st.sidebar.subheader("Knowledge Base Integration")
    
    use_context = st.sidebar.checkbox(
        "Use knowledge base for context",
        value=st.session_state.chat_settings["use_context"],
        help="When enabled, relevant content from your books will be provided to the AI"
    )
    if use_context != st.session_state.chat_settings["use_context"]:
        st.session_state.chat_settings["use_context"] = use_context
    
    if use_context:
        context_strategy = st.sidebar.radio(
            "Context strategy",
            options=["Relevant", "Recent"],
            index=0 if st.session_state.chat_settings["context_strategy"] == "relevant" else 1,
            help="Relevant: Use semantic search to find relevant passages. Recent: Use recently viewed or mentioned passages."
        )
        st.session_state.chat_settings["context_strategy"] = context_strategy.lower()
    
    # Display knowledge base stats
    kb_stats = knowledge_base.get_stats()
    st.sidebar.info(f"Documents in KB: {kb_stats.get('document_count', 0)}")
    st.sidebar.info(f"Chunks in KB: {kb_stats.get('chunk_count', 0)}")
    
    # Actions
    st.sidebar.subheader("Actions")
    
    if st.sidebar.button("Clear Chat History", key="clear_chat_btn"):
        st.session_state.chat_history = []
        st.session_state.context_docs = []
        st.session_state.chat_context = ""
        st.rerun()

def clear_chat_history():
    """Clear the chat history."""
    st.session_state.chat_history = []
    st.session_state.context_docs = []
    st.session_state.chat_context = ""
    st.rerun()

def get_context_from_kb(query: str, knowledge_base: KnowledgeBase, strategy: str = "relevant", limit: int = 5) -> str:
    """
    Get context from the knowledge base based on the specified strategy.
    
    Args:
        query: The user's query
        knowledge_base: The knowledge base to search
        strategy: The context retrieval strategy ('relevant' or 'recent')
        limit: Maximum number of results to include
        
    Returns:
        A string containing the relevant context
    """
    if strategy == "relevant":
        # Get relevant content using semantic search
        from knowledge_base.search import search_knowledge_base
        
        results = search_knowledge_base(
            query,
            knowledge_base,
            limit=limit
        )
        
        if not results:
            return ""
        
        # Store context docs for display
        st.session_state.context_docs = results
        
        # Format context for the AI
        context_parts = []
        for i, result in enumerate(results):
            doc_id = result["metadata"].get("document_id", "unknown")
            title = result["metadata"].get("title", "Untitled document")
            chunk_text = result["text"]
            
            context_parts.append(f"--- DOCUMENT {i+1}: {title} (ID: {doc_id}) ---\n{chunk_text}")
        
        return "\n\n".join(context_parts)
    
    elif strategy == "recent":
        # Use the most recently mentioned documents from the chat history
        # This would be more sophisticated in a real implementation,
        # potentially tracking which documents were recently viewed or mentioned
        from knowledge_base.search import get_recent_documents
        
        results = get_recent_documents(knowledge_base, limit=limit)
        
        if not results:
            return ""
        
        # Store context docs for display
        st.session_state.context_docs = results
        
        # Format context for the AI
        context_parts = []
        for i, result in enumerate(results):
            doc_id = result["metadata"].get("document_id", "unknown")
            title = result["metadata"].get("title", "Untitled document")
            chunk_text = result["text"]
            
            context_parts.append(f"--- DOCUMENT {i+1}: {title} (ID: {doc_id}) ---\n{chunk_text}")
        
        return "\n\n".join(context_parts)
    
    return ""

def render_chat_interface(knowledge_base: KnowledgeBase):
    """
    Render the chat interface.
    
    Args:
        knowledge_base: The application's knowledge base
    """
    # Initialize session state if needed
    initialize_chat_state()
    
    # Chat header
    st.title("Chat with AI")
    st.subheader("Ask questions about your documents and get AI-powered responses")
    
    # Check if knowledge base is empty
    kb_stats = knowledge_base.get_stats()
    if kb_stats.get("document_count", 0) == 0:
        st.warning("Your knowledge base is empty. Please add documents first.")
        
        if st.button("Go to Knowledge Management", key="chat_to_book_management_btn"):
            st.session_state.current_page = "book_management"
            st.rerun()
        
        return
    
    # Main layout with chat area and input
    chat_container = st.container()
    
    # Display existing chat messages
    with chat_container:
        for message in st.session_state.chat_history:
            role = message["role"]
            content = message["content"]
            
            with st.chat_message(role):
                st.write(content)
                
                # If this is an assistant message and it has context, show it in an expander
                if role == "assistant" and message.get("context_docs"):
                    with st.expander("View sources", expanded=False):
                        for i, doc in enumerate(message["context_docs"]):
                            st.markdown(f"**Source {i+1}**: {doc['metadata'].get('title', 'Untitled')}")
                            st.text(doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"])
    
    # Chat input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Add to chat history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Get context from knowledge base if enabled
        context = ""
        if st.session_state.chat_settings["use_context"]:
            with st.spinner("Searching knowledge base..."):
                context = get_context_from_kb(
                    user_input,
                    knowledge_base,
                    strategy=st.session_state.chat_settings["context_strategy"]
                )
                st.session_state.chat_context = context
        
        # Process with AI and get response
        with st.spinner("Thinking..."):
            try:
                # Prepare messages for the AI
                messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history]
                
                # Get the AI client
                ai_client = st.session_state.chat_ai_client
                
                # Check if AI client is available
                if not ai_client.is_available():
                    response = "AI service is not available. Please check your settings."
                    logger.error("AI service not available for chat response")
                else:
                    # Generate response
                    system_prompt = None
                    if st.session_state.chat_settings["use_context"] and context:
                        system_prompt = """You are a helpful assistant that answers questions about books and documents.
                        
When the user asks a question, consider the provided document contexts to give accurate, relevant information.
Always be truthful - if the information isn't in the documents, say so.
Cite specific documents when providing information from them.
Be concise but complete in your answers."""
                    
                    response = ai_client.generate_chat_response(
                        messages=messages,
                        system_prompt=system_prompt,
                        context=context,
                        model=st.session_state.chat_settings["model"],
                        temperature=st.session_state.chat_settings["temperature"]
                    )
                
                # Add to chat history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response,
                    "context_docs": st.session_state.context_docs if st.session_state.chat_settings["use_context"] else []
                })
                
                # Display assistant response
                with st.chat_message("assistant"):
                    st.write(response)
                    
                    # Show context sources if available
                    if st.session_state.chat_settings["use_context"] and st.session_state.context_docs:
                        with st.expander("View sources", expanded=False):
                            for i, doc in enumerate(st.session_state.context_docs):
                                st.markdown(f"**Source {i+1}**: {doc['metadata'].get('title', 'Untitled')}")
                                st.text(doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"])
            
            except Exception as e:
                error_msg = f"Error generating response: {str(e)}"
                logger.error(error_msg)
                st.error(error_msg)