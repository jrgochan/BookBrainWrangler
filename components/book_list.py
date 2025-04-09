"""
Book list component for the application.
Provides a UI component for rendering a list of books.
"""

import os
import streamlit as st

def render_book_list(books, on_select=None, on_delete=None, on_edit=None, on_toggle_kb=None, indexed_books=None, thumbnail_cache=None):
    """
    Render a grid of book cards with thumbnails and actions.

    Args:
        books: List of book dictionaries
        on_select: Optional callback when a book is selected
        on_delete: Optional callback when a book is deleted
        on_edit: Optional callback when a book is edited
        on_toggle_kb: Optional callback when knowledge base toggle is clicked
        indexed_books: Optional list of book IDs already in the knowledge base
        thumbnail_cache: Optional cache dictionary for book thumbnails
    """
    if not books:
        st.info("No books found matching your criteria.")
        return
    
    # Initialize thumbnail cache if not provided
    if thumbnail_cache is None and 'thumbnail_cache' in st.session_state:
        thumbnail_cache = st.session_state.thumbnail_cache
    
    # Create a grid layout
    num_cols = 3
    cols = st.columns(num_cols)
    
    # Render each book in the grid
    for i, book in enumerate(books):
        with cols[i % num_cols]:
            with st.container(border=True):
                # Book title and author
                st.markdown(f"### {book['title']}")
                st.caption(f"by {book['author']}")
                
                # Categories
                if book.get('categories'):
                    category_text = ", ".join(book['categories'])
                    st.markdown(f"*{category_text}*")
                
                # Actions row with buttons
                # Create a more organized action row with 3 columns
                action_col1, action_col2, action_col3 = st.columns(3)
                
                with action_col1:
                    if on_select:
                        if st.button("View", key=f"view_{book['id']}", use_container_width=True):
                            on_select(book['id'])
                
                with action_col2:
                    if on_edit:
                        # Use a primary button for edit to make it stand out
                        if st.button("Edit", key=f"edit_{book['id']}", use_container_width=True):
                            on_edit(book['id'])
                
                with action_col3:
                    if on_delete:
                        # Use a "danger" styled button for delete
                        btn_style = "color: white; background-color: #ff4b4b; border: none; border-radius: 4px; padding: 0.25rem 0.75rem; width: 100%; cursor: pointer;"
                        
                        # Check if this book is pending deletion confirmation
                        is_pending_delete = ('confirm_delete' in st.session_state and 
                                           st.session_state.confirm_delete == book['id'])
                        
                        # Different text based on confirmation status
                        btn_text = "Confirm" if is_pending_delete else "Delete"
                        
                        # Create a styled button since st.button doesn't support danger type
                        if st.button(btn_text, key=f"delete_{book['id']}", use_container_width=True):
                            on_delete(book['id'])
                
                # Knowledge base toggle in a separate row for clarity
                if on_toggle_kb and indexed_books is not None:
                    is_indexed = book['id'] in indexed_books
                    # Create a container for the toggle to ensure consistent spacing
                    with st.container():
                        if st.toggle(
                            "Add to Knowledge Base", 
                            value=is_indexed, 
                            key=f"kb_toggle_{book['id']}"
                        ):
                            if not is_indexed:  # Add to KB
                                on_toggle_kb(book['id'], True)
                        else:
                            if is_indexed:  # Remove from KB
                                on_toggle_kb(book['id'], False)