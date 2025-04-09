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
    st.subheader("Upload New Book")
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
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload a PDF or DOCX file from your CZUR ET24 Pro scanner or other sources", 
        type=["pdf", "docx"]
    )
    
    # Auto-extract metadata from uploaded file with improved progress display
    extracted_metadata = {}
    if uploaded_file and 'extracted_metadata' not in st.session_state:
        # Save uploaded file temporarily to extract metadata
        try:
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
                        from document_processing.pdf_processor import extract_page_as_image, image_to_base64
                        
                        meta_progress.progress(30, text="Generating preview...")
                        preview_image = extract_page_as_image(temp_path, 1)
                        if preview_image:
                            preview_base64 = image_to_base64(preview_image)
                            st.image(f"data:image/jpeg;base64,{preview_base64}", 
                                     caption="First page preview", 
                                     width=300)
                    except Exception as e:
                        st.warning(f"Preview generation failed: {str(e)}")
                
                # Step 4: Extract metadata
                meta_progress.progress(50, text="Analyzing document for metadata...")
                
                # Extract metadata
                extracted_metadata = document_processor.extract_metadata(temp_path)
                
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
            except:
                pass  # Ignore errors in cleanup
                
        except Exception as e:
            st.warning(f"Could not extract metadata automatically: {str(e)}")
            st.session_state.extracted_metadata = {}
    
    # Use extracted metadata if available
    if uploaded_file and 'extracted_metadata' in st.session_state:
        extracted_metadata = st.session_state.extracted_metadata
    
    # Book metadata inputs - pre-fill with extracted data if available
    col1, col2 = st.columns(2)
    with col1:
        book_title = st.text_input("Book Title", 
                                  value=extracted_metadata.get('title', '') if extracted_metadata else '')
    with col2:
        book_author = st.text_input("Book Author", 
                                   value=extracted_metadata.get('author', '') if extracted_metadata else '')
    
    # Join categories with commas if they exist
    default_categories = ''
    if extracted_metadata and 'categories' in extracted_metadata and extracted_metadata['categories']:
        default_categories = ', '.join(extracted_metadata.get('categories', []))
    
    book_category = st.text_input("Category (comma-separated for multiple categories)",
                                 value=default_categories)
    
    # Process button - Improved UI
    col1, col2 = st.columns([3, 1])
    with col1:
        process_button = st.button("Process Book", type="primary", use_container_width=True)
    with col2:
        reset_button = st.button("Reset Form", use_container_width=True)
        
    if reset_button:
        # Clear the form and extracted metadata
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
                log_container = st.empty()
                log_messages = []
        
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
            
            log_messages.append(f"📄 File: {uploaded_file.name} ({file_size_mb:.2f} MB)")
            log_messages.append(f"📋 Type: {file_type}")
            log_container.markdown("  \n".join(log_messages))
            
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
                    
                    # Add to log
                    log_messages.append(f"🔄 {status_text}")
                    log_container.markdown("  \n".join(log_messages))
                    
                    # Handle OCR-specific updates
                    if "current_image" in message and st.session_state.ocr_settings['show_current_image']:
                        page_num = current + 1  # 1-based page number for display
                        display_interval = st.session_state.ocr_settings['display_interval']
                        
                        if page_num % display_interval == 0 or page_num == 1 or page_num == total:
                            ocr_image_container.image(
                                f"data:image/jpeg;base64,{message['current_image']}", 
                                caption=f"Page {page_num}/{total}", 
                                use_container_width=True
                            )
                    
                    # Display extracted text if available
                    if "ocr_text" in message and st.session_state.ocr_settings['show_extracted_text']:
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
                        threshold = st.session_state.ocr_settings['confidence_threshold']
                        
                        # Format confidence as percentage
                        conf_text = f"OCR Confidence: {confidence:.1f}%"
                        
                        if confidence < threshold:
                            conf_text = f"⚠️ {conf_text} (Low Quality)"
                            ocr_confidence_container.error(conf_text)
                            # Add to log
                            log_messages.append(f"⚠️ Low quality detection: {confidence:.1f}% confidence (below threshold of {threshold}%)")
                        else:
                            ocr_confidence_container.success(conf_text)
                            # Add to log
                            log_messages.append(f"✅ Good quality detection: {confidence:.1f}% confidence")
                        
                        log_container.markdown("  \n".join(log_messages))
                else:
                    # Simple string message
                    status_container.markdown(f"**Status**: {message}")
                    # Add to log
                    log_messages.append(f"ℹ️ {message}")
                    log_container.markdown("  \n".join(log_messages))
            
            # Process the file with the callback
            status_container.markdown("**Status**: Starting document processing...")
            
            # For PDFs, show page count
            if file_ext == '.pdf':
                page_count = document_processor.get_page_count(temp_path)
                info_container.info(f"PDF has {page_count} pages to process")
                log_messages.append(f"📑 Document has {page_count} pages")
                log_container.markdown("  \n".join(log_messages))
            
            # Extract content - this is the main processing step
            progress_bar.progress(10/100, text="Starting document processing...")
            
            extracted_content = document_processor.extract_content(
                temp_path, 
                include_images=True, 
                progress_callback=update_progress
            )
            
            # Add book to database
            progress_bar.progress(90/100, text="Adding book to database...")
            status_container.markdown("**Status**: Adding book to database...")
            log_messages.append("📝 Preparing to save book to database")
            log_container.markdown("  \n".join(log_messages))
            
            # Parse categories
            categories = [cat.strip() for cat in book_category.split(",") if cat.strip()]
            log_messages.append(f"🏷️ Categories: {', '.join(categories) if categories else 'None'}")
            
            # Add to database
            book_id = book_manager.add_book(
                title=book_title,
                author=book_author,
                categories=categories,
                file_path=temp_path,
                content=extracted_content.get('text') if isinstance(extracted_content, dict) else extracted_content
            )
            
            # Complete
            progress_bar.progress(100/100, text="Book processing complete!")
            status_container.markdown("**Status**: Book processing complete!")
            
            # Update log
            log_messages.append(f"✅ Book added to database with ID: {book_id}")
            log_container.markdown("  \n".join(log_messages))
            
            # Mark the process as complete
            process_status.update(label=f"✅ Book '{book_title}' successfully processed!", state="complete")
            
            # Success message outside the status container
            st.success(f"Book '{book_title}' by {book_author} successfully processed and added to your library!")
            
            # Additional success information
            st.info("You can now view this book in your library below, or use it in the Knowledge Base and AI Chat features.")
            
            # Show a summary of what happened
            with st.expander("Processing Summary", expanded=False):
                st.markdown(f"""
                ### Book Processing Summary
                - **Title**: {book_title}
                - **Author**: {book_author}
                - **Categories**: {', '.join(categories) if categories else 'None'}
                - **Source File**: {uploaded_file.name} ({file_size_mb:.2f} MB)
                - **Extracted Text Length**: {len(extracted_content.get('text', '')) if isinstance(extracted_content, dict) else len(extracted_content)} characters
                - **Status**: Successfully added to database
                """)
            
            # Clear the form and extracted metadata
            if 'extracted_metadata' in st.session_state:
                del st.session_state.extracted_metadata
                
            # Button to view library
            if st.button("View Your Book Library"):
                st.rerun()  # This will refresh the page, showing the updated library
            
        except Exception as e:
            # Handle errors with more detailed information
            error_message = str(e)
            status_container.markdown(f"**Status**: Error: {error_message}")
            
            # Add error to log
            log_messages.append(f"❌ ERROR: {error_message}")
            log_container.markdown("  \n".join(log_messages))
            
            # Update status to error
            process_status.update(label=f"⚠️ Error processing document", state="error")
            
            # Show error message with suggestions
            st.error(f"Error processing book: {error_message}")
            
            st.warning("""
            ### Troubleshooting Suggestions:
            1. Check that the file format is supported (PDF or DOCX)
            2. Verify that the file isn't corrupted
            3. Try with a smaller file if it's very large
            4. Check the OCR settings in the Settings page
            """)
            
            # Button to try again
            if st.button("Reset and Try Again"):
                # Clear extracted metadata on error for next attempt
                if 'extracted_metadata' in st.session_state:
                    del st.session_state.extracted_metadata
                st.rerun()

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