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
                col1, col2 = st.columns(2)
                
                with col1:
                    if on_select:
                        if st.button("View", key=f"view_{book['id']}"):
                            on_select(book['id'])
                
                with col2:
                    if on_edit:
                        if st.button("Edit", key=f"edit_{book['id']}"):
                            on_edit(book['id'])
                
                # Knowledge base toggle
                if on_toggle_kb and indexed_books is not None:
                    is_indexed = book['id'] in indexed_books
                    if st.toggle(
                        "In Knowledge Base", 
                        value=is_indexed, 
                        key=f"kb_toggle_{book['id']}"
                    ):
                        if not is_indexed:  # Add to KB
                            on_toggle_kb(book['id'], True)
                    else:
                        if is_indexed:  # Remove from KB
                            on_toggle_kb(book['id'], False)
                
                # Delete button (separate row)
                if on_delete:
                    if st.button("Delete", key=f"delete_{book['id']}"):
                        on_delete(book['id'])