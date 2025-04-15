"""
Internet Archive Search Page for Book Knowledge AI - Enhanced Modern UI

This page allows users to search for books on the Internet Archive
and import them into their local knowledge base, with an improved modern interface.
"""

import os
import time
import hashlib
import streamlit as st
from typing import Dict, List, Any, Optional, Tuple
import concurrent.futures
import threading
import asyncio
import base64
from io import BytesIO
from datetime import datetime

from utils.logger import get_logger
from utils.archive_integration import ArchiveOrgClient
from utils.ui_helpers import show_progress_bar, create_download_link
from book_manager import BookManager
from document_processing import DocumentProcessor
from knowledge_base import KnowledgeBase
from components.console import render_console, create_processing_logger

# Initialize logger
logger = get_logger(__name__)

# Constants for UI
CARD_HEIGHT = 280
CARDS_PER_ROW = 3
DEFAULT_COVER_URL = "https://archive.org/images/notfound.png"

def load_custom_css():
    """Load custom CSS styles for the modern Archive Search page."""
    styles = """
    <style>
    /* Modern card styling */
    .modern-card {
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s, box-shadow 0.2s;
        background-color: white;
    }
    .modern-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
    }
    .search-form {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        margin-bottom: 2rem;
    }
    .book-item {
        background-color: white;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        transition: box-shadow 0.2s;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .book-item:hover {
        box-shadow: 0 4px 15px rgba(30, 136, 229, 0.15);
    }
    .book-cover-container {
        position: relative;
        padding-top: 0;
        overflow: hidden;
        text-align: center;
        background-color: #f5f8fa;
    }
    .book-details {
        padding: 0.8rem;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
    }
    .book-title {
        font-size: 1rem;
        font-weight: bold;
        margin-bottom: 0.4rem;
        color: #2c3e50;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }
    .book-author {
        font-size: 0.8rem;
        color: #546e7a;
        margin-bottom: 0.4rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .book-meta {
        font-size: 0.75rem;
        color: #78909c;
        margin-bottom: 0.6rem;
    }
    .book-actions {
        padding: 0.6rem;
        border-top: 1px solid #f1f1f1;
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        margin-top: auto;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 4px;
        margin-right: 0.5rem;
    }
    .badge-success {
        background-color: #e3fcef;
        color: #0c7742;
    }
    .badge-info {
        background-color: #e1f5fe;
        color: #0277bd;
    }
    .badge-warning {
        background-color: #fff8e1;
        color: #ff8f00;
    }
    .console-container {
        border-radius: 8px;
        margin-top: 1.5rem;
        position: relative;
    }
    .search-container {
        position: relative;
    }
    .search-icon {
        position: absolute;
        left: 10px;
    }
    .bulk-download-title {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 15px;
        color: #1E88E5;
    }
    .book-count-info {
        padding: 8px 15px;
        border-radius: 4px;
        margin: 10px 0;
        font-size: 16px;
    }
    .existing-books-list {
        max-height: 200px;
        overflow-y: auto;
        margin-top: 5px;
        padding: 10px;
        background-color: #f8f9fa;
        border-radius: 4px;
    }
    .book-list-item {
        padding: 5px 0;
        border-bottom: 1px solid #e0e0e0;
    }
    .download-options {
        margin: 20px 0;
        padding: 15px;
        background-color: #f9f9f9;
        border-radius: 6px;
        border: 1px solid #eaeaea;
    }
    /* Progress indicator styling */
    .step-container {
        display: flex;
        margin-bottom: 20px;
    }
    .step {
        flex: 1;
        text-align: center;
        position: relative;
        font-size: 14px;
    }
    .step-circle {
        width: 30px;
        height: 30px;
        line-height: 30px;
        border-radius: 50%;
        background-color: #e0e0e0;
        color: #757575;
        margin: 0 auto 8px;
        position: relative;
        z-index: 2;
    }
    .step-active .step-circle {
        background-color: #2196F3;
        color: white;
    }
    .step-complete .step-circle {
        background-color: #4CAF50;
        color: white;
    }
    .step-line {
        position: absolute;
        top: 15px;
        left: 50%;
        width: 100%;
        height: 2px;
        background-color: #e0e0e0;
        z-index: 1;
    }
    .step-complete .step-line {
        background-color: #4CAF50;
    }
    /* End custom CSS */
    </style>
    """
    st.markdown(styles, unsafe_allow_html=True)

def render_archive_search_page():
    """
    Render the Internet Archive search page with modern UI.
    """
    # Load custom CSS
    load_custom_css()
    
    st.title("Internet Archive Book Search")
    
    with st.expander("About Internet Archive", expanded=False):
        st.markdown("""
        The [Internet Archive](https://archive.org) is a non-profit digital library offering free universal access to books,
        movies, music, and billions of archived web pages.
        
        Use this page to search for books and add them directly to your knowledge base.
        """)
    
    # Access the necessary components from session state
    book_manager = st.session_state.book_manager
    knowledge_base = st.session_state.knowledge_base
    
    # Initialize the Internet Archive client
    archive_client = ArchiveOrgClient()
    
    # Initialize document processor for processing downloaded files
    document_processor = st.session_state.document_processor
    
    # Initialize processing logs in session state if needed
    if "archive_processing_logs" not in st.session_state:
        st.session_state.archive_processing_logs = []
    
    # Function to add a log entry
    def add_log(message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.archive_processing_logs.append({
            'timestamp': time.time(),
            'formatted_time': timestamp,
            'level': level,
            'message': message
        })
    
    # Modern search form with improved styling
    st.markdown('<div class="search-form">', unsafe_allow_html=True)
    with st.form(key="archive_search_form"):
        st.subheader("Search for Books")
        
        search_query = st.text_input("Search query", 
                                    placeholder="Enter title, author, subject...",
                                    key="archive_search_query")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            max_results = st.number_input("Maximum results", 
                                         min_value=10, 
                                         max_value=100, 
                                         value=24, 
                                         step=6)
        
        with col2:
            media_type = st.selectbox("Media type", 
                                     ["texts", "audio", "movies"], 
                                     index=0)
                
        with col3:
            sort_by = st.selectbox("Sort by", [
                "Most Popular", 
                "Relevance", 
                "Date Added",
                "Title"
            ])
        
        submit_search = st.form_submit_button("Search Internet Archive", 
                                            type="primary",
                                            use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Process search if button clicked
    if submit_search and search_query:
        with st.spinner(f"Searching Internet Archive for '{search_query}'..."):
            # Map sort_by UI options to API parameters
            sort_mapping = {
                "Most Popular": "downloads desc",
                "Relevance": "",  # Default relevance sorting
                "Date Added": "addeddate desc",
                "Title": "title asc"
            }
            sort_param = sort_mapping[sort_by]
            
            results = archive_client.search_books(
                search_query, 
                max_results=max_results, 
                media_type=media_type,
                sort=sort_param
            )
        
        if not results:
            st.warning(f"No results found for '{search_query}'")
        else:
            st.success(f"Found {len(results)} results for '{search_query}'")
            st.session_state.archive_search_results = results
            st.session_state.current_query = search_query  # Use a different key name than the input widget
            
            # Prefetch covers for all results to display in grid
            with st.spinner("Loading book covers..."):
                # Retrieve covers for all books
                covers = fetch_covers_for_results(results)
                st.session_state.archive_search_covers = covers
    
    # Display search results if available
    if "archive_search_results" in st.session_state and st.session_state.archive_search_results:
        results = st.session_state.archive_search_results
        query = st.session_state.get("current_query", "")
        covers = st.session_state.get("archive_search_covers", {})
        
        # Results header with actions
        st.markdown(f"""
        <div class="modern-card">
            <h3>Search Results for '{query}'</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(f"Showing {len(results)} results")
        
        with col2:
            if st.button("Download All", key="download_all_btn", type="primary"):
                bulk_download_modal(
                    results, 
                    archive_client, 
                    document_processor, 
                    book_manager, 
                    knowledge_base, 
                    add_log
                )
        
        # Display books in a grid layout
        display_results_grid(
            results, 
            covers, 
            archive_client, 
            document_processor, 
            book_manager, 
            knowledge_base, 
            add_log
        )
    
    # Display processing logs
    if st.session_state.archive_processing_logs:
        with st.container(border=True):
            st.subheader("Processing Log")
            
            # Modern console with improved styling
            st.markdown('<div class="console-container">', unsafe_allow_html=True)
            render_console(st.session_state.archive_processing_logs, title="", auto_scroll=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Clear logs button
            if st.button("Clear Logs", key="clear_logs_btn"):
                st.session_state.archive_processing_logs = []
                st.rerun()

def fetch_covers_for_results(results: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Fetch cover images for all search results.
    
    Args:
        results: List of search results
        
    Returns:
        Dictionary mapping identifier to cover URL
    """
    covers = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_id = {
            executor.submit(get_book_cover, result['identifier']): result['identifier']
            for result in results
        }
        
        for future in concurrent.futures.as_completed(future_to_id):
            identifier = future_to_id[future]
            try:
                cover_url = future.result()
                covers[identifier] = cover_url
            except Exception:
                covers[identifier] = DEFAULT_COVER_URL
    
    return covers

def get_book_cover(identifier: str) -> str:
    """
    Get the cover URL for a book.
    
    Args:
        identifier: Internet Archive identifier
        
    Returns:
        URL to book cover image
    """
    # Try different cover image options (ordered by preference)
    cover_options = [
        f"https://archive.org/services/img/{identifier}",
        f"https://archive.org/download/{identifier}/page/cover_w800.jpg",
        f"https://archive.org/download/{identifier}/page/cover_medium.jpg",
        f"https://archive.org/download/{identifier}/page/cover_small.jpg",
        f"https://archive.org/download/{identifier}/page/cover_thumb.jpg"
    ]
    
    for url in cover_options:
        try:
            import requests
            response = requests.head(url, timeout=2)
            if response.status_code == 200:
                return url
        except Exception:
            continue
    
    # If no cover found, return default
    return DEFAULT_COVER_URL

def display_results_grid(
    results: List[Dict[str, Any]],
    covers: Dict[str, str],
    archive_client: ArchiveOrgClient,
    document_processor: DocumentProcessor,
    book_manager: BookManager,
    knowledge_base: KnowledgeBase,
    add_log
):
    """
    Display search results in a modern grid layout.
    
    Args:
        results: List of search results
        covers: Dictionary of cover images
        archive_client: ArchiveOrgClient instance
        document_processor: DocumentProcessor instance
        book_manager: BookManager instance
        knowledge_base: KnowledgeBase instance
        add_log: Function to add log entries
    """
    # Cache for format information to avoid repeated API calls
    if "format_cache" not in st.session_state:
        st.session_state.format_cache = {}
    
    # Checkboxes for batch selection
    if "selected_books" not in st.session_state:
        st.session_state.selected_books = set()
    
    # If there are selected books, show batch download option
    if st.session_state.selected_books:
        st.info(f"{len(st.session_state.selected_books)} books selected")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.caption("Use checkboxes to select/deselect books")
        
        with col2:
            if st.button("Download Selected", key="download_selected_btn"):
                # Get the selected results
                selected_results = [r for r in results if r['identifier'] in st.session_state.selected_books]
                bulk_download_modal(
                    selected_results, 
                    archive_client, 
                    document_processor, 
                    book_manager, 
                    knowledge_base, 
                    add_log
                )
    
    # Check if any book exists in the knowledge base
    existing_books = set()
    for result in results:
        if archive_client.check_book_exists_by_title_author(result['title'], result['author']):
            existing_books.add(result['identifier'])
    
    # Display books in a grid layout
    # Calculate number of columns based on screen size
    # We'll create rows of 'cols_per_row' columns
    cols_per_row = 3
    
    # Process results in groups of cols_per_row
    for i in range(0, len(results), cols_per_row):
        cols = st.columns(cols_per_row)
        
        # For each column in this row
        for j in range(cols_per_row):
            if i + j < len(results):
                book = results[i + j]
                book_id = book['identifier']
                
                with cols[j]:
                    # Display book card
                    display_book_card(
                        book,
                        covers.get(book_id, DEFAULT_COVER_URL),
                        book_id in existing_books,
                        archive_client,
                        document_processor,
                        book_manager,
                        knowledge_base,
                        add_log
                    )

def display_book_card(
    book: Dict[str, Any],
    cover_url: str,
    already_exists: bool,
    archive_client: ArchiveOrgClient,
    document_processor: DocumentProcessor,
    book_manager: BookManager,
    knowledge_base: KnowledgeBase,
    add_log
):
    """
    Display a book as a modern card in the grid layout.
    
    Args:
        book: Book metadata dictionary
        cover_url: URL to book cover image
        already_exists: Whether the book already exists in the knowledge base
        archive_client: ArchiveOrgClient instance
        document_processor: DocumentProcessor instance
        book_manager: BookManager instance
        knowledge_base: KnowledgeBase instance
        add_log: Function to add log entries
    """
    book_id = book['identifier']
    title = book['title']
    author = book['author']
    date = book.get('date', 'Unknown date')
    downloads = book.get('downloads', 0)
    
    # Card container
    st.markdown(f'<div class="book-item">', unsafe_allow_html=True)
    
    # Cover image
    st.markdown(f'<div class="book-cover-container">', unsafe_allow_html=True)
    
    # Selection checkbox
    is_selected = book_id in st.session_state.selected_books
    if st.checkbox("", value=is_selected, key=f"select_{book_id}"):
        st.session_state.selected_books.add(book_id)
    else:
        if book_id in st.session_state.selected_books:
            st.session_state.selected_books.remove(book_id)
    
    # Display cover image
    st.image(cover_url, use_column_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Book details
    st.markdown(f'<div class="book-details">', unsafe_allow_html=True)
    
    # Title with tooltip for full title
    st.markdown(f'<div class="book-title" title="{title}">{title}</div>', unsafe_allow_html=True)
    
    # Author
    st.markdown(f'<div class="book-author">{author}</div>', unsafe_allow_html=True)
    
    # Date and downloads
    metadata_html = f"""
    <div class="book-meta">
        {date} • {f'{downloads:,} downloads' if downloads else 'Downloads N/A'}
    </div>
    """
    st.markdown(metadata_html, unsafe_allow_html=True)
    
    # Status badge for existing books
    if already_exists:
        st.markdown('<span class="badge badge-info">Already in library</span>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Actions section
    st.markdown(f'<div class="book-actions">', unsafe_allow_html=True)
    
    # Preview link
    preview_url = f"https://archive.org/details/{book_id}"
    st.markdown(f'<a href="{preview_url}" target="_blank" style="text-decoration:none; font-size:0.8rem;">Preview ↗</a>', unsafe_allow_html=True)
    
    # Download button
    if st.button("Download", key=f"download_{book_id}"):
        # Load formats if not cached
        format_key = f"formats_{book_id}"
        if format_key not in st.session_state:
            with st.spinner("Loading formats..."):
                st.session_state[format_key] = archive_client.get_available_formats(book_id)
        
        formats = st.session_state[format_key]
        
        if not formats:
            st.error("No download formats available")
        else:
            # Find PDF format if available (as a preferred default)
            pdf_format = next((f for f in formats if f['format'].lower() == 'pdf'), None)
            format_to_use = pdf_format if pdf_format else formats[0]
            
            download_and_process_book(
                book,
                format_to_use,
                archive_client,
                document_processor,
                book_manager,
                knowledge_base,
                add_log
            )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Close the book item container
    st.markdown('</div>', unsafe_allow_html=True)

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
    # Create a full-width container that looks like a dialog
    st.markdown("---")
    st.subheader("Processing Book")
    dialog_container = st.container(border=True)
    with dialog_container:
        # Display book information at the top
        st.subheader(f"Processing: {book_info['title']}")
        st.caption(f"by {book_info['author']}")
        
        # Display format information
        st.info(f"Format: {format_info['format'].upper()} - {format_info['name']} ({int(int(format_info['size'])/1024)} KB)")
        
        # Create a multi-step progress indicator
        steps = [
            "Download", 
            "Extract Text", 
            "Add to Database", 
            "Index in Knowledge Base"
        ]
        
        # Initialize progress
        current_step = 0
        
        # Step 1: Download file
        render_progress_steps(steps, current_step)
        
        download_status = st.empty()
        download_progress = st.progress(0)
        download_status.text("Starting download...")
        
        try:
            # Log starting the download
            add_log(f"Starting download of '{book_info['title']}' in {format_info['format']} format")
            
            # Update UI
            for i in range(10):
                time.sleep(0.1)  # Simulate progress 
                download_progress.progress(i / 10)
                download_status.text(f"Downloading... ({i*10}%)")
            
            # Download the book
            local_path = archive_client.download_book(
                book_info['identifier'],
                format_info['url'],
                book_info['title'],
                book_info['author']
            )
            
            # Update UI
            download_progress.progress(1.0)
            download_status.text("Download complete!")
            
            if not local_path:
                add_log(f"Download failed for: {book_info['title']}", "ERROR")
                st.error("Download failed. Please try again.")
                return
            
            # Show file details
            file_size = os.path.getsize(local_path) / 1024  # KB
            st.caption(f"Downloaded to: {local_path} ({file_size:.1f} KB)")
            
            # Calculate file hash for duplicate detection
            file_hash = archive_client.calculate_file_hash(local_path)
            
            # Check if this exact file is already in the database
            existing_book_id = archive_client.check_hash_exists(file_hash)
            if existing_book_id:
                add_log(f"File already exists in knowledge base: {book_info['title']}", "WARNING")
                st.warning("This exact file already exists in your knowledge base.")
                return
            
            # Step 2: Process document
            current_step = 1
            render_progress_steps(steps, current_step)
            
            process_status = st.empty()
            process_status.text("Processing document...")
            
            add_log(f"Processing document: {local_path}", "INFO")
            result = document_processor.process_document(
                local_path,
                include_images=True,
                ocr_enabled=False
            )
            
            # Extract content stats
            content = result.get("text", "")
            word_count = len(content.split()) if content else 0
            page_count = result.get("page_count", 0)
            
            process_status.text(f"Processing complete! Extracted {word_count} words from {page_count} pages.")
            
            # Step 3: Add to database
            current_step = 2
            render_progress_steps(steps, current_step)
            
            db_status = st.empty()
            db_status.text("Adding to book database...")
            
            # Extract categories from subjects
            categories = []
            if book_info['subjects'] and isinstance(book_info['subjects'], list):
                # Limit to 5 categories max
                categories = book_info['subjects'][:5]
            
            # Add to book manager
            book_id = book_manager.add_book(
                book_info['title'],
                book_info['author'],
                categories,
                file_path=local_path,
                content=content
            )
            
            # Store the file hash for future duplicate detection
            if book_id is not None:
                archive_client.store_file_hash(book_id, file_hash)
                db_status.text(f"Added to database with ID: {book_id}")
            else:
                db_status.text("Failed to add to database")
                add_log(f"Failed to add to database: {book_info['title']}", "ERROR")
                st.error("Failed to add book to database")
                return
            
            # Step 4: Add to knowledge base
            current_step = 3
            render_progress_steps(steps, current_step)
            
            kb_status = st.empty()
            kb_status.text("Adding to knowledge base...")
            
            # Create document ID
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
                content,
                metadata
            )
            
            kb_status.text("Successfully added to knowledge base")
            add_log(f"Successfully added to knowledge base: {book_info['title']}", "SUCCESS")
            
            # Show success message
            st.success(f"Book '{book_info['title']}' has been successfully added to your knowledge base.")
            
        except Exception as e:
            add_log(f"Error processing {book_info['title']}: {str(e)}", "ERROR")
            st.error(f"Error: {str(e)}")

def render_progress_steps(steps, current_step):
    """
    Render a horizontal progress indicator for multi-step processes.
    
    Args:
        steps: List of step names
        current_step: Current step index (0-based)
    """
    step_html = '<div class="step-container">'
    
    for i, step in enumerate(steps):
        # Determine step state
        if i < current_step:
            state = "step-complete"
        elif i == current_step:
            state = "step-active"
        else:
            state = ""
        
        # Add step line (except for the first step)
        if i > 0:
            line_class = "step-line"
            if i <= current_step:
                line_class += " step-complete"
            step_html += f'<div class="{line_class}"></div>'
        
        # Add step circle and label
        step_html += f"""
        <div class="step {state}">
            <div class="step-circle">{i+1}</div>
            <div class="step-label">{step}</div>
        </div>
        """
    
    step_html += '</div>'
    st.markdown(step_html, unsafe_allow_html=True)

def bulk_download_modal(
    books: List[Dict[str, Any]],
    archive_client: ArchiveOrgClient,
    document_processor: DocumentProcessor,
    book_manager: BookManager,
    knowledge_base: KnowledgeBase,
    add_log
):
    """
    Show a modal for bulk downloading multiple books with improved visual layout.
    
    Args:
        books: List of books to download
        archive_client: ArchiveOrgClient instance
        document_processor: DocumentProcessor instance
        book_manager: BookManager instance
        knowledge_base: KnowledgeBase instance
        add_log: Function to add log entries
    """
    # Check if any books already exist in knowledge base
    existing_books = []
    for book in books:
        if archive_client.check_book_exists_by_title_author(book['title'], book['author']):
            existing_books.append(book)
    
    with st.container(border=True):
        # Use HTML for better title formatting
        st.markdown('<div class="bulk-download-title">Bulk Download Books</div>', unsafe_allow_html=True)
        
        # Show book count with enhanced styling
        st.markdown(f"""
        <div class="book-count-info" style="background-color: #e3f2fd; color: #1565c0;">
            <strong>📚 Selected:</strong> {len(books)} books for download
        </div>
        """, unsafe_allow_html=True)
        
        # Show existing books with improved styling
        if existing_books:
            st.markdown(f"""
            <div class="book-count-info" style="background-color: #fff8e1; color: #ff8f00;">
                <strong>⚠️ Note:</strong> {len(existing_books)} books already exist in your knowledge base
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("View already existing books"):
                st.markdown('<div class="existing-books-list">', unsafe_allow_html=True)
                for book in existing_books:
                    st.markdown(f"""
                    <div class="book-list-item">
                        <strong>{book['title']}</strong><br/>
                        <small>by {book['author']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Options section with better organization
        st.markdown('<div class="download-options">', unsafe_allow_html=True)
        st.markdown('#### Download Options', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            skip_existing = st.checkbox("Skip existing books", value=True, 
                                       help="If checked, books already in your knowledge base will be skipped")
        
        with col2:
            preferred_format = st.selectbox(
                "Preferred format",
                ["PDF", "EPUB", "TXT", "DOCX"],
                index=0,
                help="The system will try to download this format first, but will fall back to available formats if needed"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Additional information before starting
        st.info("""
        **Processing Information:**
        - Each book will be downloaded from the Internet Archive
        - Text will be extracted and added to your knowledge base
        - This process may take several minutes depending on file sizes
        """)
        
        # Start download button with better styling
        st.markdown('<div style="margin-top: 20px; text-align: center;">', unsafe_allow_html=True)
        if st.button("Start Downloading", key="start_bulk_download", type="primary", use_container_width=True):
            # Process each book
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_books = len(books)
            success_count = 0
            error_count = 0
            skipped_count = 0
            
            for i, book in enumerate(books):
                # Update progress
                progress = (i / total_books)
                book_title = book['title']
                status_text.text(f"Processing {i+1}/{total_books}: {book_title}")
                progress_bar.progress(progress)
                
                # Check if book exists and should be skipped
                if skip_existing and archive_client.check_book_exists_by_title_author(book['title'], book['author']):
                    add_log(f"Skipping existing book: {book_title}", "INFO")
                    skipped_count += 1
                    continue
                
                try:
                    # Get available formats
                    formats = archive_client.get_available_formats(book['identifier'])
                    
                    if not formats:
                        add_log(f"No supported formats available for: {book_title}", "WARNING")
                        error_count += 1
                        continue
                    
                    # Find the preferred format
                    preferred_format_lower = preferred_format.lower()
                    format_info = next(
                        (f for f in formats if f['format'].lower() == preferred_format_lower), 
                        formats[0]  # Default to first format if preferred not available
                    )
                    
                    # Download and process
                    add_log(f"Downloading {book_title} in {format_info['format']} format", "INFO")
                    
                    # Download book
                    local_path = archive_client.download_book(
                        book['identifier'],
                        format_info['url'],
                        book['title'],
                        book['author']
                    )
                    
                    if not local_path:
                        add_log(f"Download failed for: {book_title}", "ERROR")
                        error_count += 1
                        continue
                    
                    # Calculate file hash for duplicate detection
                    file_hash = archive_client.calculate_file_hash(local_path)
                    
                    # Check if this exact file is already in the database
                    existing_book_id = archive_client.check_hash_exists(file_hash)
                    if existing_book_id:
                        add_log(f"File already exists in knowledge base: {book_title}", "WARNING")
                        skipped_count += 1
                        continue
                    
                    # Process document
                    add_log(f"Processing document: {local_path}", "INFO")
                    result = document_processor.process_document(
                        local_path,
                        include_images=True,
                        ocr_enabled=False
                    )
                    
                    # Extract categories from subjects
                    categories = []
                    if book['subjects'] and isinstance(book['subjects'], list):
                        # Limit to 5 categories max
                        categories = book['subjects'][:5]
                    
                    # Add to book manager
                    book_id = book_manager.add_book(
                        book['title'],
                        book['author'],
                        categories,
                        file_path=local_path,
                        content=result.get("text", "")
                    )
                    
                    # Store the file hash for future duplicate detection
                    if book_id is not None:
                        archive_client.store_file_hash(book_id, file_hash)
                    
                    # Add to knowledge base
                    doc_id = knowledge_base.generate_id()
                    
                    # Create metadata dictionary
                    metadata = {
                        "title": book['title'],
                        "author": book['author'],
                        "source": "Internet Archive",
                        "identifier": book['identifier'],
                        "date": book.get('date', 'Unknown'),
                        "categories": categories,
                        "book_id": book_id
                    }
                    
                    # Add to knowledge base
                    knowledge_base.add_document(
                        doc_id,
                        result.get("text", ""),
                        metadata
                    )
                    
                    add_log(f"Successfully added to knowledge base: {book_title}", "SUCCESS")
                    success_count += 1
                    
                except Exception as e:
                    add_log(f"Error processing {book_title}: {str(e)}", "ERROR")
                    error_count += 1
            
            # Final progress update
            progress_bar.progress(1.0)
            status_text.text("Download complete!")
            
            # Summary message
            st.success(f"Bulk download complete: {success_count} added, {skipped_count} skipped, {error_count} failed")