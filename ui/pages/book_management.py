"""
Book Management page for the application.
This page provides an interface to upload, manage, and view books.
"""

import streamlit as st
import os
import time
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional

from utils.logger import get_logger
from utils.file_helpers import is_valid_document, save_uploaded_file
from ui.components.book_list import render_book_list

# Get a logger for this module
logger = get_logger(__name__)

def render_book_management_page(book_manager, document_processor, knowledge_base):
    """
    Render the Book Management page.
    
    Args:
        book_manager: The BookManager instance
        document_processor: The DocumentProcessor instance
        knowledge_base: The KnowledgeBase instance
    """
    logger.info("Rendering Book Management page")
    st.title("Book Management")
    
    # Upload new book section
    st.subheader("Upload New Book")
    render_upload_section(book_manager, document_processor)
    
    # Book library section
    render_library_section(book_manager, knowledge_base)
    
    # Book editing modal
    render_edit_modal(book_manager)

def render_upload_section(book_manager, document_processor):
    """
    Render the upload section for adding new books.
    
    Args:
        book_manager: The BookManager instance
        document_processor: The DocumentProcessor instance
    """
    logger.debug("Rendering upload section")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload a PDF or DOCX file from your scanner or other sources", 
        type=["pdf", "docx"]
    )
    
    # Auto-extract metadata from uploaded file with improved progress display
    extracted_metadata = {}
    if uploaded_file and 'extracted_metadata' not in st.session_state:
        # Save uploaded file temporarily to extract metadata
        try:
            logger.info(f"Processing uploaded file: {uploaded_file.name}")
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            temp_path = f"temp_metadata_{int(time.time())}{file_ext}"
            
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Create a more interactive metadata extraction UI
            meta_col1, meta_col2 = st.columns([3, 1])
            
            with meta_col1:
                meta_status = st.status("Extracting metadata...", expanded=True) 
                meta_progress = st.progress(0, text="Preparing to analyze document...")
            
            with meta_col2:
                st.info(f"File: {uploaded_file.name}")
                file_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
                st.caption(f"Size: {file_size_mb:.2f} MB")
            
            # Show more detailed extraction steps
            with meta_status:
                # Step 1: Initialize
                meta_progress.progress(10, text="Initializing document processor...")
                time.sleep(0.2)  # Small delay for visual feedback
                
                # Step 2: Document type detection
                meta_progress.progress(20, text="Detecting document type...")
                time.sleep(0.2)
                
                file_type = "PDF" if file_ext == '.pdf' else "DOCX" if file_ext == '.docx' else "Document"
                st.write(f"📄 Document type: **{file_type}**")
                
                # Step 3: Content preview
                if file_ext == '.pdf':
                    try:
                        from document_processing.formats.pdf import extract_page_as_image
                        from utils.image_helpers import image_to_base64
                        
                        meta_progress.progress(30, text="Generating preview...")
                        preview_image = extract_page_as_image(temp_path, 1)
                        if preview_image:
                            preview_base64 = image_to_base64(preview_image)
                            st.image(f"data:image/jpeg;base64,{preview_base64}", 
                                     caption="First page preview", 
                                     width=300)
                    except Exception as e:
                        logger.warning(f"Preview generation failed: {str(e)}")
                        st.warning(f"Preview generation failed: {str(e)}")
                
                # Step 4: Extract metadata
                meta_progress.progress(50, text="Analyzing document for metadata...")
                
                # Extract metadata with file path context
                try:
                    from document_processing.metadata import extract_metadata
                    extracted_metadata = extract_metadata(temp_path)
                except Exception as e:
                    logger.warning(f"Metadata extraction failed: {str(e)}")
                    extracted_metadata = {}
                
                # Step 5: Display found metadata
                meta_progress.progress(90, text="Metadata found!")
                
                found_items = []
                if extracted_metadata.get('title'):
                    found_items.append(f"📚 **Title**: {extracted_metadata['title']}")
                if extracted_metadata.get('author'):
                    found_items.append(f"✍️ **Author**: {extracted_metadata['author']}")
                if extracted_metadata.get('categories') and len(extracted_metadata['categories']) > 0:
                    found_items.append(f"🏷️ **Categories**: {', '.join(extracted_metadata['categories'])}")
                
                if found_items:
                    st.write("### Found Metadata")
                    for item in found_items:
                        st.write(item)
                else:
                    st.write("⚠️ No metadata found automatically. Please fill in the details below.")
                
                # Final step
                meta_progress.progress(100, text="Metadata extraction complete!")
                meta_status.update(label="Metadata extracted successfully!", state="complete")
                
                # Store in session state to avoid re-extracting
                st.session_state.extracted_metadata = extracted_metadata
                
            # Clean up temp file
            try:
                os.remove(temp_path)
                logger.debug(f"Removed temporary file: {temp_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {str(e)}")
                
        except Exception as e:
            logger.error(f"Could not extract metadata automatically: {str(e)}")
            st.warning(f"Could not extract metadata automatically: {str(e)}")
            st.session_state.extracted_metadata = {}
    
    # Use extracted metadata if available
    if uploaded_file and 'extracted_metadata' in st.session_state:
        extracted_metadata = st.session_state.extracted_metadata
    
    # Book metadata inputs - pre-fill with extracted data if available
    col1, col2 = st.columns(2)
    with col1:
        book_title = st.text_input("Book Title", 
                                  value=extracted_metadata.get('title', '') if extracted_metadata else '',
                                  key="new_book_title")
    with col2:
        book_author = st.text_input("Book Author", 
                                   value=extracted_metadata.get('author', '') if extracted_metadata else '',
                                   key="new_book_author")
    
    # Join categories with commas if they exist
    default_categories = ''
    if extracted_metadata and 'categories' in extracted_metadata and extracted_metadata['categories']:
        default_categories = ', '.join(extracted_metadata.get('categories', []))
    
    book_category = st.text_input("Category (comma-separated for multiple categories)",
                                 value=default_categories,
                                 key="new_book_categories")
    
    # Process button - Improved UI
    col1, col2 = st.columns([3, 1])
    with col1:
        process_button = st.button("Process Book", type="primary", use_container_width=True, key="process_book_button")
    with col2:
        reset_button = st.button("Reset Form", use_container_width=True, key="reset_form_button")
        
    if reset_button:
        # Clear the form and extracted metadata
        logger.debug("Reset form button clicked")
        if 'extracted_metadata' in st.session_state:
            del st.session_state.extracted_metadata
        st.rerun()
        
    if uploaded_file and process_button:
        # Validate input
        if not book_title:
            st.error("Please enter a book title")
            return
        
        if not book_author:
            st.error("Please enter a book author")
            return
        
        logger.info(f"Processing book: {book_title} by {book_author}")
        
        # Create a processing status container with expanded view
        process_status = st.status("Processing document...", expanded=True)
        
        # Create a progress tracking container
        with process_status:
            # Processing info header
            st.markdown(f"### Processing: {uploaded_file.name}")
            
            # Create progress elements
            progress_container = st.empty()
            progress_bar = progress_container.progress(0, text="Initializing document processor...")
            
            status_container = st.empty()
            info_container = st.empty()
            
            # Create tabs for different visualization aspects
            process_tabs = st.tabs(["Page Preview", "Extracted Text", "Processing Info"])
            
            with process_tabs[0]:
                ocr_image_container = st.empty()
                ocr_confidence_container = st.empty()
                
            with process_tabs[1]:
                ocr_text_container = st.empty()
                
            with process_tabs[2]:
                st.caption("This tab shows technical details about the processing")
                
                # Create a fixed-height terminal-like container with scrolling
                terminal_container = st.container()
                with terminal_container:
                    # Apply custom CSS for terminal-like appearance
                    st.markdown("""
                    <style>
                    .terminal-box {
                        background-color: #0e1117;
                        color: #16c60c;
                        font-family: 'Courier New', monospace;
                        border: 1px solid #4d4d4d;
                        border-radius: 5px;
                        padding: 10px;
                        height: 350px;
                        overflow-y: auto;
                        white-space: pre-wrap;
                        word-break: break-word;
                        line-height: 1.3;
                        font-size: 0.9rem;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Create empty element to hold terminal output
                    terminal_output = st.empty()
                
                # Initialize log messages list with timestamp
                log_messages = []
                current_time = datetime.now().strftime("%H:%M:%S")
                log_messages.append(f"[{current_time}] 🖥️ Terminal initialized")
                log_messages.append(f"[{current_time}] 🔄 Starting book processing...")
                
                # Helper function to update the terminal display with auto-scroll
                def update_terminal():
                    # Keep only the last 100 messages to prevent excessive length
                    display_messages = log_messages[-100:] if len(log_messages) > 100 else log_messages
                    terminal_content = "\n".join(display_messages)
                    
                    # Update the terminal display
                    terminal_output.markdown(f'<div class="terminal-box">{terminal_content}</div>', unsafe_allow_html=True)
                
                # Initial terminal update
                update_terminal()
        
        # Process the book with status updates
        try:
            # Save uploaded file temporarily
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            temp_path = f"temp_{int(time.time())}{file_ext}"
            
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Update log
            file_type = "PDF" if file_ext == '.pdf' else "DOCX" if file_ext == '.docx' else f"Document ({file_ext})"
            file_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
            
            current_time = datetime.now().strftime("%H:%M:%S")
            log_messages.append(f"[{current_time}] 📄 File: {uploaded_file.name} ({file_size_mb:.2f} MB)")
            log_messages.append(f"[{current_time}] 📋 Type: {file_type}")
            update_terminal()
            
            # Define progress callback function with enhanced UI feedback
            def update_progress(current, total, message):
                # Update progress bar
                if total > 0:
                    progress_value = min(100, int((current / total) * 100)) / 100
                    progress_text = f"Processing page {current+1}/{total} ({int(progress_value*100)}%)"
                    progress_bar.progress(progress_value, text=progress_text)
                
                # Handle different message formats
                if isinstance(message, dict):
                    status_text = message.get("text", "Processing...")
                    status_container.markdown(f"**Status**: {status_text}")
                    
                    # Add to log with timestamp
                    current_time = datetime.now().strftime("%H:%M:%S")
                    log_messages.append(f"[{current_time}] 🔄 {status_text}")
                    update_terminal()
                    
                    # Handle OCR-specific updates
                    if "current_image" in message and st.session_state.get('ocr_settings', {}).get('show_current_image', True):
                        page_num = current + 1  # 1-based page number for display
                        display_interval = st.session_state.get('ocr_settings', {}).get('display_interval', 5)
                        
                        if page_num % display_interval == 0 or page_num == 1 or page_num == total:
                            ocr_image_container.image(
                                f"data:image/jpeg;base64,{message['current_image']}", 
                                caption=f"Page {page_num}/{total}", 
                                use_container_width=True
                            )
                    
                    # Display extracted text if available
                    if "ocr_text" in message and st.session_state.get('ocr_settings', {}).get('show_extracted_text', True):
                        text_preview = message["ocr_text"]
                        # Truncate if too long for display
                        if len(text_preview) > 1000:
                            text_preview = text_preview[:1000] + "...(truncated)"
                            
                        ocr_text_container.text_area(
                            "Extracted Text Preview", 
                            text_preview,
                            height=300
                        )
                    
                    # Display OCR confidence if available
                    if "confidence" in message:
                        confidence = message["confidence"]
                        threshold = st.session_state.get('ocr_settings', {}).get('confidence_threshold', 70.0)
                        
                        # Format confidence as percentage
                        conf_text = f"OCR Confidence: {confidence:.1f}%"
                        
                        if confidence < threshold:
                            conf_text = f"⚠️ {conf_text} (Low Quality)"
                            ocr_confidence_container.error(conf_text)
                            # Add to log with timestamp
                            current_time = datetime.now().strftime("%H:%M:%S")
                            log_messages.append(f"[{current_time}] ⚠️ Low quality detection: {confidence:.1f}% confidence (below threshold of {threshold}%)")
                        else:
                            ocr_confidence_container.success(conf_text)
                            # Add to log with timestamp
                            current_time = datetime.now().strftime("%H:%M:%S")
                            log_messages.append(f"[{current_time}] ✅ Good quality detection: {confidence:.1f}% confidence")
                        
                        update_terminal()
                else:
                    # Simple string message
                    status_container.markdown(f"**Status**: {message}")
                    
                    # Add to log with timestamp
                    current_time = datetime.now().strftime("%H:%M:%S")
                    log_messages.append(f"[{current_time}] 🔄 {message}")
                    update_terminal()
            
            # Process the document with progress updates via callback
            use_ocr = st.session_state.get('ocr_settings', {}).get('use_ocr', True)
            include_images = True
            
            # Update status
            status_container.markdown("**Status**: Starting document processing...")
            current_time = datetime.now().strftime("%H:%M:%S")
            log_messages.append(f"[{current_time}] 🔍 OCR Enabled: {use_ocr}")
            update_terminal()
            
            # Process document
            processed_doc = document_processor.process(
                temp_path, 
                file_type=None,  # Auto-detect
                use_ocr=use_ocr,
                include_images=include_images,
                progress_callback=update_progress
            )
            
            # Extract the document content
            text_content = processed_doc.get('text', '')
            
            # Update progress and status
            progress_bar.progress(1.0, text="Processing complete!")
            status_container.markdown("**Status**: Document processing complete!")
            
            # Log completion
            current_time = datetime.now().strftime("%H:%M:%S")
            log_messages.append(f"[{current_time}] ✅ Document processing complete!")
            update_terminal()
            
            # Add the book to the database
            categories = [cat.strip() for cat in book_category.split(',') if cat.strip()]
            
            # Update status
            status_container.markdown("**Status**: Adding book to database...")
            current_time = datetime.now().strftime("%H:%M:%S")
            log_messages.append(f"[{current_time}] 💾 Adding book to database...")
            update_terminal()
            
            try:
                # Add book to the database
                book_id = book_manager.add_book(
                    title=book_title,
                    author=book_author,
                    categories=categories,
                    file_path=temp_path,
                    content=text_content
                )
                
                # Update status
                if book_id:
                    # Success message
                    process_status.update(label=f"Book '{book_title}' processed successfully!", state="complete")
                    
                    # Log success
                    current_time = datetime.now().strftime("%H:%M:%S")
                    log_messages.append(f"[{current_time}] ✅ Book added to database with ID: {book_id}")
                    update_terminal()
                    
                    # Clear the form
                    if 'extracted_metadata' in st.session_state:
                        del st.session_state.extracted_metadata
                    
                    # Add success message
                    st.success(f"Book '{book_title}' processed and added to the library!")
                    
                    # Clean up the temporary file
                    try:
                        os.remove(temp_path)
                        logger.debug(f"Removed temporary file: {temp_path}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up temp file: {str(e)}")
                    
                    # Rerun the app to refresh the book list
                    time.sleep(1)  # Small delay for better UX
                    st.rerun()
                    
                else:
                    # Error message
                    process_status.update(label="Failed to add book to database", state="error")
                    
                    # Log error
                    current_time = datetime.now().strftime("%H:%M:%S")
                    log_messages.append(f"[{current_time}] ❌ Failed to add book to database")
                    update_terminal()
                    
                    # Display error
                    st.error("Failed to add book to database. Please try again.")
                    
            except Exception as db_error:
                # Log error
                logger.error(f"Database error: {str(db_error)}")
                
                # Update status
                process_status.update(label=f"Database error: {str(db_error)}", state="error")
                
                # Log to terminal
                current_time = datetime.now().strftime("%H:%M:%S")
                log_messages.append(f"[{current_time}] ❌ Database error: {str(db_error)}")
                update_terminal()
                
                # Display error
                st.error(f"Database error: {str(db_error)}")
                
        except Exception as e:
            # Log error
            logger.error(f"Processing error: {str(e)}")
            
            # Update status
            process_status.update(label=f"Processing error: {str(e)}", state="error")
            
            # Log to terminal
            current_time = datetime.now().strftime("%H:%M:%S")
            log_messages.append(f"[{current_time}] ❌ Processing error: {str(e)}")
            update_terminal()
            
            # Display error
            st.error(f"An error occurred during processing: {str(e)}")
            
            # Try to clean up temporary files
            try:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass

def render_library_section(book_manager, knowledge_base):
    """
    Render the book library section.
    
    Args:
        book_manager: The BookManager instance
        knowledge_base: The KnowledgeBase instance
    """
    logger.debug("Rendering library section")
    st.subheader("Book Library")
    
    # Get all books
    books = book_manager.get_all_books()
    
    # Get all categories for filtering
    all_categories = book_manager.get_all_categories()
    all_categories = ["All Categories"] + all_categories
    
    # Create a search and filter UI
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input("Search by title or author", key="search_books")
    
    with col2:
        selected_category = st.selectbox("Filter by category", all_categories, key="filter_category")
    
    # Apply search and filtering
    if search_query or (selected_category and selected_category != "All Categories"):
        category = None if selected_category == "All Categories" else selected_category
        books = book_manager.search_books(query=search_query, category=category)
    
    # Check if any books were found
    if not books:
        st.info("No books found in your library. Upload a book to get started!")
        return
    
    # Get indexed books (those in the knowledge base)
    try:
        indexed_book_ids = knowledge_base.get_document_ids()
        indexed_book_ids = [id.replace("book_", "") for id in indexed_book_ids if id.startswith("book_")]
        indexed_book_ids = [int(id) for id in indexed_book_ids if id.isdigit()]
    except Exception as e:
        logger.error(f"Error getting indexed book IDs: {str(e)}")
        indexed_book_ids = []
    
    # Define callback functions for book actions
    def on_delete(book_id):
        st.session_state.delete_book_id = book_id
        st.session_state.show_delete_confirmation = True
    
    def on_edit(book_id):
        # Find the book details
        book = next((b for b in books if b["id"] == book_id), None)
        if book:
            st.session_state.edit_book_id = book_id
            st.session_state.edit_book_title = book["title"]
            st.session_state.edit_book_author = book["author"]
            st.session_state.edit_book_categories = ", ".join(book["categories"]) if book["categories"] else ""
            st.session_state.show_edit_modal = True
    
    def on_toggle_kb(book_id, is_in_kb):
        if is_in_kb:
            # Remove from knowledge base
            try:
                success = knowledge_base.remove_document(f"book_{book_id}")
                if success:
                    st.success(f"Book removed from knowledge base")
                    logger.info(f"Book {book_id} removed from knowledge base")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Failed to remove book from knowledge base")
                    logger.error(f"Failed to remove book {book_id} from knowledge base")
            except Exception as e:
                st.error(f"Error removing book from knowledge base: {str(e)}")
                logger.error(f"Error removing book {book_id} from knowledge base: {str(e)}")
        else:
            # Add to knowledge base
            try:
                # Get book content
                content = book_manager.get_book_content(book_id)
                if not content:
                    st.error("Book content not found")
                    return
                
                # Get book details for metadata
                book = next((b for b in books if b["id"] == book_id), None)
                if not book:
                    st.error("Book details not found")
                    return
                
                # Add to knowledge base
                success = knowledge_base.add_document(
                    document_id=f"book_{book_id}",
                    text=content,
                    metadata={
                        "title": book["title"],
                        "author": book["author"],
                        "categories": book["categories"],
                        "source": "book",
                        "book_id": book_id
                    }
                )
                
                if success:
                    st.success(f"Book added to knowledge base")
                    logger.info(f"Book {book_id} added to knowledge base")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Failed to add book to knowledge base")
                    logger.error(f"Failed to add book {book_id} to knowledge base")
                    
            except Exception as e:
                st.error(f"Error adding book to knowledge base: {str(e)}")
                logger.error(f"Error adding book {book_id} to knowledge base: {str(e)}")
    
    # Initialize thumbnail cache if it doesn't exist
    if 'thumbnail_cache' not in st.session_state:
        st.session_state.thumbnail_cache = {}
    
    # Render the book list component
    render_book_list(
        books, 
        on_delete=on_delete,
        on_edit=on_edit,
        on_toggle_kb=on_toggle_kb,
        indexed_books=indexed_book_ids,
        thumbnail_cache=st.session_state.thumbnail_cache
    )
    
    # Handle delete confirmation
    if st.session_state.get('show_delete_confirmation', False):
        delete_id = st.session_state.get('delete_book_id')
        book_to_delete = next((b for b in books if b["id"] == delete_id), None)
        
        if book_to_delete:
            st.warning(f"Are you sure you want to delete '{book_to_delete['title']}'? This action cannot be undone.")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Yes, Delete", key="confirm_delete", type="primary"):
                    # Delete the book
                    try:
                        logger.info(f"Deleting book {delete_id}")
                        book_manager.delete_book(delete_id)
                        
                        # Also remove from knowledge base if present
                        if str(delete_id) in indexed_book_ids:
                            try:
                                knowledge_base.remove_document(f"book_{delete_id}")
                                logger.info(f"Removed book {delete_id} from knowledge base")
                            except Exception as e:
                                logger.error(f"Error removing book {delete_id} from knowledge base: {str(e)}")
                        
                        # Clear the confirmation state
                        st.session_state.show_delete_confirmation = False
                        st.session_state.delete_book_id = None
                        
                        # Show success message
                        st.success(f"Book '{book_to_delete['title']}' deleted successfully!")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Error deleting book {delete_id}: {str(e)}")
                        st.error(f"Error deleting book: {str(e)}")
            
            with col2:
                if st.button("Cancel", key="cancel_delete"):
                    # Clear the confirmation state
                    st.session_state.show_delete_confirmation = False
                    st.session_state.delete_book_id = None
                    st.rerun()

def render_edit_modal(book_manager):
    """
    Render the book editing modal.
    
    Args:
        book_manager: The BookManager instance
    """
    if st.session_state.get('show_edit_modal', False):
        logger.debug(f"Rendering edit modal for book {st.session_state.edit_book_id}")
        
        # Get book details from session state
        book_id = st.session_state.edit_book_id
        book_title = st.session_state.edit_book_title
        book_author = st.session_state.edit_book_author
        book_categories = st.session_state.edit_book_categories
        
        # Create a form-like container
        st.subheader(f"Edit Book: {book_title}")
        
        # Book metadata inputs
        col1, col2 = st.columns(2)
        with col1:
            new_title = st.text_input("Book Title", value=book_title, key="edit_title_input")
        with col2:
            new_author = st.text_input("Book Author", value=book_author, key="edit_author_input")
        
        new_categories = st.text_input("Categories (comma-separated)", value=book_categories, key="edit_categories_input")
        
        # Convert categories string to list
        categories_list = [cat.strip() for cat in new_categories.split(',') if cat.strip()]
        
        # Action buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Save Changes", key="save_edit_button", type="primary"):
                try:
                    logger.info(f"Updating book {book_id} with new metadata")
                    # Update the book
                    book_manager.update_book(
                        book_id=book_id,
                        title=new_title,
                        author=new_author,
                        categories=categories_list
                    )
                    
                    # Clear the edit state
                    st.session_state.show_edit_modal = False
                    st.session_state.edit_book_id = None
                    st.session_state.edit_book_title = None
                    st.session_state.edit_book_author = None
                    st.session_state.edit_book_categories = None
                    
                    # Show success message
                    st.success(f"Book updated successfully!")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error updating book {book_id}: {str(e)}")
                    st.error(f"Error updating book: {str(e)}")
        
        with col2:
            if st.button("Cancel", key="cancel_edit_button"):
                # Clear the edit state
                st.session_state.show_edit_modal = False
                st.session_state.edit_book_id = None
                st.session_state.edit_book_title = None
                st.session_state.edit_book_author = None
                st.session_state.edit_book_categories = None
                st.rerun()