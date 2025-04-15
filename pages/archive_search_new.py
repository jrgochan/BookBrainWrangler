"""
Internet Archive Search Page for Book Knowledge AI.

This page allows users to search for books on the Internet Archive
and import them into their local knowledge base.
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
CARDS_PER_ROW = 4
DEFAULT_COVER_URL = "https://archive.org/images/notfound.png"

# CSS Styles for the modern UI
def load_custom_css():
    """Load custom CSS styles for the Archive Search page."""
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
    
    /* Search form styling */
    .search-form {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        margin-bottom: 2rem;
    }
    
    /* Book result styling */
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
    
    /* Status badges */
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
    
    /* Processing console */
    .console-container {
        border-radius: 8px;
        margin-top: 1.5rem;
        position: relative;
    }
    
    /* Search box with icon */
    .search-container {
        position: relative;
    }
    
    .search-icon {
        position: absolute;
        left: 10px;
        top: 50%;
        transform: translateY(-50%);
        color: #94a3b8;
        z-index: 1;
    }
    
    .search-input {
        padding-left: 35px !important;
    }
    
    /* Modern tabs */
    .modern-tabs {
        display: flex;
        background-color: #f8fafc;
        border-radius: 8px;
        padding: 0.35rem;
        margin-bottom: 1.5rem;
    }
    
    .tab {
        flex: 1;
        text-align: center;
        padding: 0.5rem 1rem;
        cursor: pointer;
        border-radius: 6px;
        transition: all 0.2s;
        font-weight: 500;
    }
    
    .tab-active {
        background-color: white;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    /* Loading indicators */
    .loader {
        display: inline-block;
        width: 1rem;
        height: 1rem;
        border: 2px solid rgba(0, 0, 0, 0.1);
        border-top-color: #3498db;
        border-radius: 50%;
        animation: spin 1s ease-in-out infinite;
        margin-right: 0.5rem;
        vertical-align: middle;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    </style>
    """
    st.markdown(styles, unsafe_allow_html=True)
    
def archive_search_page(book_manager: BookManager, knowledge_base: KnowledgeBase):
    """
    Render the modernized Internet Archive search page.
    
    Args:
        book_manager: BookManager instance
        knowledge_base: KnowledgeBase instance
    """
    # Load custom CSS for modern UI
    load_custom_css()
    
    # Page header with improved visual design
    st.markdown("""
    <h1 style="color: #1e3a8a; margin-bottom: 0.5rem;">Internet Archive Search</h1>
    <p style="color: #64748b; font-size: 1.1rem; margin-bottom: 2rem;">
        Find and import books directly into your knowledge base
    </p>
    """, unsafe_allow_html=True)
    
    # About Internet Archive in a cleaner, modern expander
    with st.expander("About Internet Archive", expanded=False):
        st.markdown("""
        <div style="padding: 0.5rem 0; line-height: 1.6;">
            The <a href="https://archive.org" target="_blank" style="color: #3b82f6; text-decoration: none; font-weight: 500;">Internet Archive</a> 
            is a non-profit digital library offering free universal access to books, movies, music, and billions of archived web pages.
            <br><br>
            Use this page to search for books and add them directly to your knowledge base.
        </div>
        """, unsafe_allow_html=True)
    
    # Initialize the Internet Archive client
    archive_client = ArchiveOrgClient()
    
    # Initialize document processor for processing downloaded files
    document_processor = st.session_state.document_processor
    
    # Status console container for log messages
    if "console_collapsed" not in st.session_state:
        st.session_state.console_collapsed = True
        
    # Initialize processing logs in session state if needed
    if "archive_processing_logs" not in st.session_state:
        st.session_state.archive_processing_logs = []
    
    # Function to add a log entry
    def add_log(message, level="INFO"):
        log_entry = {
            'timestamp': datetime.now(),
            'level': level,
            'message': message
        }
        st.session_state.archive_processing_logs.append(log_entry)
        return log_entry

    # Create search form with modern design
    st.markdown('<div class="search-form">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### Search Books")
    
    with col2:
        # Toggle console visibility button
        if st.button("📋 Show Logs" if st.session_state.console_collapsed else "📋 Hide Logs"):
            st.session_state.console_collapsed = not st.session_state.console_collapsed
    
    # Create a form for the search
    with st.form(key="archive_search_form"):
        # Search input with icon
        st.markdown("""
        <div class="search-container">
            <div class="search-icon">🔍</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add custom CSS class to search input
        search_query = st.text_input(
            "Enter search terms",
            key="archive_search_query",
            placeholder="Example: 'machine learning' or 'philosophy'",
            help="Search by title, author, subject, or keywords"
        )
        
        # Create a more visually appealing layout for filters
        filter_cols = st.columns([1, 1, 1])
        
        with filter_cols[0]:
            max_results = st.number_input(
                "Maximum results", 
                min_value=10, 
                max_value=100, 
                value=24, 
                step=6,
                help="Maximum number of results to return"
            )
        
        with filter_cols[1]:
            media_type = st.selectbox(
                "Media type", 
                ["texts", "audio", "movies"], 
                index=0,
                help="Type of media to search for"
            )
            
        with filter_cols[2]:
            sort_by = st.selectbox(
                "Sort by", 
                [
                    "Most Popular", 
                    "Relevance", 
                    "Date Added",
                    "Title"
                ],
                help="Sort order for search results"
            )
        
        # Modern search button with icon
        submit_search = st.form_submit_button(
            "🔍 Search Internet Archive",
            type="primary",
            use_container_width=True
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Console/processing log display that can be toggled
    if not st.session_state.console_collapsed or st.session_state.archive_processing_logs:
        with st.container(border=True, height=300):
            st.markdown("""
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin: 0; padding: 0;">Processing Console</h3>
                <div>
                    <span style="color: #64748b; font-size: 0.9rem;">
                        Real-time processing information
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            render_console(
                st.session_state.archive_processing_logs, 
                max_height=220,
                auto_scroll=True,
                key="archive_console"
            )
            
            if st.session_state.archive_processing_logs:
                if st.button("Clear Console", key="clear_console_btn", type="secondary"):
                    st.session_state.archive_processing_logs = []
                    st.rerun()
    
    # Process search if button clicked
    if submit_search and search_query:
        add_log(f"Searching Internet Archive for: '{search_query}'")
        
        with st.spinner(f"Searching Internet Archive..."):
            # Map sort_by UI options to API parameters
            sort_mapping = {
                "Most Popular": "downloads desc",
                "Relevance": "",  # Default relevance sorting
                "Date Added": "addeddate desc",
                "Title": "title asc"
            }
            sort_param = sort_mapping[sort_by]
            
            try:
                results = archive_client.search_books(
                    search_query, 
                    max_results=max_results, 
                    media_type=media_type,
                    sort=sort_param
                )
                
                if not results:
                    st.warning(f"No results found for '{search_query}'")
                    add_log(f"No results found for '{search_query}'", "WARNING")
                else:
                    add_log(f"Found {len(results)} results for '{search_query}'", "SUCCESS")
                    st.session_state.archive_search_results = results
                    st.session_state.current_query = search_query  # Use a different key name than the input widget
                    
                    # Prefetch covers for all results to display in grid
                    add_log("Loading book covers...")
                    with st.spinner("Loading book covers..."):
                        # Retrieve covers for all books
                        covers = fetch_covers_for_results(results)
                        st.session_state.archive_search_covers = covers
                        add_log(f"Loaded {len(covers)} book covers", "SUCCESS")
            except Exception as e:
                error_message = f"Error searching Internet Archive: {str(e)}"
                st.error(error_message)
                add_log(error_message, "ERROR")
                logger.error(error_message, exc_info=True)
    
    # Display search results with modern UI if available
    if "archive_search_results" in st.session_state and st.session_state.archive_search_results:
        results = st.session_state.archive_search_results
        query = st.session_state.get("current_query", "")
        covers = st.session_state.get("archive_search_covers", {})
        
        # Results header with improved styling
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin: 1rem 0 1.5rem 0;">
            <h2 style="margin: 0; padding: 0;">Search Results</h2>
            <div style="background-color: #f1f5f9; padding: 0.4rem 0.8rem; border-radius: 6px;">
                <span style="color: #334155; font-size: 0.9rem;">
                    {len(results)} books found for "{query}"
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Batch operations bar
        with st.container(border=True):
            batch_cols = st.columns([3, 1])
            
            with batch_cols[0]:
                # Get count of selected books
                selected_count = len(st.session_state.get("selected_books", set()))
                
                if selected_count > 0:
                    st.markdown(f"""
                    <div style="padding: 0.5rem 0;">
                        <span class="badge badge-info">{selected_count} books selected</span>
                        <span style="color: #64748b; font-size: 0.9rem; margin-left: 0.5rem;">
                            Use checkboxes to select/deselect books
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="padding: 0.5rem 0;">
                        <span style="color: #64748b; font-size: 0.9rem;">
                            Use checkboxes to select individual books for batch operations
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            
            with batch_cols[1]:
                action_cols = st.columns([1, 1])
                
                with action_cols[0]:
                    if st.button("Download All", key="download_all_btn", use_container_width=True):
                        bulk_download_modal(
                            results, 
                            archive_client, 
                            document_processor, 
                            book_manager, 
                            knowledge_base, 
                            add_log
                        )
                
                with action_cols[1]:
                    # Enable button only if books are selected
                    if selected_count > 0:
                        if st.button("Download Selected", key="download_selected_btn", use_container_width=True):
                            # Get the selected results
                            selected_results = [r for r in results if r['identifier'] in st.session_state.get("selected_books", set())]
                            bulk_download_modal(
                                selected_results, 
                                archive_client, 
                                document_processor, 
                                book_manager, 
                                knowledge_base, 
                                add_log
                            )
                    else:
                        st.button("Download Selected", key="download_selected_btn_disabled", use_container_width=True, disabled=True)
        
        # Show results in a modern grid layout
        display_results_grid(
            results, 
            covers, 
            archive_client, 
            document_processor, 
            book_manager, 
            knowledge_base, 
            add_log
        )

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
    # Initialize session state for selection if not already done
    if "selected_books" not in st.session_state:
        st.session_state.selected_books = set()
    
    # Initialize format cache if not already done
    if "format_cache" not in st.session_state:
        st.session_state.format_cache = {}
    
    # Check if books exist in knowledge base
    existing_books = set()
    for result in results:
        try:
            if archive_client.check_book_exists_by_title_author(result.get('title', ''), result.get('author', '')):
                existing_books.add(result['identifier'])
        except Exception:
            # Skip books with missing title or author
            pass
    
    # Calculate number of columns based on screen width
    num_cols = min(CARDS_PER_ROW, len(results))
    if num_cols == 0:
        num_cols = 1
    
    # Create grid layout
    # Display books in rows with n columns
    for i in range(0, len(results), num_cols):
        cols = st.columns(num_cols)
        
        for j in range(num_cols):
            idx = i + j
            if idx < len(results):
                book = results[idx]
                book_id = book['identifier']
                
                with cols[j]:
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
    title = book.get('title', 'Unknown Title')
    author = book.get('author', 'Unknown Author')
    date = book.get('date', 'Unknown date')
    downloads = book.get('downloads', 0)
    
    # Create a container with our custom book-item class
    with st.container():
        st.markdown(f'<div class="book-item">', unsafe_allow_html=True)
        
        # Cover image container
        st.markdown(f'<div class="book-cover-container">', unsafe_allow_html=True)
        
        # Selection checkbox
        is_selected = book_id in st.session_state.selected_books
        if st.checkbox("", value=is_selected, key=f"select_grid_{book_id}", help="Select for batch download"):
            st.session_state.selected_books.add(book_id)
        else:
            if book_id in st.session_state.selected_books:
                st.session_state.selected_books.remove(book_id)
        
        # Cover image
        st.image(cover_url, use_column_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Book details
        st.markdown(f'<div class="book-details">', unsafe_allow_html=True)
        
        # Title truncated to fit
        truncated_title = title if len(title) < 50 else title[:47] + "..."
        st.markdown(f'<div class="book-title" title="{title}">{truncated_title}</div>', unsafe_allow_html=True)
        
        # Author
        truncated_author = author if len(author) < 40 else author[:37] + "..."
        st.markdown(f'<div class="book-author" title="{author}">{truncated_author}</div>', unsafe_allow_html=True)
        
        # Status badge if already in knowledge base
        if already_exists:
            st.markdown(f'<span class="badge badge-success">In Knowledge Base</span>', unsafe_allow_html=True)
        
        # Basic metadata
        metadata_parts = []
        if date:
            metadata_parts.append(f"{date}")
        if downloads:
            metadata_parts.append(f"{downloads:,} downloads")
        
        metadata_text = " · ".join(metadata_parts)
        if metadata_text:
            st.markdown(f'<div class="book-meta">{metadata_text}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Actions section
        st.markdown(f'<div class="book-actions">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # View on Archive.org
            preview_url = book.get('preview_url', f"https://archive.org/details/{book_id}")
            st.markdown(f"""
            <a href="{preview_url}" target="_blank" style="text-decoration: none; display: inline-block;">
                <small>View on Archive.org</small>
            </a>
            """, unsafe_allow_html=True)
        
        with col2:
            # Format selector and download button
            format_key = f"format_grid_{book_id}"
            
            # Load formats lazily
            if format_key not in st.session_state:
                try:
                    st.session_state[format_key] = archive_client.get_available_formats(book_id)
                except Exception:
                    st.session_state[format_key] = ["PDF", "TEXT"]
                    
            # Filter to preferred formats for readability
            formats = st.session_state[format_key]
            preferred_formats = [f for f in formats if f in ["PDF", "EPUB", "TEXT", "KINDLE"]]
            if not preferred_formats and formats:
                preferred_formats = formats[:3]  # Just show first 3 if no preferred formats
            
            # Add download button if formats available
            if preferred_formats:
                if st.button(
                    "Download", 
                    key=f"download_btn_grid_{book_id}",
                    help=f"Available formats: {', '.join(preferred_formats)}"
                ):
                    show_download_modal(
                        book,
                        preferred_formats[0] if preferred_formats else formats[0],
                        archive_client,
                        document_processor,
                        book_manager,
                        knowledge_base,
                        add_log
                    )
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def show_download_modal(
    book: Dict[str, Any],
    format_type: str,
    archive_client: ArchiveOrgClient,
    document_processor: DocumentProcessor,
    book_manager: BookManager,
    knowledge_base: KnowledgeBase,
    add_log
):
    """
    Show a modal dialog for downloading a single book.
    
    Args:
        book: Book metadata
        format_type: Format to download
        archive_client: ArchiveOrgClient instance
        document_processor: DocumentProcessor instance
        book_manager: BookManager instance 
        knowledge_base: KnowledgeBase instance
        add_log: Function to add log entries
    """
    book_id = book['identifier']
    title = book.get('title', 'Unknown')
    author = book.get('author', 'Unknown')
    
    # Create a container for the download dialog
    with st.container(border=True):
        st.markdown(f"""
        <h3 style="margin-top: 0;">Downloading Book</h3>
        <p style="margin-bottom: 1.5rem; color: #64748b;">
            <strong>Title:</strong> {title}<br>
            <strong>Author:</strong> {author}<br>
            <strong>Format:</strong> {format_type}
        </p>
        """, unsafe_allow_html=True)
        
        # Progress indicator
        progress_container = st.empty()
        with progress_container.container():
            progress_bar = st.progress(0, "Preparing to download...")
            status_text = st.empty()
            
        # Detailed log container
        log_container = st.empty()
        
        try:
            # Step 1: Download the file
            add_log(f"Starting download of '{title}' in {format_type} format")
            status_text.text("Downloading from Internet Archive...")
            
            # Download the file
            download_path = archive_client.download_book(
                book_id, 
                format_type, 
                lambda progress: progress_bar.progress(max(0.05, progress * 0.5))
            )
            
            if not download_path:
                add_log(f"Failed to download book: {title}", "ERROR")
                status_text.text("❌ Download failed")
                st.error("Download failed. Please try a different format or book.")
                return
            
            # Step 2: Process the downloaded file
            add_log(f"Downloaded book to {download_path}. Beginning processing...")
            status_text.text("Processing document...")
            progress_bar.progress(0.5, "Processing...")
            
            # Process the file
            result = document_processor.process_document(
                download_path,
                progress_callback=lambda progress, message: (
                    progress_bar.progress(0.5 + progress * 0.3),
                    add_log(message)
                )
            )
            
            # Step 3: Add to knowledge base
            add_log("Adding document to knowledge base...")
            status_text.text("Adding to knowledge base...")
            progress_bar.progress(0.8, "Adding to knowledge base...")
            
            # Generate document ID
            doc_id = knowledge_base.generate_id()
            
            # Add metadata from book and extracted metadata
            metadata = {
                "title": title,
                "author": author,
                "source": "Internet Archive",
                "identifier": book_id,
                "date_added": datetime.now().isoformat(),
            }
            
            # Add additional metadata from processing if available
            if result and "metadata" in result:
                extracted_metadata = result.get("metadata", {})
                if "title" in extracted_metadata and not extracted_metadata["title"].strip():
                    extracted_metadata.pop("title")  # Remove empty titles
                if "author" in extracted_metadata and not extracted_metadata["author"].strip():
                    extracted_metadata.pop("author")  # Remove empty authors
                    
                # Merge with preference for book metadata for title/author
                for key, value in extracted_metadata.items():
                    if key not in metadata or not metadata[key]:
                        metadata[key] = value
            
            # Add to knowledge base
            knowledge_base.add_document(
                doc_id,
                result.get("text", ""),
                metadata
            )
            
            # Step 4: Finalize
            add_log(f"Successfully added '{title}' to knowledge base", "SUCCESS")
            progress_bar.progress(1.0, "Complete!")
            status_text.text("✅ Successfully added to knowledge base")
            
            st.success(f"Added '{title}' to your knowledge base.")
            
        except Exception as e:
            error_message = f"Error processing book: {str(e)}"
            add_log(error_message, "ERROR")
            status_text.text("❌ Error occurred")
            progress_bar.progress(1.0, "Failed")
            st.error(error_message)
            logger.error(error_message, exc_info=True)
            
        finally:
            # Display detailed log
            with log_container.container():
                # Get only logs for this specific operation
                # For simplicity we'll just show the 10 most recent logs
                recent_logs = st.session_state.archive_processing_logs[-10:]
                render_console(recent_logs, max_height=150, title="Processing Details", auto_scroll=True)

def bulk_download_modal(
    results: List[Dict[str, Any]],
    archive_client: ArchiveOrgClient,
    document_processor: DocumentProcessor,
    book_manager: BookManager,
    knowledge_base: KnowledgeBase,
    add_log
):
    """
    Show a modal dialog for batch downloading multiple books.
    
    Args:
        results: List of book results to download
        archive_client: ArchiveOrgClient instance
        document_processor: DocumentProcessor instance
        book_manager: BookManager instance
        knowledge_base: KnowledgeBase instance
        add_log: Function to add log entries
    """
    if not results:
        st.warning("No books selected for download")
        return
    
    # Create a modern dialog for bulk download
    with st.container(border=True):
        st.markdown(f"""
        <h3 style="margin-top: 0;">Batch Download</h3>
        <p style="margin-bottom: 1rem; color: #64748b;">
            Downloading {len(results)} books from Internet Archive
        </p>
        """, unsafe_allow_html=True)
        
        # Progress tracking
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        progress_bar = progress_placeholder.progress(0, "Preparing batch download...")
        
        # Initialize tracking variables
        total_books = len(results)
        completed = 0
        failed = 0
        
        # Show book list
        books_container = st.container(border=True, height=200)
        with books_container:
            st.markdown("### Books to Download")
            
            for idx, book in enumerate(results, 1):
                title = book.get('title', 'Unknown Title')
                author = book.get('author', 'Unknown Author')
                
                st.markdown(f"{idx}. **{title}** by {author}")
        
        # Start download process
        add_log(f"Starting batch download of {total_books} books")
        
        # Process each book
        for idx, book in enumerate(results, 1):
            book_id = book['identifier']
            title = book.get('title', 'Unknown')
            author = book.get('author', 'Unknown')
            
            # Get preferred format
            try:
                formats = archive_client.get_available_formats(book_id)
                preferred_formats = [f for f in formats if f in ["PDF", "EPUB", "TEXT", "KINDLE"]]
                format_type = preferred_formats[0] if preferred_formats else formats[0] if formats else "PDF"
            except Exception:
                format_type = "PDF"  # Default to PDF if can't get formats
            
            try:
                # Update status
                current_percent = (idx - 1) / total_books
                progress_bar.progress(current_percent, f"Processing book {idx} of {total_books}")
                status_placeholder.text(f"Downloading '{title}' ({format_type})...")
                
                add_log(f"Processing book {idx}/{total_books}: '{title}' by {author}")
                
                # Download the file
                download_path = archive_client.download_book(
                    book_id, 
                    format_type=format_type
                )
                
                if not download_path:
                    add_log(f"Failed to download '{title}'", "ERROR")
                    failed += 1
                    continue
                
                # Process the document
                add_log(f"Processing '{title}'...")
                result = document_processor.process_document(download_path)
                
                # Add to knowledge base
                doc_id = knowledge_base.generate_id()
                
                # Create metadata
                metadata = {
                    "title": title,
                    "author": author,
                    "source": "Internet Archive",
                    "identifier": book_id,
                    "date_added": datetime.now().isoformat(),
                }
                
                # Add to knowledge base
                knowledge_base.add_document(
                    doc_id,
                    result.get("text", ""),
                    metadata
                )
                
                add_log(f"Successfully added '{title}' to knowledge base", "SUCCESS")
                completed += 1
                
                # Update progress
                current_percent = idx / total_books
                progress_bar.progress(current_percent, f"Completed {idx} of {total_books}")
                status_placeholder.text(f"Completed: {completed}, Failed: {failed}")
                
            except Exception as e:
                error_message = f"Error processing '{title}': {str(e)}"
                add_log(error_message, "ERROR")
                logger.error(error_message, exc_info=True)
                failed += 1
        
        # Final status
        progress_bar.progress(1.0, "Complete")
        
        if failed == 0:
            status_placeholder.success(f"Successfully downloaded and processed all {completed} books")
        else:
            status_placeholder.warning(f"Completed: {completed}, Failed: {failed}")
            
        add_log(f"Batch download completed: {completed} successful, {failed} failed", 
                "SUCCESS" if failed == 0 else "WARNING")

def render_archive_search_page():
    """
    Main function to render the archive search page.
    """
    from book_manager import BookManager
    book_manager = BookManager()
    
    # Render the new, modernized archive search page
    archive_search_page(book_manager, st.session_state.knowledge_base)