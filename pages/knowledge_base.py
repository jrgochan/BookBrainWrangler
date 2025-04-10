"""
Knowledge Base page for the application.
"""

import streamlit as st
import time
from utils.ui_helpers import create_download_link, show_progress_bar
from utils.notifications import get_notification_manager, render_notification_center, NotificationLevel, NotificationType

def render_knowledge_base_page(book_manager, knowledge_base):
    """
    Render the Knowledge Base page.
    
    Args:
        book_manager: The BookManager instance
        knowledge_base: The KnowledgeBase instance
    """
    # Get notification manager
    notification_manager = get_notification_manager()
    
    # Display notification indicator
    notification_manager.render_notification_indicator()
    
    st.title("Knowledge Base")
    
    # Display notifications indicator without using an expander
    if notification_manager.count_unread() > 0:
        st.info(f"📢 You have {notification_manager.count_unread()} unread notifications. View them on the Notifications page.")
    
    # Check for KB rebuild/reset requests from settings page
    if hasattr(st.session_state, 'rebuild_kb') and st.session_state.rebuild_kb:
        with st.spinner("Rebuilding knowledge base..."):
            # Get current settings
            kb_settings = st.session_state.get('kb_settings', {})
            vector_store_type = kb_settings.get('vector_store_type', 'faiss')
            distance_func = kb_settings.get('distance_func', 'cosine')
            use_gpu = kb_settings.get('use_gpu', True)
            
            # Create a new knowledge base with the selected vector store type
            # We'll use the same knowledge_base object but with a new vector_store
            kwargs = {
                'collection_name': knowledge_base.vector_store.collection_name,
                'base_path': knowledge_base.vector_store.base_path,
                'data_path': knowledge_base.vector_store.data_path,
                'embedding_function': knowledge_base.vector_store.embedding_function,
                'distance_func': distance_func
            }
            
            # Add GPU setting if using FAISS
            if vector_store_type == 'faiss':
                kwargs['use_gpu'] = use_gpu
                st.info(f"FAISS vector store initialized with GPU support: {'enabled' if use_gpu else 'disabled'}")
            
            # Create the vector store
            knowledge_base.vector_store = knowledge_base.vector_store.__class__(**kwargs)
            
            # Get all books that should be indexed
            all_books = book_manager.get_all_books()
            for book in all_books:
                if hasattr(book, 'include_in_kb') and book.include_in_kb:
                    # Re-index the book
                    book_manager.add_book_to_knowledge_base(book.id, knowledge_base)
            
            # Reset the flag
            st.session_state.rebuild_kb = False
            st.success("Knowledge base has been rebuilt!")
            
    # Check for KB reset request
    if hasattr(st.session_state, 'reset_kb') and st.session_state.reset_kb:
        with st.spinner("Resetting knowledge base..."):
            # Get current GPU settings
            kb_settings = st.session_state.get('kb_settings', {})
            
            # Reset the vector store - GPU settings will be applied within the reset method
            if knowledge_base.vector_store.reset():
                # Reset the flag
                st.session_state.reset_kb = False
                st.success("Knowledge base has been reset!")
            else:
                st.error("Failed to reset knowledge base. Check logs for details.")
    
    # Get all books and indexed books
    all_books = book_manager.get_all_books()
    indexed_book_ids = knowledge_base.get_indexed_book_ids()
    
    # Display knowledge base stats
    render_knowledge_base_stats(knowledge_base)
    
    # Book grid for toggling knowledge base inclusion
    render_book_grid(book_manager, knowledge_base, all_books, indexed_book_ids)
    
    # Knowledge base operations
    render_knowledge_base_operations(book_manager, knowledge_base)

def render_knowledge_base_stats(knowledge_base):
    """
    Render the knowledge base statistics section.
    
    Args:
        knowledge_base: The KnowledgeBase instance
    """
    st.header("Knowledge Base Status")
    
    # Get the vector store type from session state or from the knowledge base
    kb_settings = st.session_state.get('kb_settings', {})
    vector_store_type = kb_settings.get('vector_store_type', 'faiss')
    use_gpu = kb_settings.get('use_gpu', True)
    
    # Show vector store type
    if vector_store_type == 'faiss':
        gpu_status = ""
        # Check if the vector store has GPU information
        if hasattr(knowledge_base.vector_store, 'using_gpu'):
            gpu_status = f" (GPU: {'Enabled' if knowledge_base.vector_store.using_gpu else 'Disabled'})"
        st.info(f"Vector Store: **{vector_store_type.upper()}{gpu_status}**")
    else:
        st.info(f"Vector Store: **{vector_store_type.upper()}**")
    
    # Get vector store statistics
    try:
        stats = knowledge_base.get_vector_store_stats()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Books in Knowledge Base", stats.get("book_count", 0))
        
        with col2:
            st.metric("Total Documents", stats.get("document_count", 0))
        
        with col3:
            st.metric("Vector Dimensions", stats.get("dimensions", 0))
        
    except Exception as e:
        st.error(f"Error getting knowledge base statistics: {str(e)}")

def render_book_grid(book_manager, knowledge_base, books, indexed_book_ids):
    """
    Render the book grid with knowledge base toggle.
    
    Args:
        book_manager: The BookManager instance
        knowledge_base: The KnowledgeBase instance
        books: List of book dictionaries
        indexed_book_ids: List of book IDs in the knowledge base
    """
    st.header("Books in Knowledge Base")
    
    if not books:
        st.info("No books found in your library. Upload some books to get started!")
        return
    
    # Create a grid of books with toggle switches
    book_columns = st.columns(3)
    
    for i, book in enumerate(books):
        with book_columns[i % 3]:
            with st.container(border=True):
                # Book title and author
                st.markdown(f"### {book['title']}")
                st.markdown(f"*by {book['author']}*")
                
                # Check if we need to initialize or update the book's KB status in session state
                book_state_key = f"kb_status_{book['id']}"
                if book_state_key not in st.session_state:
                    # Initialize with current status
                    st.session_state[book_state_key] = book['id'] in indexed_book_ids
                
                # Get content availability status
                if book_state_key + "_no_content" not in st.session_state:
                    st.session_state[book_state_key + "_no_content"] = False
                
                # Use the stored value for the toggle
                is_in_kb = st.session_state[book_state_key]
                toggle_key = f"kb_toggle_{book['id']}"
                
                # If we've previously seen this book has no content, show disabled toggle with message
                if st.session_state[book_state_key + "_no_content"]:
                    st.toggle(
                        "Include in Knowledge Base", 
                        value=False,
                        key=toggle_key,
                        disabled=True,
                        help="This book has no content and cannot be added to the knowledge base"
                    )
                    st.caption("❌ No content available")
                    continue
                
                # Regular toggle for books with content (or unknown content status)
                toggle_value = st.toggle(
                    "Include in Knowledge Base", 
                    value=is_in_kb, 
                    key=toggle_key,
                    help="Toggle to add or remove this book from your knowledge base"
                )
                
                # Toggle state changed
                if toggle_value != is_in_kb:
                    # Save the new value for the next rerun
                    st.session_state[book_state_key] = toggle_value
                    
                    # Toggle turned ON - Add to KB
                    if toggle_value and not is_in_kb:
                        with st.spinner(f"Adding '{book['title']}' to knowledge base..."):
                            # Get the book content
                            content = book_manager.get_book_content(book['id'])
                            
                            # Check if content exists
                            if not content:
                                st.error(f"Cannot add '{book['title']}' to knowledge base: no content available")
                                get_notification_manager().notify_missing_content(
                                    book_id=book['id'],
                                    book_title=book['title']
                                )
                                # Mark this book as having no content for future runs
                                st.session_state[book_state_key + "_no_content"] = True
                                # Reset the KB status
                                st.session_state[book_state_key] = False
                                st.rerun()
                                
                            # Create progress tracking
                            progress_container = st.empty()
                            
                            # Define progress callback
                            def update_progress(current, total, message):
                                if isinstance(message, str):
                                    show_progress_bar(
                                        progress_container, 
                                        current, 
                                        total, 
                                        f"Processing: {message}"
                                    )
                                else:
                                    show_progress_bar(
                                        progress_container, 
                                        current, 
                                        total, 
                                        "Processing document"
                                    )
                            
                            # Add to knowledge base with progress updates
                            success = knowledge_base.toggle_book_in_knowledge_base(
                                book['id'], 
                                content, 
                                add_to_kb=True,
                                progress_callback=update_progress,
                                book_title=book['title']  # Pass book title for notifications
                            )
                            
                            if success:
                                st.success(f"Added '{book['title']}' to knowledge base!")
                                # Display success notification
                                get_notification_manager().create_notification(
                                    message=f"Successfully added '{book['title']}' to knowledge base.",
                                    level=NotificationLevel.SUCCESS,
                                    notification_type=NotificationType.GENERAL,
                                    book_id=book['id'],
                                    book_title=book['title']
                                )
                            else:
                                st.error(f"Failed to add '{book['title']}' to knowledge base.")
                                # Reset the toggle state in session
                                st.session_state[book_state_key] = False
                                
                            time.sleep(1)  # Brief pause to show message
                            st.rerun()  # Refresh to update stats
                            
                    # Toggle turned OFF - Remove from KB
                    elif not toggle_value and is_in_kb:
                        with st.spinner(f"Removing '{book['title']}' from knowledge base..."):
                            success = knowledge_base.toggle_book_in_knowledge_base(
                                book['id'], 
                                None, 
                                add_to_kb=False,
                                book_title=book['title']
                            )
                            
                            if success:
                                st.warning(f"Removed '{book['title']}' from knowledge base")
                                # Display removal notification
                                get_notification_manager().create_notification(
                                    message=f"Removed '{book['title']}' from knowledge base.",
                                    level=NotificationLevel.INFO,
                                    notification_type=NotificationType.GENERAL,
                                    book_id=book['id'],
                                    book_title=book['title']
                                )
                            else:
                                st.error(f"Failed to remove '{book['title']}' from knowledge base.")
                                # Reset the toggle state in session
                                st.session_state[book_state_key] = True
                                
                            time.sleep(1)  # Brief pause to show message
                            st.rerun()  # Refresh to update stats

def render_knowledge_base_operations(book_manager, knowledge_base):
    """
    Render the knowledge base operations section.
    
    Args:
        book_manager: The BookManager instance
        knowledge_base: The KnowledgeBase instance
    """
    st.header("Knowledge Base Operations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Rebuild Knowledge Base", help="Rebuilds the entire knowledge base. Useful if there are issues."):
            # Create a progress container
            progress_container = st.empty()
            status_container = st.empty()
            
            # Define progress callback
            def update_progress(current, total, message):
                # Update progress bar
                show_progress_bar(progress_container, current, total, "Rebuilding")
                
                # Update status message
                if isinstance(message, str):
                    status_container.text(message)
            
            # Rebuild with progress updates
            with st.spinner("Rebuilding knowledge base..."):
                try:
                    knowledge_base.rebuild_knowledge_base(
                        book_manager,
                        progress_callback=update_progress
                    )
                    st.success("Knowledge base rebuilt successfully!")
                except Exception as e:
                    st.error(f"Error rebuilding knowledge base: {str(e)}")
    
    # Add a new section for enhanced export functionality
    st.subheader("Export Knowledge Base")
    
    # Import export utilities
    from utils.export_helpers import export_knowledge_base, EXPORT_FORMATS
    
    # Create UI for export options
    export_format = st.selectbox(
        "Export Format", 
        list(EXPORT_FORMATS.keys()),
        format_func=lambda x: EXPORT_FORMATS[x]["name"],
        help="Select the format for exporting your knowledge base"
    )
    
    # Content options
    with st.expander("Export Options", expanded=True):
        include_metadata = st.checkbox("Include Book Metadata", value=True, 
                                      help="Include book titles, authors, and categories")
        
        include_content = st.checkbox("Include Content Chunks", value=True,
                                     help="Include the actual text chunks from your knowledge base")
        
        include_embeddings = st.checkbox("Include Vector Embeddings", value=False,
                                        help="Include vector embeddings (warning: can create large files)")
        
        # Show estimated export size based on options
        kb_stats = knowledge_base.get_stats()
        chunk_count = kb_stats.get('chunk_count', 0)
        dimensions = kb_stats.get('dimensions', 0)
        
        # Calculate rough estimates
        base_size_mb = 0.01  # Base size for metadata
        content_size_mb = 0.0002 * chunk_count if include_content else 0  # Approx 200 bytes per chunk
        embedding_size_mb = 0.000004 * chunk_count * dimensions if include_embeddings else 0  # Approx 4 bytes per dimension
        
        total_size_mb = base_size_mb + content_size_mb + embedding_size_mb
        
        # Show size estimate with appropriate unit
        if total_size_mb < 1:
            st.caption(f"Estimated export size: {total_size_mb * 1000:.0f} KB")
        else:
            st.caption(f"Estimated export size: {total_size_mb:.1f} MB")
            
        # Warning for large exports
        if total_size_mb > 50:
            st.warning("⚠️ This export may create a large file. Consider disabling embeddings or content for a smaller file.")
    
    # Export button
    if st.button("Generate Export", key="generate_export_button", type="primary", help="Create and download the export file"):
        try:
            # Check if there are books in the knowledge base
            indexed_book_ids = knowledge_base.get_indexed_book_ids()
            
            if not indexed_book_ids:
                st.warning("No books in knowledge base to export.")
                return
            
            # Create a progress container for the export
            export_progress = st.progress(0, "Preparing export...")
            export_status = st.empty()
            
            # Define progress callback
            def update_export_progress(progress, message):
                export_progress.progress(progress, message)
                export_status.text(message)
            
            # Generate the export
            with st.spinner(f"Generating {EXPORT_FORMATS[export_format]['name']} export..."):
                try:
                    # Show selected options for debugging
                    debug_info = st.empty()
                    debug_info.info(f"Exporting with options: Format={export_format}, Metadata={include_metadata}, Content={include_content}, Embeddings={include_embeddings}")
                    
                    # Call export function with options
                    file_data, filename, mime_type = export_knowledge_base(
                        book_manager, 
                        knowledge_base,
                        format_type=export_format,
                        include_metadata=include_metadata,
                        include_content=include_content,
                        include_embeddings=include_embeddings,
                        progress_callback=update_export_progress
                    )
                    
                    # Create download button
                    st.download_button(
                        label=f"Download {EXPORT_FORMATS[export_format]['name']}",
                        data=file_data,
                        file_name=filename,
                        mime=mime_type,
                        key="kb_export_download"
                    )
                    
                    # Success message
                    st.success(f"Knowledge base exported successfully as {filename}")
                    
                    # Complete progress
                    export_progress.progress(1.0, "Export complete!")
                    export_status.text(f"Export complete! Click the download button above to save {filename}")
                    
                    # Remove debug info after success
                    debug_info.empty()
                    
                except Exception as e:
                    st.error(f"Error generating export: {str(e)}")
                    st.error(f"Error details: {type(e).__name__}: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc(), language="python")
                    export_progress.empty()
                    export_status.empty()
        
        except Exception as e:
            st.error(f"Error exporting knowledge base: {str(e)}")
