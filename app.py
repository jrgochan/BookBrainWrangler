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
        
        if st.button("📄 Knowledge Management", key="sidebar_book_mgmt_btn", use_container_width=True):
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
    
    Get started by uploading documents in the Knowledge Management section.
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

# Render knowledge management page
def render_book_management_page():
    """Render the knowledge management page."""
    # Import the console component
    from components.console import render_console, create_processing_logger
    import pandas as pd
    
    st.title("Knowledge Management")
    st.subheader("Upload, view, and manage your documents")
    
    # Initialize processing logs in session state if needed
    if "processing_logs" not in st.session_state:
        st.session_state.processing_logs = []
    
    # Function to add a log entry
    def add_log(message, level="INFO"):
        st.session_state.processing_logs.append({
            'timestamp': datetime.now(),
            'level': level,
            'message': message
        })
    
    # Upload new document
    st.header("Upload New Document")
    uploaded_file = st.file_uploader(
        "Upload a PDF or DOCX file",
        type=["pdf", "docx"],
        key="book_upload"
    )
    
    if uploaded_file:
        # Add process button for better control
        if st.button("Process Document", key="process_document_btn"):
            # Clear previous logs
            st.session_state.processing_logs = []
            
            # Add initial log
            add_log(f"Starting processing of file: {uploaded_file.name}")
            
            # Create console logger and processing callback
            progress_callback = create_processing_logger(st.session_state.processing_logs)
            
            # Display the console (will update in real-time)
            console_placeholder = st.empty()
            
            # Create progress bar placeholder
            progress_bar_placeholder = st.empty()
            progress_percent = 0
            
            try:
                # Save uploaded file
                add_log("Saving uploaded file...")
                file_path = st.session_state.document_processor.save_uploaded_file(uploaded_file)
                add_log(f"File saved to: {file_path}", "SUCCESS")
                
                # Update console
                with console_placeholder.container():
                    render_console(st.session_state.processing_logs, title="Processing Log")
                
                # Initialize progress bar at 10%
                progress_percent = 10
                progress_bar_placeholder.progress(progress_percent / 100, f"Processing: {progress_percent}% complete")
                
                # Process document with detailed logging
                add_log(f"Starting document processing: {file_path}")
                
                # Create a wrapper for the progress callback to update both the logs and progress bar
                def combined_progress_callback(progress, message):
                    # Update logs with the original callback
                    progress_callback(progress, message)
                    
                    # Update progress bar (scale from 10% to 90%)
                    nonlocal progress_percent
                    progress_percent = 10 + int(progress * 80)
                    progress_bar_placeholder.progress(progress_percent / 100, f"Processing: {progress_percent}% complete")
                
                # Process document with combined progress callback
                result = st.session_state.document_processor.process_document(
                    file_path,
                    include_images=True,
                    ocr_enabled=False,
                    progress_callback=combined_progress_callback
                )
                
                # Update console after processing
                with console_placeholder.container():
                    render_console(st.session_state.processing_logs, title="Processing Log")
                
                # Set progress to 90%
                progress_percent = 90
                progress_bar_placeholder.progress(progress_percent / 100, f"Processing: {progress_percent}% complete")
                    
                # Add processing completion log
                add_log(f"Document processing complete: {len(result.get('text', ''))} characters of text extracted", "SUCCESS")
                
                if 'images' in result and result['images']:
                    add_log(f"Extracted {len(result['images'])} images from document", "SUCCESS")
                
                # Add metadata extraction details
                if 'metadata' in result and result['metadata']:
                    metadata = result['metadata']
                    add_log(f"Extracted metadata: Title='{metadata.get('title', 'Unknown')}', Author='{metadata.get('author', 'Unknown')}'")
                
                # Add to processing results
                st.session_state.processing_results[file_path] = result
                add_log("Document added to processing results")
                
                # Add to knowledge base - update progress to 95%
                progress_percent = 95
                progress_bar_placeholder.progress(progress_percent / 100, f"Processing: {progress_percent}% complete")
                
                add_log("Generating document ID...")
                doc_id = st.session_state.knowledge_base.generate_id()
                add_log(f"Document ID generated: {doc_id}")
                
                add_log("Adding document to knowledge base...")
                st.session_state.knowledge_base.add_document(
                    doc_id,
                    result.get("text", ""),
                    result.get("metadata", {})
                )
                add_log("Document successfully added to knowledge base", "SUCCESS")
                
                # Complete progress bar - 100%
                progress_percent = 100
                progress_bar_placeholder.progress(progress_percent / 100, "Processing complete!")
                
                # Update console one last time
                with console_placeholder.container():
                    render_console(st.session_state.processing_logs, title="Processing Log")
                
                # Final success message
                st.success(f"Document '{uploaded_file.name}' processed and added to knowledge base.")
                
                # Display document preview
                st.subheader("Document Preview")
                
                # Show metadata
                if "metadata" in result and result["metadata"]:
                    st.json(result["metadata"])
                else:
                    st.info("No metadata extracted from document")
                
                # Show text preview
                if "text" in result and result["text"]:
                    with st.expander("Text Preview"):
                        preview_text = result["text"][:1000] + "..." if len(result["text"]) > 1000 else result["text"]
                        st.text(preview_text)
                
                # Show image preview if available
                if "images" in result and result["images"]:
                    with st.expander(f"Images ({len(result['images'])})"):
                        cols = st.columns(3)
                        for i, img in enumerate(result["images"]):
                            if "data" in img:
                                col_idx = i % 3
                                with cols[col_idx]:
                                    st.image(f"data:image/{img.get('format', 'jpeg')};base64,{img['data']}", 
                                            caption=f"Page {img.get('page', i+1)}",
                                            width=200)
                
            except Exception as e:
                error_msg = f"Error processing document: {str(e)}"
                add_log(error_msg, "ERROR")
                st.error(error_msg)
                logger.error(error_msg)
                
                # Update console to show the error
                with console_placeholder.container():
                    render_console(st.session_state.processing_logs, title="Processing Log")
        
        # Show processing log even when not actively processing
        if st.session_state.processing_logs:
            st.subheader("Processing Log")
            render_console(st.session_state.processing_logs)
    
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
        # Import the document details page
        from pages.document_details import document_details_page
        
        # Render the document details page
        document_details_page(
            document_id=st.session_state.selected_document,
            knowledge_base=st.session_state.knowledge_base,
            on_back=lambda: setattr(st.session_state, 'selected_document', None)
        )

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
        
        if st.button("Go to Knowledge Management", key="chat_to_book_management_btn"):
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
    # Import and load the settings page module
    from pages.settings import settings_page
    settings_page()

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
