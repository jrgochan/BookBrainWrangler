"""
Internet Archive Search Page for Book Knowledge AI.

This page allows users to search for books on the Internet Archive
and import them into their local knowledge base.
"""

import os
import time
import streamlit as st
from typing import Dict, List, Any, Optional, Tuple

from utils.logger import get_logger
from utils.archive_integration import ArchiveOrgClient
from book_manager import BookManager
from document_processing import DocumentProcessor
from knowledge_base import KnowledgeBase
from components.console import render_console, create_processing_logger

# Initialize logger
logger = get_logger(__name__)

def archive_search_page(book_manager: BookManager, knowledge_base: KnowledgeBase):
    """
    Render the Internet Archive search page.
    
    Args:
        book_manager: BookManager instance
        knowledge_base: KnowledgeBase instance
    """
    st.title("Internet Archive Book Search")
    st.markdown("""
    Search for books on the Internet Archive and add them to your knowledge base.
    
    The [Internet Archive](https://archive.org) is a non-profit digital library offering free universal access to books,
    movies, music, and billions of archived web pages.
    """)
    
    # Initialize the Internet Archive client
    archive_client = ArchiveOrgClient()
    
    # Initialize document processor for processing downloaded files
    document_processor = st.session_state.document_processor
    
    # Initialize processing logs in session state if needed
    if "archive_processing_logs" not in st.session_state:
        st.session_state.archive_processing_logs = []
    
    # Function to add a log entry
    def add_log(message, level="INFO"):
        st.session_state.archive_processing_logs.append({
            'timestamp': time.time(),
            'level': level,
            'message': message
        })
    
    # Search form
    with st.form(key="archive_search_form"):
        search_query = st.text_input("Search for books", key="archive_search_query")
        col1, col2 = st.columns(2)
        
        with col1:
            max_results = st.number_input("Maximum results", min_value=10, max_value=100, value=25, step=5)
        
        with col2:
            media_type = st.selectbox("Media type", ["texts", "audio", "movies"], index=0)
        
        submit_search = st.form_submit_button("Search Internet Archive")
    
    # Process search if button clicked
    if submit_search and search_query:
        with st.spinner(f"Searching Internet Archive for '{search_query}'..."):
            results = archive_client.search_books(search_query, max_results=max_results, media_type=media_type)
        
        if not results:
            st.warning(f"No results found for '{search_query}'")
        else:
            st.success(f"Found {len(results)} results for '{search_query}'")
            st.session_state.archive_search_results = results
    
    # Display search results if available
    if "archive_search_results" in st.session_state and st.session_state.archive_search_results:
        st.subheader("Search Results")
        
        # Check if we need to show a "show more" button
        if "show_result_details" not in st.session_state:
            st.session_state.show_result_details = {}
        
        for i, result in enumerate(st.session_state.archive_search_results):
            with st.expander(f"{result['title']} by {result['author']}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Basic info
                    st.markdown(f"**Author:** {result['author']}")
                    st.markdown(f"**Date:** {result['date']}")
                    
                    # Show/hide details button
                    result_id = result['identifier']
                    if result_id not in st.session_state.show_result_details:
                        st.session_state.show_result_details[result_id] = False
                    
                    if st.button("Show Details", key=f"show_details_{result_id}"):
                        st.session_state.show_result_details[result_id] = True
                    
                    if st.session_state.show_result_details[result_id]:
                        # Subjects/categories
                        if result['subjects']:
                            st.markdown("**Subjects:**")
                            subjects_str = ", ".join(result['subjects'][:10])  # Limit to first 10
                            st.markdown(f"{subjects_str}")
                        
                        # Description
                        if isinstance(result['description'], str):
                            st.markdown("**Description:**")
                            st.markdown(result['description'][:500] + "..." if len(result['description']) > 500 else result['description'])
                        
                        # Available formats (fetched on demand)
                        st.markdown("**Available Formats:**")
                        with st.spinner("Loading available formats..."):
                            formats = archive_client.get_available_formats(result['identifier'])
                        
                        if not formats:
                            st.info("No supported formats available for this book.")
                        else:
                            # Create a selector for available formats
                            format_options = [f"{f['format'].upper()} - {f['name']} ({int(f['size']/1024)} KB)" for f in formats]
                            selected_format = st.selectbox("Select format to download", format_options, key=f"format_{result_id}")
                            
                            # Get the selected format information
                            selected_index = format_options.index(selected_format)
                            format_info = formats[selected_index]
                            
                            # Check if book already exists by title and author
                            if archive_client.check_book_exists_by_title_author(result['title'], result['author']):
                                st.warning("⚠️ This book is already in your knowledge base.")
                            
                            # Download button
                            if st.button("Download and Process", key=f"download_{result_id}"):
                                download_and_process_book(
                                    result, 
                                    format_info,
                                    archive_client,
                                    document_processor,
                                    book_manager,
                                    knowledge_base,
                                    add_log
                                )
                
                with col2:
                    # Preview link and stats
                    st.markdown(f"[View on Archive.org]({result['preview_url']})")
                    st.markdown(f"Downloads: {result['downloads']:,}")
    
    # Display processing logs
    if st.session_state.archive_processing_logs:
        st.subheader("Processing Log")
        render_console(st.session_state.archive_processing_logs, title="Processing Log")

def download_and_process_book(
    book_info: Dict[str, Any],
    format_info: Dict[str, Any],
    archive_client: ArchiveOrgClient,
    document_processor: DocumentProcessor,
    book_manager: BookManager,
    knowledge_base: KnowledgeBase,
    add_log
):
    """
    Download and process a book from the Internet Archive.
    
    Args:
        book_info: Book metadata
        format_info: Information about the format to download
        archive_client: ArchiveOrgClient instance
        document_processor: DocumentProcessor instance  
        book_manager: BookManager instance
        knowledge_base: KnowledgeBase instance
        add_log: Function to add log entries
    """
    # Create placeholders for progress feedback
    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    
    try:
        # Set initial status
        status_placeholder.info("Starting download...")
        progress_bar.progress(5)
        add_log(f"Starting download of '{book_info['title']}' in {format_info['format']} format")
        
        # Download the file
        status_placeholder.info(f"Downloading {format_info['name']}...")
        local_path = archive_client.download_book(
            book_info['identifier'],
            format_info['url'],
            book_info['title'],
            book_info['author']
        )
        
        if not local_path:
            status_placeholder.error("Download failed!")
            add_log("Download failed", "ERROR")
            return
        
        progress_bar.progress(30)
        add_log(f"Download complete: {local_path}", "SUCCESS")
        
        # Calculate file hash
        status_placeholder.info("Calculating file hash for duplicate detection...")
        file_hash = archive_client.calculate_file_hash(local_path)
        
        # Check if this exact file is already in the database
        existing_book_id = archive_client.check_hash_exists(file_hash)
        if existing_book_id:
            progress_bar.progress(100)
            status_placeholder.warning(f"This exact file is already in your knowledge base (Book ID: {existing_book_id}).")
            add_log(f"File already exists in knowledge base with Book ID: {existing_book_id}", "WARNING")
            return
        
        progress_bar.progress(40)
        
        # Process the document
        status_placeholder.info("Processing document...")
        add_log(f"Processing document: {local_path}")
        
        # Create a progress callback for document processing
        def process_progress_callback(progress, message):
            # Map the 0-1 progress to 40-80% of our overall progress
            overall_progress = 40 + int(progress * 40)
            progress_bar.progress(overall_progress)
            add_log(message)
        
        # Process the document
        result = document_processor.process_document(
            local_path,
            include_images=True,
            ocr_enabled=False,
            progress_callback=process_progress_callback
        )
        
        progress_bar.progress(80)
        add_log(f"Document processing complete: {len(result.get('text', ''))} characters extracted", "SUCCESS")
        
        # Extract categories from subjects
        categories = []
        if book_info['subjects'] and isinstance(book_info['subjects'], list):
            # Limit to 5 categories max
            categories = book_info['subjects'][:5]
        
        # Add to book manager
        status_placeholder.info("Adding to book manager...")
        book_id = book_manager.add_book(
            book_info['title'],
            book_info['author'],
            categories,
            file_path=local_path,
            content=result.get("text", "")
        )
        
        # Store the file hash for future duplicate detection
        archive_client.store_file_hash(book_id, file_hash)
        
        progress_bar.progress(90)
        add_log(f"Book added to manager with ID: {book_id}", "SUCCESS")
        
        # Add to knowledge base
        status_placeholder.info("Adding to knowledge base...")
        
        # Generate document ID
        doc_id = knowledge_base.generate_id()
        
        # Create metadata dictionary
        metadata = {
            "title": book_info['title'],
            "author": book_info['author'],
            "source": "Internet Archive",
            "identifier": book_info['identifier'],
            "date": book_info.get('date', 'Unknown'),
            "categories": categories,
            "book_id": book_id
        }
        
        # Add to knowledge base
        knowledge_base.add_document(
            doc_id,
            result.get("text", ""),
            metadata
        )
        
        progress_bar.progress(100)
        add_log(f"Document added to knowledge base with ID: {doc_id}", "SUCCESS")
        
        # Final success message
        status_placeholder.success(f"Book '{book_info['title']}' successfully added to your knowledge base!")
        
    except Exception as e:
        error_msg = f"Error processing book: {str(e)}"
        status_placeholder.error(error_msg)
        add_log(error_msg, "ERROR")
        logger.error(error_msg)
        
def render_archive_search_page():
    """
    Main function to render the archive search page.
    """
    from book_manager import BookManager
    book_manager = BookManager()
    
    archive_search_page(book_manager, st.session_state.knowledge_base)