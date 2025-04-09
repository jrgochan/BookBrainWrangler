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
                
                # Extract metadata with file path context
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
                    log_messages.append(f"[{current_time}] ℹ️ {message}")
                    update_terminal()
            
            # Process the file with the callback
            status_container.markdown("**Status**: Starting document processing...")
            
            # For PDFs, show page count
            if file_ext == '.pdf':
                page_count = document_processor.get_page_count(temp_path)
                info_container.info(f"PDF has {page_count} pages to process")
                current_time = datetime.now().strftime("%H:%M:%S")
                log_messages.append(f"[{current_time}] 📑 Document has {page_count} pages")
                update_terminal()
            
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
            current_time = datetime.now().strftime("%H:%M:%S")
            log_messages.append(f"[{current_time}] 📝 Preparing to save book to database")
            update_terminal()
            
            # Parse categories
            categories = [cat.strip() for cat in book_category.split(",") if cat.strip()]
            current_time = datetime.now().strftime("%H:%M:%S")
            log_messages.append(f"[{current_time}] 🏷️ Categories: {', '.join(categories) if categories else 'None'}")
            update_terminal()
            
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
            
            # Update log with timestamp
            current_time = datetime.now().strftime("%H:%M:%S")
            log_messages.append(f"[{current_time}] ✅ Book added to database with ID: {book_id}")
            update_terminal()
            
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
            if st.button("View Your Book Library", key="view_library_button"):
                st.rerun()  # This will refresh the page, showing the updated library
            
        except Exception as e:
            # Handle errors with more detailed information
            error_message = str(e)
            status_container.markdown(f"**Status**: Error: {error_message}")
            
            # Add error to log with timestamp
            current_time = datetime.now().strftime("%H:%M:%S")
            log_messages.append(f"[{current_time}] ❌ ERROR: {error_message}")
            update_terminal()
            
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
            if st.button("Reset and Try Again", key="retry_upload_button"):
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
        search_query = st.text_input("Search books", st.session_state.search_query, key="search_books_query")
        if search_query != st.session_state.search_query:
            st.session_state.search_query = search_query
    
    with col2:
        categories = book_manager.get_all_categories()
        filter_options = ["All"] + categories
        filter_category = st.selectbox(
            "Filter by category", 
            filter_options, 
            index=filter_options.index(st.session_state.filter_category) if st.session_state.filter_category in filter_options else 0,
            key="filter_books_category"
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
        # Simply set the book to edit in session state without triggering metadata extraction
        st.session_state.book_to_edit = book_id
        st.rerun()
    
    def on_delete(book_id):
        # Get the book title before deleting
        book = book_manager.get_book(book_id)
        title = book['title'] if book else f"Book {book_id}"
        
        # Confirmation dialog using session state
        if 'confirm_delete' not in st.session_state:
            st.session_state.confirm_delete = None
            
        if st.session_state.confirm_delete == book_id:
            # User confirmed deletion
            book_manager.delete_book(book_id)
            
            # Remove from thumbnail cache
            if 'thumbnail_cache' in st.session_state and book_id in st.session_state.thumbnail_cache:
                del st.session_state.thumbnail_cache[book_id]
                
            st.success(f"Book '{title}' deleted successfully!")
            
            # Reset confirmation state
            st.session_state.confirm_delete = None
            st.rerun()
        else:
            # Set book_id as pending confirmation
            st.session_state.confirm_delete = book_id
            st.warning(f"Are you sure you want to delete '{title}'? Click Delete again to confirm.")
            st.rerun()
    
    render_book_list(books, on_edit=on_edit, on_delete=on_delete)

def render_edit_modal(book_manager):
    """
    Render the enhanced book editing interface with tabs.
    
    Args:
        book_manager: The BookManager instance
    """
    if 'book_to_edit' in st.session_state and st.session_state.book_to_edit:
        book = book_manager.get_book(st.session_state.book_to_edit)
        if book:
            st.header(f"Book Management: {book['title']}")
            
            # Create tabs for different editing functions
            basic_tab, content_tab, kb_tab, ai_tab = st.tabs([
                "Basic Info", 
                "Content Preview", 
                "Knowledge Base Status", 
                "Reanalyze with AI"
            ])
            
            # Basic Info Tab
            with basic_tab:
                st.subheader("Edit Book Metadata")
                
                new_title = st.text_input("Book Title", book['title'], key=f"edit_title_{book['id']}")
                new_author = st.text_input("Book Author", book['author'], key=f"edit_author_{book['id']}")
                new_categories = st.text_input("Categories (comma-separated)", ", ".join(book['categories']), key=f"edit_categories_{book['id']}")
                
                # Additional metadata fields
                col1, col2 = st.columns(2)
                with col1:
                    publication_date = st.date_input("Publication Date", value=None, key=f"edit_pub_date_{book['id']}")
                with col2:
                    language = st.selectbox("Language", 
                                           options=["English", "Spanish", "French", "German", "Chinese", "Japanese", "Other"],
                                           index=0,
                                           key=f"edit_language_{book['id']}")
                
                # Notes field
                notes = st.text_area("Notes", placeholder="Add any notes about this book...", key=f"edit_notes_{book['id']}")
                
                # Save and Cancel buttons
                save_col, cancel_col = st.columns(2)
                with save_col:
                    if st.button("Save Changes", type="primary", use_container_width=True, key=f"save_changes_{book['id']}"):
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
                
                with cancel_col:
                    if st.button("Cancel", use_container_width=True, key=f"cancel_edit_{book['id']}"):
                        # Clear the edit state and refresh
                        del st.session_state.book_to_edit
                        st.rerun()
            
            # Content Preview Tab
            with content_tab:
                st.subheader("Book Content Preview")
                
                # Get book content
                content = book_manager.get_book_content(book['id'])
                
                if content:
                    # Show content stats
                    word_count = len(content.split())
                    char_count = len(content)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Word Count", f"{word_count:,}")
                    with col2:
                        st.metric("Character Count", f"{char_count:,}")
                    
                    # Preview of first 1000 characters
                    preview_length = min(1000, len(content))
                    preview_text = content[:preview_length] + ("..." if len(content) > preview_length else "")
                    
                    st.markdown("### Content Preview")
                    st.text_area("First 1000 characters", value=preview_text, height=300, disabled=True, key=f"content_preview_{book['id']}")
                    
                    # Option to export content
                    st.download_button(
                        label="Export Content as TXT",
                        data=content,
                        file_name=f"{book['title']}_content.txt",
                        mime="text/plain"
                    )
                else:
                    st.warning("No content available for this book.")
            
            # Knowledge Base Status Tab
            with kb_tab:
                st.subheader("Knowledge Base Integration")
                
                # Check if book is in KB
                try:
                    from knowledge_base import KnowledgeBase
                    kb = KnowledgeBase()
                    is_indexed = kb.is_document_indexed(book['id'])
                    
                    if is_indexed:
                        st.success("This book is currently indexed in the Knowledge Base.")
                        
                        # Show chunking info
                        chunks = kb.get_document_chunks(book['id'])
                        if chunks:
                            st.metric("Number of Text Chunks", len(chunks))
                            
                            # Option to view chunks
                            if st.checkbox("View Chunks", key=f"view_chunks_{book['id']}"):
                                for i, chunk in enumerate(chunks[:10]):  # Show first 10 chunks
                                    with st.expander(f"Chunk {i+1}"):
                                        st.write(chunk.page_content[:200] + "..." if len(chunk.page_content) > 200 else chunk.page_content)
                                
                                if len(chunks) > 10:
                                    st.info(f"Showing 10 out of {len(chunks)} chunks. All chunks will be used for AI responses.")
                        
                        # Remove from KB option
                        if st.button("Remove from Knowledge Base", key=f"remove_kb_{book['id']}"):
                            kb.remove_document(book['id'])
                            st.warning("Book has been removed from the Knowledge Base.")
                            st.rerun()
                    else:
                        st.warning("This book is not currently indexed in the Knowledge Base.")
                        
                        # Add to KB option
                        if st.button("Add to Knowledge Base", type="primary", key=f"add_kb_{book['id']}"):
                            try:
                                kb.add_document(book['id'], book_manager)
                                st.success("Book has been added to the Knowledge Base.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error adding book to Knowledge Base: {str(e)}")
                except Exception as e:
                    st.error(f"Error accessing Knowledge Base: {str(e)}")
            
            # Reanalyze with AI Tab
            with ai_tab:
                st.subheader("AI Analysis & Insights")
                
                # AI Model selection
                ai_model = st.selectbox(
                    "Select AI Model", 
                    options=["Ollama - Llama2", "Ollama - Mistral", "OpenAI - GPT-3.5", "OpenAI - GPT-4"],
                    index=0,
                    key=f"ai_model_{book['id']}"
                )
                
                # Analysis options
                st.write("#### Select Analysis Types")
                
                col1, col2 = st.columns(2)
                with col1:
                    extract_themes = st.checkbox("Extract Key Themes", value=True, key=f"themes_{book['id']}")
                    summarize = st.checkbox("Generate Summary", value=True, key=f"summary_{book['id']}")
                    extract_entities = st.checkbox("Identify Named Entities", value=False, key=f"entities_{book['id']}")
                
                with col2:
                    sentiment = st.checkbox("Sentiment Analysis", value=False, key=f"sentiment_{book['id']}")
                    key_quotes = st.checkbox("Extract Notable Quotes", value=False, key=f"quotes_{book['id']}")
                    metadata_enhance = st.checkbox("Enhance Metadata", value=True, key=f"enhance_{book['id']}")
                
                # Analysis Depth
                analysis_depth = st.slider("Analysis Depth", min_value=1, max_value=5, value=3, 
                                         help="Higher values produce more detailed analysis but take longer",
                                         key=f"depth_{book['id']}")
                
                # Run Analysis button
                if st.button("Run AI Analysis", type="primary", key=f"run_analysis_{book['id']}"):
                    # This would connect to the AI model and run the analysis
                    # For now, show a placeholder for the functionality
                    with st.spinner("Running AI analysis..."):
                        st.info("AI Analysis would be performed here, connecting to the selected model.")
                        st.info("This feature requires implementation of the AI integration.")
                        
                        # Placeholder for future AI analysis results
                        st.write("#### AI Analysis Results")
                        st.warning("This is a placeholder. The actual AI analysis needs to be implemented.")
                        
                        # Example of how the UI would look
                        with st.expander("Analysis Summary"):
                            st.write("The AI would provide a summary of the analysis here...")
                
                # Guide for AI Analysis
                with st.expander("About AI Analysis"):
                    st.markdown("""
                    **AI Analysis** allows you to extract deeper insights from your books using advanced language models.
                    
                    The AI can:
                    - Identify major themes and concepts
                    - Generate concise summaries
                    - Extract key entities (people, places, organizations)
                    - Analyze sentiment and emotional tone
                    - Identify notable or quotable passages
                    - Enhance metadata with additional relevant tags
                    
                    This feature requires proper configuration of the AI model connections.
                    """)
                    
            # Add button to return to book list at the bottom of all tabs
            st.divider()
            if st.button("Return to Book List", use_container_width=True, key=f"return_to_list_{book['id']}"):
                del st.session_state.book_to_edit
                st.rerun()