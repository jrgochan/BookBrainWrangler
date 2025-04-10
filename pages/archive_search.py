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
CARD_HEIGHT = 320
CARDS_PER_ROW = 3
DEFAULT_COVER_URL = "https://archive.org/images/notfound.png"

def archive_search_page(book_manager: BookManager, knowledge_base: KnowledgeBase):
    """
    Render the Internet Archive search page.
    
    Args:
        book_manager: BookManager instance
        knowledge_base: KnowledgeBase instance
    """
    st.title("Internet Archive Book Search")
    
    with st.expander("About Internet Archive", expanded=False):
        st.markdown("""
        The [Internet Archive](https://archive.org) is a non-profit digital library offering free universal access to books,
        movies, music, and billions of archived web pages.
        
        Use this page to search for books and add them directly to your knowledge base.
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
        col1, col2, col3 = st.columns(3)
        
        with col1:
            max_results = st.number_input("Maximum results", min_value=10, max_value=100, value=24, step=6)
        
        with col2:
            media_type = st.selectbox("Media type", ["texts", "audio", "movies"], index=0)
            
        with col3:
            sort_by = st.selectbox("Sort by", [
                "Most Popular", 
                "Relevance", 
                "Date Added",
                "Title"
            ])
        
        submit_search = st.form_submit_button("Search Internet Archive")
    
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
        
        # Actions for bulk download
        st.subheader(f"Search Results for '{query}'")
        
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
        
        # Show results in a grid of cards
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
        st.subheader("Processing Log")
        render_console(st.session_state.archive_processing_logs, title="Processing Log")
        
        # Clear logs button
        if st.button("Clear Logs"):
            st.session_state.archive_processing_logs = []
            st.experimental_rerun()

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
    Display search results in a grid layout.
    
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
    
    # Display grid of cards
    num_cols = CARDS_PER_ROW
    rows = [results[i:i+num_cols] for i in range(0, len(results), num_cols)]
    
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
    
    # Display rows of cards
    for row in rows:
        cols = st.columns(num_cols)
        
        for i, book in enumerate(row):
            with cols[i]:
                # Get book data
                book_id = book['identifier']
                title = book['title']
                author = book['author']
                
                # Display book card with cover
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
    Display a card for a single book.
    
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
    
    # Card container (adjust height to accommodate different elements)
    with st.container(border=True):
        # Selection checkbox (for batch operations)
        col1, col2 = st.columns([5, 1])
        with col1:
            st.caption(date)
        with col2:
            is_selected = book_id in st.session_state.selected_books
            if st.checkbox("", value=is_selected, key=f"select_{book_id}"):
                st.session_state.selected_books.add(book_id)
            else:
                if book_id in st.session_state.selected_books:
                    st.session_state.selected_books.remove(book_id)
        
        # Cover image
        st.image(cover_url, use_container_width=True)
        
        # Title and author (truncate if too long)
        max_title_len = 50
        truncated_title = title[:max_title_len] + "..." if len(title) > max_title_len else title
        st.markdown(f"**{truncated_title}**")
        st.caption(f"by {author}")
        
        # Link to Internet Archive
        preview_url = book.get('preview_url', f"https://archive.org/details/{book_id}")
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f"[View on Archive.org]({preview_url})")
        with col2:
            if book.get('downloads'):
                st.caption(f"{book['downloads']:,} downloads")
        
        # Status indicator if the book already exists in knowledge base
        if already_exists:
            st.info("✓ In Knowledge Base", icon="✓")
        
        # Download button with format selection
        with st.expander("Download Options"):
            # Lazy-load format information when expanding
            format_key = f"formats_{book_id}"
            
            if format_key not in st.session_state:
                with st.spinner("Loading formats..."):
                    formats = archive_client.get_available_formats(book_id)
                    st.session_state[format_key] = formats
            else:
                formats = st.session_state[format_key]
            
            if not formats:
                st.info("No supported formats available")
            else:
                # Sort formats by preference (PDF first, then EPUB, etc.)
                format_preference = {"pdf": 0, "epub": 1, "txt": 2, "docx": 3, "doc": 4}
                formats.sort(key=lambda f: format_preference.get(f['format'].lower(), 999))
                
                # Format options for select box
                format_options = [f"{f['format'].upper()} - {f['name']} ({int(int(f['size'])/1024)} KB)" for f in formats]
                selected_format = st.selectbox(
                    "Format", 
                    format_options, 
                    key=f"format_{book_id}"
                )
                
                # Get the selected format information
                selected_index = format_options.index(selected_format)
                format_info = formats[selected_index]
                
                # Download buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Add to Knowledge Base", key=f"add_kb_{book_id}"):
                        download_and_process_book(
                            book, 
                            format_info,
                            archive_client,
                            document_processor,
                            book_manager,
                            knowledge_base,
                            add_log
                        )
                
                with col2:
                    # Direct download link
                    direct_url = format_info['url']
                    file_name = format_info['name']
                    st.markdown(f"[Direct Download]({direct_url})", unsafe_allow_html=True)

def bulk_download_modal(
    books: List[Dict[str, Any]],
    archive_client: ArchiveOrgClient,
    document_processor: DocumentProcessor,
    book_manager: BookManager,
    knowledge_base: KnowledgeBase,
    add_log
):
    """
    Show a modal for bulk downloading multiple books.
    
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
        st.subheader("Bulk Download")
        
        # Show book count and list
        st.info(f"Preparing to download {len(books)} books")
        
        if existing_books:
            st.warning(f"{len(existing_books)} books already exist in your knowledge base")
            
            with st.expander("Show already existing books"):
                for book in existing_books:
                    st.write(f"• {book['title']} by {book['author']}")
        
        # Options for download
        col1, col2 = st.columns(2)
        
        with col1:
            skip_existing = st.checkbox("Skip existing books", value=True)
        
        with col2:
            preferred_format = st.selectbox(
                "Preferred format",
                ["PDF", "EPUB", "TXT", "DOCX"],
                index=0
            )
        
        # Start download button
        if st.button("Start Downloading", key="start_bulk_download", type="primary"):
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
    # Create a container that looks like a dialog
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
            "Hash Calculation", 
            "Document Processing", 
            "Adding to Book Manager", 
            "Adding to Knowledge Base"
        ]
        
        # Display steps as a progress list
        steps_container = st.container()
        with steps_container:
            step_statuses = {step: "⬜" for step in steps}
            step_details = {step: st.empty() for step in steps}
            step_progress = {step: st.empty() for step in steps}
        
        # Main progress bar
        overall_progress = st.progress(0, "Starting process...")
        
        # Current operation status
        status_text = st.empty()
        
        # Create a section for logs (using a container instead of an expander to avoid nesting)
        st.markdown("**Detailed Log**")
        log_container = st.container()
            
        try:
            # STEP 1: DOWNLOAD
            # Update step status
            step_statuses["Download"] = "🔄"
            update_steps_display(steps_container, steps, step_statuses, step_details)
            
            status_text.text("Downloading file...")
            add_log(f"Starting download of '{book_info['title']}' in {format_info['format']} format")
            
            # Create a progress indicator for the download
            download_progress = step_progress["Download"]
            download_progress.progress(0, "Starting download...")
            
            # Track download start time for calculation
            download_start_time = time.time()
            
            # Mock download progress updates
            def download_tracker():
                while not hasattr(download_tracker, 'complete'):
                    elapsed = time.time() - download_start_time
                    # Simulate progress based on file size
                    file_size_kb = int(format_info['size']) / 1024
                    # Estimate download speed (arbitrary for simulation)
                    speed_kb_per_sec = 500
                    estimated_time = file_size_kb / speed_kb_per_sec
                    progress = min(0.99, elapsed / estimated_time)
                    
                    if progress < 0.99:
                        download_progress.progress(progress, f"Downloading: {int(progress * 100)}%")
                        overall_progress.progress(progress * 0.3, f"Downloading: {int(progress * 100)}%")
                        time.sleep(0.1)
                    else:
                        break
            
            # Start download tracker in a thread
            import threading
            tracker_thread = threading.Thread(target=download_tracker)
            tracker_thread.daemon = True
            tracker_thread.start()
            
            # Perform the actual download
            local_path = archive_client.download_book(
                book_info['identifier'],
                format_info['url'],
                book_info['title'],
                book_info['author']
            )
            
            # Set tracker complete flag
            download_tracker.complete = True
            
            # Wait for tracker thread to finish
            tracker_thread.join(timeout=0.5)
            
            if not local_path:
                download_progress.progress(1.0, "Download failed!")
                overall_progress.progress(0.3, "Process failed")
                status_text.error("Download failed!")
                add_log("Download failed", "ERROR")
                step_statuses["Download"] = "❌"
                update_steps_display(steps_container, steps, step_statuses, step_details)
                return
            
            # Update download progress to complete
            download_progress.progress(1.0, "Download complete!")
            overall_progress.progress(0.3, "Download complete")
            step_statuses["Download"] = "✅"
            step_details["Download"].info(f"File saved to: {os.path.basename(local_path)}")
            update_steps_display(steps_container, steps, step_statuses, step_details)
            add_log(f"Download complete: {local_path}", "SUCCESS")
            
            # STEP 2: HASH CALCULATION
            status_text.text("Calculating file hash for duplicate detection...")
            step_statuses["Hash Calculation"] = "🔄"
            update_steps_display(steps_container, steps, step_statuses, step_details)
            
            hash_progress = step_progress["Hash Calculation"]
            hash_progress.progress(0, "Calculating hash...")
            
            # Calculate file hash with visual progress updates
            file_size = os.path.getsize(local_path)
            chunk_size = 4096
            chunks_total = file_size / chunk_size
            
            hash_md5 = hashlib.md5()
            with open(local_path, "rb") as f:
                i = 0
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hash_md5.update(chunk)
                    i += 1
                    if i % 100 == 0:  # Update progress every 100 chunks
                        progress = min(0.99, i / chunks_total)
                        hash_progress.progress(progress, "Calculating hash...")
                        overall_progress.progress(0.3 + progress * 0.05, "Calculating hash...")
            
            file_hash = hash_md5.hexdigest()
            
            # Update hash progress to complete
            hash_progress.progress(1.0, "Hash calculation complete!")
            overall_progress.progress(0.35, "Hash calculation complete")
            
            # Check if this exact file is already in the database
            existing_book_id = archive_client.check_hash_exists(file_hash)
            if existing_book_id:
                step_statuses["Hash Calculation"] = "⚠️"
                step_details["Hash Calculation"].warning(f"File already exists in knowledge base (Book ID: {existing_book_id})")
                update_steps_display(steps_container, steps, step_statuses, step_details)
                overall_progress.progress(1.0, "Process complete - duplicate detected")
                status_text.warning("Duplicate book detected!")
                add_log(f"File already exists in knowledge base with Book ID: {existing_book_id}", "WARNING")
                return
            
            step_statuses["Hash Calculation"] = "✅"
            step_details["Hash Calculation"].info(f"Hash: {file_hash[:8]}...{file_hash[-8:]}")
            update_steps_display(steps_container, steps, step_statuses, step_details)
            
            # STEP 3: DOCUMENT PROCESSING
            status_text.text("Processing document...")
            step_statuses["Document Processing"] = "🔄"
            update_steps_display(steps_container, steps, step_statuses, step_details)
            add_log(f"Processing document: {local_path}")
            
            processing_progress = step_progress["Document Processing"]
            processing_progress.progress(0, "Starting document processing...")
            
            # Create a progress callback for document processing
            def process_progress_callback(progress, message):
                processing_progress.progress(progress, message)
                overall_progress.progress(0.35 + progress * 0.35, message)
                add_log(message)
            
            # Process the document
            result = document_processor.process_document(
                local_path,
                include_images=True,
                ocr_enabled=False,
                progress_callback=process_progress_callback
            )
            
            # Update processing progress to complete
            processing_progress.progress(1.0, "Processing complete!")
            overall_progress.progress(0.7, "Document processing complete")
            step_statuses["Document Processing"] = "✅"
            
            # Add processing details
            extracted_chars = len(result.get("text", ""))
            images_count = len(result.get("images", []))
            step_details["Document Processing"].info(f"Extracted {extracted_chars:,} characters and {images_count} images")
            update_steps_display(steps_container, steps, step_statuses, step_details)
            add_log(f"Document processing complete: {extracted_chars} characters extracted", "SUCCESS")
            
            # Extract categories from subjects
            categories = []
            if book_info['subjects'] and isinstance(book_info['subjects'], list):
                # Limit to 5 categories max
                categories = book_info['subjects'][:5]
            
            # STEP 4: ADDING TO BOOK MANAGER
            status_text.text("Adding to book manager...")
            step_statuses["Adding to Book Manager"] = "🔄"
            update_steps_display(steps_container, steps, step_statuses, step_details)
            
            manager_progress = step_progress["Adding to Book Manager"]
            manager_progress.progress(0.5, "Adding to book manager...")
            overall_progress.progress(0.75, "Adding to book manager...")
            
            # Add to book manager
            book_id = book_manager.add_book(
                book_info['title'],
                book_info['author'],
                categories,
                file_path=local_path,
                content=result.get("text", "")
            )
            
            # Store the file hash for future duplicate detection
            if book_id is not None:  # Make sure book_id is not None before storing hash
                archive_client.store_file_hash(book_id, file_hash)
                
                manager_progress.progress(1.0, "Added to book manager!")
                overall_progress.progress(0.8, "Added to book manager")
                step_statuses["Adding to Book Manager"] = "✅"
                step_details["Adding to Book Manager"].info(f"Book ID: {book_id}")
                update_steps_display(steps_container, steps, step_statuses, step_details)
                add_log(f"Book added to manager with ID: {book_id}", "SUCCESS")
            else:
                manager_progress.progress(1.0, "Failed to add to book manager!")
                step_statuses["Adding to Book Manager"] = "❌"
                update_steps_display(steps_container, steps, step_statuses, step_details)
                add_log("Failed to add book to manager", "ERROR")
                return
            
            # STEP 5: ADDING TO KNOWLEDGE BASE
            status_text.text("Adding to knowledge base...")
            step_statuses["Adding to Knowledge Base"] = "🔄"
            update_steps_display(steps_container, steps, step_statuses, step_details)
            
            kb_progress = step_progress["Adding to Knowledge Base"]
            kb_progress.progress(0.3, "Generating document ID...")
            overall_progress.progress(0.85, "Adding to knowledge base...")
            
            # Generate document ID
            doc_id = knowledge_base.generate_id()
            kb_progress.progress(0.5, "Creating metadata...")
            
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
            
            kb_progress.progress(0.7, "Indexing document...")
            
            # Add to knowledge base
            knowledge_base.add_document(
                doc_id,
                result.get("text", ""),
                metadata
            )
            
            kb_progress.progress(1.0, "Added to knowledge base!")
            overall_progress.progress(1.0, "Process complete!")
            step_statuses["Adding to Knowledge Base"] = "✅"
            step_details["Adding to Knowledge Base"].info(f"Document ID: {doc_id}")
            update_steps_display(steps_container, steps, step_statuses, step_details)
            add_log(f"Document added to knowledge base with ID: {doc_id}", "SUCCESS")
            
            # Final success message
            status_text.success(f"Book '{book_info['title']}' successfully added to your knowledge base!")
            
            # Update logs in the expandable section
            with log_container:
                for log in st.session_state.archive_processing_logs[-10:]:  # Show last 10 logs
                    level = log.get('level', 'INFO')
                    message = log.get('message', '')
                    if level == "ERROR":
                        st.error(message)
                    elif level == "WARNING":
                        st.warning(message)
                    elif level == "SUCCESS":
                        st.success(message)
                    else:
                        st.info(message)
            
            # Add a small delay to let user see final status
            time.sleep(1)
            
        except Exception as e:
            error_msg = f"Error processing book: {str(e)}"
            status_text.error(error_msg)
            
            # Set current step to error state
            for step, status in step_statuses.items():
                if status == "🔄":
                    step_statuses[step] = "❌"
                    step_details[step].error(str(e))
                    break
                    
            update_steps_display(steps_container, steps, step_statuses, step_details)
            overall_progress.progress(1.0, "Process failed")
            
            add_log(error_msg, "ERROR")
            logger.error(error_msg)
            
            # Show error details in the logs section
            with log_container:
                st.error(f"Error: {str(e)}")
                st.code(e.__traceback__, language="python")

def update_steps_display(container, steps, step_statuses, step_details):
    """
    Update the steps display in the dialog.
    
    Args:
        container: Container to render in
        steps: List of step names
        step_statuses: Dictionary of step statuses
        step_details: Dictionary of step detail placeholders
    """
    # We need to use st.markdown to build a visual progress list
    with container:
        # Clear previous content if any
        for step in steps:
            # Only update the steps, not the detail placeholders
            pass
            
        # Use markdown to create a visual progress list
        steps_md = ""
        for step in steps:
            status_icon = step_statuses[step]
            steps_md += f"{status_icon} **{step}**\n\n"
            
        st.markdown(steps_md)
        
def render_archive_search_page():
    """
    Main function to render the archive search page.
    """
    from book_manager import BookManager
    book_manager = BookManager()
    
    archive_search_page(book_manager, st.session_state.knowledge_base)
