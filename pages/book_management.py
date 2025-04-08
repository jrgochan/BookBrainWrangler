"""
Book Management page for the application.
This page provides an interface to upload, manage, and view books.
"""

import streamlit as st
import os
import time
import tempfile
import shutil
from typing import Dict, List, Any, Optional

from utils.ui_helpers import show_progress_bar
from utils.file_helpers import is_valid_document, save_uploaded_file
from components.book_list import render_book_list

def render_book_management_page(book_manager, document_processor, knowledge_base):
    """
    Render the Book Management page.
    
    Args:
        book_manager: The BookManager instance
        document_processor: The DocumentProcessor instance
        knowledge_base: The KnowledgeBase instance
    """
    st.title("Book Management")
    
    # Upload new book section
    with st.expander("Upload New Book", expanded=True):
        render_upload_section(book_manager, document_processor)
    
    # Book library section
    render_library_section(book_manager)
    
    # Book editing modal
    render_edit_modal(book_manager)

def render_upload_section(book_manager, document_processor):
    """
    Render the upload section for adding new books.
    
    Args:
        book_manager: The BookManager instance
        document_processor: The DocumentProcessor instance
    """
    st.header("Upload New Book")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload a PDF or DOCX file from your CZUR ET24 Pro scanner or other sources", 
        type=["pdf", "docx"]
    )
    
    # Book metadata inputs
    col1, col2 = st.columns(2)
    with col1:
        book_title = st.text_input("Book Title")
    with col2:
        book_author = st.text_input("Book Author")
    
    book_category = st.text_input("Category (comma-separated for multiple categories)")
    
    # Process button
    if uploaded_file and st.button("Process Book"):
        # Validate input
        if not book_title:
            st.error("Please enter a book title")
            return
        
        if not book_author:
            st.error("Please enter a book author")
            return
        
        # Create a progress tracking container
        progress_container = st.empty()
        status_container = st.empty()
        info_container = st.empty()
        
        # OCR visualization containers - using a container instead of nested expander
        st.subheader("Document Processing Details")
        ocr_container = st.container()
        with ocr_container:
            ocr_image_container = st.empty()
            ocr_text_container = st.empty()
            ocr_confidence_container = st.empty()
        
        # Process the book with status updates
        try:
            # Save uploaded file temporarily
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            temp_path = f"temp_{int(time.time())}{file_ext}"
            
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Initialize processing status
            file_type = "PDF" if file_ext == '.pdf' else "DOCX" if file_ext == '.docx' else f"Document ({file_ext})"
            info_container.info(f"Processing {file_type} file: {uploaded_file.name}")
            
            # Define progress callback function
            def update_progress(current, total, message):
                # Update progress bar
                if total > 0:
                    show_progress_bar(progress_container, current, total, "Processing")
                
                # Handle different message formats
                if isinstance(message, dict):
                    status_text = message.get("text", "Processing...")
                    status_container.text(status_text)
                    
                    # Handle OCR-specific updates
                    if "current_image" in message and st.session_state.ocr_settings['show_current_image']:
                        page_num = current + 1  # 1-based page number for display
                        display_interval = st.session_state.ocr_settings['display_interval']
                        
                        if page_num % display_interval == 0 or page_num == 1 or page_num == total:
                            ocr_image_container.image(
                                f"data:image/jpeg;base64,{message['current_image']}", 
                                caption=f"Page {page_num}/{total}", 
                                use_column_width=True
                            )
                    
                    # Display extracted text if available
                    if "ocr_text" in message and st.session_state.ocr_settings['show_extracted_text']:
                        if message.get("action") == "completed":
                            ocr_text_container.text_area(
                                "Extracted Text", 
                                message["ocr_text"], 
                                height=150
                            )
                    
                    # Display OCR confidence if available
                    if "confidence" in message:
                        confidence = message["confidence"]
                        threshold = st.session_state.ocr_settings['confidence_threshold']
                        
                        # Format confidence as percentage
                        conf_text = f"OCR Confidence: {confidence:.1f}%"
                        
                        if confidence < threshold:
                            conf_text = f"⚠️ {conf_text} (Low Quality)"
                            ocr_confidence_container.error(conf_text)
                        else:
                            ocr_confidence_container.success(conf_text)
                else:
                    # Simple string message
                    status_container.text(message)
            
            # Process the file with the callback
            status_container.text("Starting document processing...")
            
            # For PDFs, show page count
            if file_ext == '.pdf':
                page_count = document_processor.get_page_count(temp_path)
                info_container.info(f"PDF has {page_count} pages to process")
            
            # Extract content
            extracted_content = document_processor.extract_content(
                temp_path, 
                include_images=True, 
                progress_callback=update_progress
            )
            
            # Add book to database
            status_container.text("Adding book to database...")
            show_progress_bar(progress_container, 90, 100)
            
            # Parse categories
            categories = [cat.strip() for cat in book_category.split(",") if cat.strip()]
            
            # Add to database
            book_id = book_manager.add_book(
                title=book_title,
                author=book_author,
                categories=categories,
                file_path=temp_path,
                content=extracted_content.get('text') if isinstance(extracted_content, dict) else extracted_content
            )
            
            # Complete
            show_progress_bar(progress_container, 100, 100)
            status_container.text("Book processing complete!")
            
            st.success(f"Book '{book_title}' successfully processed and added to your library!")
            
            # Clear the form
            st.rerun()
            
        except Exception as e:
            status_container.text(f"Error: {str(e)}")
            st.error(f"Error processing book: {e}")

def render_library_section(book_manager):
    """
    Render the book library section.
    
    Args:
        book_manager: The BookManager instance
    """
    st.header("Your Book Library")
    
    # Initialize state variables if they don't exist
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'filter_category' not in st.session_state:
        st.session_state.filter_category = "All"
    
    # Search and filter
    col1, col2 = st.columns(2)
    with col1:
        search_query = st.text_input("Search books", st.session_state.search_query)
        if search_query != st.session_state.search_query:
            st.session_state.search_query = search_query
    
    with col2:
        categories = book_manager.get_all_categories()
        filter_options = ["All"] + categories
        filter_category = st.selectbox(
            "Filter by category", 
            filter_options, 
            index=filter_options.index(st.session_state.filter_category) if st.session_state.filter_category in filter_options else 0
        )
        if filter_category != st.session_state.filter_category:
            st.session_state.filter_category = filter_category
    
    # Get filtered books
    if filter_category == "All":
        books = book_manager.search_books(search_query)
    else:
        books = book_manager.search_books(search_query, category=filter_category)
    
    # Render book list
    def on_edit(book_id):
        st.session_state.book_to_edit = book_id
        st.rerun()
    
    def on_delete(book_id):
        book = book_manager.get_book(book_id)
        book_manager.delete_book(book_id)
        # Remove from thumbnail cache
        if 'thumbnail_cache' in st.session_state and book_id in st.session_state.thumbnail_cache:
            del st.session_state.thumbnail_cache[book_id]
        st.success(f"Book '{book['title']}' deleted successfully!")
        st.rerun()
    
    render_book_list(books, on_edit=on_edit, on_delete=on_delete)

def render_edit_modal(book_manager):
    """
    Render the book editing modal.
    
    Args:
        book_manager: The BookManager instance
    """
    if hasattr(st.session_state, 'book_to_edit') and st.session_state.book_to_edit:
        book = book_manager.get_book(st.session_state.book_to_edit)
        if book:
            st.header(f"Edit Book: {book['title']}")
            
            new_title = st.text_input("Book Title", book['title'])
            new_author = st.text_input("Book Author", book['author'])
            new_categories = st.text_input("Categories (comma-separated)", ", ".join(book['categories']))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Changes"):
                    categories = [cat.strip() for cat in new_categories.split(",") if cat.strip()]
                    book_manager.update_book(
                        book_id=book['id'],
                        title=new_title,
                        author=new_author,
                        categories=categories
                    )
                    st.success("Book updated successfully!")
                    
                    # Clear the edit state and refresh
                    del st.session_state.book_to_edit
                    st.rerun()
            
            with col2:
                if st.button("Cancel"):
                    # Clear the edit state and refresh
                    del st.session_state.book_to_edit
                    st.rerun()