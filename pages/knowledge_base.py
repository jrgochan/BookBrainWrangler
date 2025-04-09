"""
Knowledge Base page for the application.
"""

import streamlit as st
import time
from utils.ui_helpers import create_download_link, show_progress_bar

def render_knowledge_base_page(book_manager, knowledge_base):
    """
    Render the Knowledge Base page.
    
    Args:
        book_manager: The BookManager instance
        knowledge_base: The KnowledgeBase instance
    """
    st.title("Knowledge Base")
    
    # Check for KB rebuild/reset requests from settings page
    if hasattr(st.session_state, 'rebuild_kb') and st.session_state.rebuild_kb:
        with st.spinner("Rebuilding knowledge base..."):
            # Get current settings
            kb_settings = st.session_state.get('kb_settings', {})
            vector_store_type = kb_settings.get('vector_store_type', 'faiss')
            distance_func = kb_settings.get('distance_func', 'cosine')
            
            # Create a new knowledge base with the selected vector store type
            # We'll use the same knowledge_base object but with a new vector_store
            knowledge_base.vector_store = knowledge_base.vector_store.__class__(
                collection_name=knowledge_base.vector_store.collection_name,
                base_path=knowledge_base.vector_store.base_path,
                data_path=knowledge_base.vector_store.data_path,
                embedding_function=knowledge_base.vector_store.embedding_function,
                distance_func=distance_func,
                vector_store_type=vector_store_type
            )
            
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
            # Reset the vector store
            knowledge_base.vector_store.reset()
            
            # Reset the flag
            st.session_state.reset_kb = False
            st.success("Knowledge base has been reset!")
    
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
    
    # Show vector store type
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
                
                # Toggle for knowledge base inclusion
                is_in_kb = book['id'] in indexed_book_ids
                
                # Use a unique key for each toggle
                toggle_key = f"kb_toggle_{book['id']}"
                
                if st.toggle(
                    "Include in Knowledge Base", 
                    value=is_in_kb, 
                    key=toggle_key,
                    help="Toggle to add or remove this book from your knowledge base"
                ):
                    # Should be added to KB but isn't yet
                    if not is_in_kb:
                        with st.spinner(f"Adding '{book['title']}' to knowledge base..."):
                            # Get the book content
                            content = book_manager.get_book_content(book['id'])
                            
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
                            knowledge_base.toggle_book_in_knowledge_base(
                                book['id'], 
                                content, 
                                add_to_kb=True,
                                progress_callback=update_progress
                            )
                            
                            st.success(f"Added '{book['title']}' to knowledge base!")
                            time.sleep(1)  # Brief pause to show success message
                            st.rerun()  # Refresh to update stats
                else:
                    # Should be removed from KB
                    if is_in_kb:
                        with st.spinner(f"Removing '{book['title']}' from knowledge base..."):
                            knowledge_base.toggle_book_in_knowledge_base(
                                book['id'], 
                                None, 
                                add_to_kb=False
                            )
                            
                            st.error(f"Removed '{book['title']}' from knowledge base")
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
    
    with col2:
        if st.button("Export Knowledge Base", help="Export all knowledge base content as a markdown document"):
            try:
                # Generate the knowledge export
                indexed_books = [book_manager.get_book(book_id) for book_id in knowledge_base.get_indexed_book_ids()]
                
                if not indexed_books:
                    st.warning("No books in knowledge base to export.")
                    return
                
                with st.spinner("Generating knowledge base export..."):
                    # Generate markdown content for the knowledge base
                    timestamp = time.strftime("%Y%m%d-%H%M%S")
                    filename = f"knowledge_base_export_{timestamp}.md"
                    
                    # Get a download link for the export
                    markdown_content = "# Knowledge Base Export\n\n"
                    markdown_content += f"*Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
                    
                    # Add book information and contexts to the export
                    for i, book in enumerate(indexed_books, 1):
                        markdown_content += f"## {i}. {book['title']}\n"
                        markdown_content += f"Author: {book['author']}\n\n"
                        
                        # Get a sample of the book content
                        content = book_manager.get_book_content(book['id'])
                        if content:
                            # Truncate content if too long
                            preview = content[:500] + "..." if len(content) > 500 else content
                            markdown_content += "### Content Sample\n"
                            markdown_content += f"{preview}\n\n"
                        
                        # Add separator between books
                        markdown_content += "---\n\n"
                    
                    # Create a download button for the markdown content
                    st.download_button(
                        label="Download Export",
                        data=markdown_content,
                        file_name=filename,
                        mime="text/markdown"
                    )
                    
                    st.success(f"Knowledge base exported as '{filename}'")
            
            except Exception as e:
                st.error(f"Error exporting knowledge base: {str(e)}")