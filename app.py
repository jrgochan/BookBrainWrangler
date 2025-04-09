"""
Book Knowledge AI - Main Application
A Streamlit-powered book management and knowledge extraction application 
that transforms documents into an interactive, AI-enhanced knowledge base.
"""

import os
import streamlit as st
from datetime import datetime

from utils.logger import get_logger
from document_processing import DocumentProcessor
from knowledge_base import KnowledgeBase

# Initialize logger
logger = get_logger(__name__)

# Set page config
st.set_page_config(
    page_title="Book Knowledge AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def init_session_state():
    """Initialize session state variables."""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.document_processor = DocumentProcessor()
        st.session_state.knowledge_base = KnowledgeBase()
        st.session_state.current_page = "home"
        st.session_state.sidebar_collapsed = False
        st.session_state.theme = "light"
        st.session_state.uploaded_files = []
        st.session_state.processing_results = {}
        st.session_state.search_results = []
        st.session_state.selected_document = None
        st.session_state.ai_model = "default"
        st.session_state.chat_history = []
        st.session_state.kb_enabled = True
        logger.info("Session state initialized")

# Render sidebar
def render_sidebar():
    """Render the application sidebar."""
    with st.sidebar:
        st.title("Book Knowledge AI")
        st.markdown("---")
        
        # Navigation
        st.header("Navigation")
        if st.button("📚 Home", key="sidebar_home_btn", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()
        
        if st.button("📄 Book Management", key="sidebar_book_mgmt_btn", use_container_width=True):
            st.session_state.current_page = "book_management"
            st.rerun()
        
        if st.button("🔍 Knowledge Base", key="sidebar_kb_btn", use_container_width=True):
            st.session_state.current_page = "knowledge_base"
            st.rerun()
        
        if st.button("💬 Chat with AI", key="sidebar_chat_btn", use_container_width=True):
            st.session_state.current_page = "chat"
            st.rerun()
        
        if st.button("⚙️ Settings", key="sidebar_settings_btn", use_container_width=True):
            st.session_state.current_page = "settings"
            st.rerun()
        
        st.markdown("---")
        
        # Status
        st.header("Status")
        kb_stats = st.session_state.knowledge_base.get_stats()
        st.info(f"Documents in KB: {kb_stats.get('document_count', 0)}")
        st.info(f"Total Chunks: {kb_stats.get('chunk_count', 0)}")
        
        # Footer
        st.markdown("---")
        st.markdown("📚 Book Knowledge AI")
        st.markdown(f"© {datetime.now().year}")

# Render home page
def render_home_page():
    """Render the home page."""
    st.title("Book Knowledge AI")
    st.subheader("Transform your books into an interactive AI knowledge base.")
    
    st.markdown("""
    ## Welcome to Book Knowledge AI!
    
    This application allows you to:
    
    - **Upload and process** books and documents
    - **Extract knowledge** from your document collection
    - **Search and explore** your knowledge base
    - **Chat with AI** about your documents
    
    Get started by uploading documents in the Book Management section.
    """)
    
    # Quick access buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Manage Documents", key="home_manage_docs_btn", use_container_width=True):
            st.session_state.current_page = "book_management"
            st.rerun()
    
    with col2:
        if st.button("🔍 Explore Knowledge Base", key="home_explore_kb_btn", use_container_width=True):
            st.session_state.current_page = "knowledge_base"
            st.rerun()
    
    with col3:
        if st.button("💬 Chat with AI", key="home_chat_btn", use_container_width=True):
            st.session_state.current_page = "chat"
            st.rerun()

# Render book management page
def render_book_management_page():
    """Render the book management page."""
    st.title("Book Management")
    st.subheader("Upload, view, and manage your documents")
    
    # Upload new document
    st.header("Upload New Document")
    uploaded_file = st.file_uploader(
        "Upload a PDF or DOCX file",
        type=["pdf", "docx"],
        key="book_upload"
    )
    
    if uploaded_file:
        st.session_state.uploaded_files.append(uploaded_file)
        
        # Process document
        with st.spinner("Processing document..."):
            try:
                # Save uploaded file
                file_path = st.session_state.document_processor.save_uploaded_file(uploaded_file)
                
                # Process document
                result = st.session_state.document_processor.process_document(
                    file_path,
                    include_images=True,
                    ocr_enabled=False
                )
                
                # Add to processing results
                st.session_state.processing_results[file_path] = result
                
                # Add to knowledge base
                doc_id = st.session_state.knowledge_base.generate_id()
                st.session_state.knowledge_base.add_document(
                    doc_id,
                    result["text"],
                    result["metadata"]
                )
                
                st.success(f"Document '{uploaded_file.name}' processed and added to knowledge base.")
                
                # Display document preview
                st.subheader("Document Preview")
                st.json(result["metadata"])
                
                with st.expander("Text Preview"):
                    st.text(result["text"][:1000] + "...")
                
            except Exception as e:
                st.error(f"Error processing document: {str(e)}")
                logger.error(f"Error processing document: {str(e)}")
    
    # List existing documents
    st.header("Existing Documents")
    documents = st.session_state.knowledge_base.list_documents()
    
    if not documents:
        st.info("No documents in the knowledge base yet. Upload a document to get started.")
    else:
        for doc in documents:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                doc_title = doc.get("metadata", {}).get("title", doc["id"])
                st.markdown(f"**{doc_title}**")
            
            with col2:
                if st.button("View", key=f"view_{doc['id']}"):
                    st.session_state.selected_document = doc["id"]
                    st.rerun()
            
            with col3:
                if st.button("Delete", key=f"delete_{doc['id']}"):
                    st.session_state.knowledge_base.delete_document(doc["id"])
                    st.success(f"Document '{doc_title}' deleted from knowledge base.")
                    st.rerun()
    
    # Display selected document
    if st.session_state.selected_document:
        st.header("Document Details")
        
        document = st.session_state.knowledge_base.get_document(st.session_state.selected_document)
        
        if document:
            # Display metadata
            st.subheader("Metadata")
            st.json(document["metadata"])
            
            # Display text
            st.subheader("Content")
            with st.expander("Show full text", expanded=False):
                st.text(document["text"])
            
            # Display chunks
            st.subheader("Chunks")
            for i, chunk in enumerate(document["chunks"]):
                with st.expander(f"Chunk {i+1}", expanded=False):
                    st.text(chunk)
        else:
            st.error("Document not found.")

# Render knowledge base page
def render_knowledge_base_page():
    """Render the knowledge base page."""
    st.title("Knowledge Base")
    st.subheader("Search and explore your knowledge base")
    
    # Search
    st.header("Search")
    query = st.text_input("Enter search query")
    
    if query:
        with st.spinner("Searching..."):
            from knowledge_base.search import search_knowledge_base
            
            results = search_knowledge_base(
                query,
                st.session_state.knowledge_base
            )
            
            st.session_state.search_results = results
    
    # Display search results
    if hasattr(st.session_state, "search_results") and st.session_state.search_results:
        st.header(f"Search Results ({len(st.session_state.search_results)})")
        
        for i, result in enumerate(st.session_state.search_results):
            with st.expander(f"Result {i+1} - Score: {result['score']:.2f}", expanded=i==0):
                st.markdown(f"**Document ID:** {result['metadata']['document_id']}")
                st.markdown(f"**Text:**")
                st.text(result["text"])
    
    # Knowledge base stats
    st.header("Knowledge Base Statistics")
    kb_stats = st.session_state.knowledge_base.get_stats()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Documents", kb_stats.get("document_count", 0))
    
    with col2:
        st.metric("Chunks", kb_stats.get("chunk_count", 0))

# Render chat page
def render_chat_page():
    """Render the chat page."""
    st.title("Chat with AI")
    st.subheader("Ask questions about your documents")
    
    # Check if knowledge base is empty
    kb_stats = st.session_state.knowledge_base.get_stats()
    if kb_stats.get("document_count", 0) == 0:
        st.warning("Your knowledge base is empty. Please add documents first.")
        
        if st.button("Go to Book Management", key="chat_to_book_management_btn"):
            st.session_state.current_page = "book_management"
            st.rerun()
        
        return
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        else:
            st.chat_message("assistant").write(message["content"])
    
    # Chat input
    user_input = st.chat_input("Ask a question about your documents")
    
    if user_input:
        # Add user message to chat history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Display user message
        st.chat_message("user").write(user_input)
        
        # Get AI response
        with st.spinner("Thinking..."):
            # Search knowledge base
            from knowledge_base.search import search_knowledge_base
            
            results = search_knowledge_base(
                user_input,
                st.session_state.knowledge_base,
                limit=5
            )
            
            # Simulate AI response
            if results:
                # Use the search results as context
                context = "\n\n".join([r["text"] for r in results])
                
                # Simple response based on results
                response = f"Based on your documents, I found the following information:\n\n{context[:500]}..."
            else:
                response = "I couldn't find any relevant information in your documents. Try a different question or add more documents to your knowledge base."
        
        # Add AI response to chat history
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response
        })
        
        # Display AI response
        st.chat_message("assistant").write(response)
        
        # Rerun to update UI
        st.rerun()

# Render settings page
def render_settings_page():
    """Render the settings page."""
    st.title("Settings")
    st.subheader("Configure application settings")
    
    # Knowledge base settings
    st.header("Knowledge Base Settings")
    
    kb_path = st.text_input(
        "Knowledge Base Path",
        value=st.session_state.knowledge_base.base_path,
        disabled=True
    )
    
    kb_collection = st.text_input(
        "Collection Name",
        value=st.session_state.knowledge_base.collection_name,
        disabled=True
    )
    
    # Reset knowledge base
    st.header("Reset Knowledge Base")
    st.warning("⚠️ This will delete all documents from your knowledge base. This action cannot be undone.")
    
    if st.button("Reset Knowledge Base", key="reset_kb_btn"):
        confirm = st.checkbox("I understand that this action cannot be undone", key="reset_kb_confirm_checkbox")
        
        if confirm and st.button("Confirm Reset", key="confirm_reset_btn"):
            st.session_state.knowledge_base.reset()
            st.success("Knowledge base has been reset.")
            st.rerun()
    
    # Application theme
    st.header("Application Theme")
    theme = st.selectbox(
        "Select Theme",
        ["Light", "Dark"],
        index=0 if st.session_state.theme == "light" else 1
    )
    
    if theme.lower() != st.session_state.theme:
        st.session_state.theme = theme.lower()
        st.success(f"Theme changed to {theme}.")

# Main application
def main():
    """Main application function."""
    try:
        # Initialize session state
        init_session_state()
        
        # Render sidebar
        render_sidebar()
        
        # Render page based on current_page
        if st.session_state.current_page == "home":
            render_home_page()
        elif st.session_state.current_page == "book_management":
            render_book_management_page()
        elif st.session_state.current_page == "knowledge_base":
            render_knowledge_base_page()
        elif st.session_state.current_page == "chat":
            render_chat_page()
        elif st.session_state.current_page == "settings":
            render_settings_page()
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        logger.error(f"Application error: {str(e)}")

if __name__ == "__main__":
    main()