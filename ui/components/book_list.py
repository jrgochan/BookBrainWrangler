"""
Book list component for the application.
This UI component renders a list of books with actions.
"""

import streamlit as st
from typing import List, Dict, Any, Callable, Optional, Union

def render_book_list(
    books: List[Dict[str, Any]], 
    on_select: Optional[Callable[[int], None]] = None, 
    on_delete: Optional[Callable[[int], None]] = None, 
    on_edit: Optional[Callable[[int], None]] = None, 
    on_toggle_kb: Optional[Callable[[int, bool], None]] = None, 
    indexed_books: Optional[List[int]] = None, 
    thumbnail_cache: Optional[Dict[int, str]] = None
) -> None:
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
    
    # Render books as a list with containers
    for book in books:
        with st.container(border=True):
            # Use columns for a horizontal layout
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Book title and author
                st.markdown(f"### {book['title']}")
                st.caption(f"by {book['author']}")
                
                # Categories
                if book.get('categories'):
                    category_text = ", ".join(book['categories'])
                    st.markdown(f"*{category_text}*")
                
                # Knowledge base status indicator
                if indexed_books is not None:
                    is_indexed = book['id'] in indexed_books
                    status_color = "green" if is_indexed else "gray"
                    status_text = "In Knowledge Base" if is_indexed else "Not in Knowledge Base"
                    st.markdown(f"<span style='color:{status_color};font-size:0.8em;'>●</span> <span style='font-size:0.8em;'>{status_text}</span>", unsafe_allow_html=True)
            
            with col2:
                # Actions column with stacked buttons
                button_col1, button_col2, button_col3 = st.columns(3)
                
                with button_col1:
                    if on_select:
                        if st.button("View", key=f"view_{book['id']}", use_container_width=True):
                            on_select(book['id'])
                
                with button_col2:
                    if on_edit:
                        # Use a primary button for edit to make it stand out
                        if st.button("Edit", key=f"edit_{book['id']}", use_container_width=True, type="primary"):
                            on_edit(book['id'])
                
                with button_col3:
                    if on_delete:
                        # Check if this book is pending deletion confirmation
                        is_pending_delete = ('confirm_delete' in st.session_state and 
                                          st.session_state.confirm_delete == book['id'])
                        
                        # Different text based on confirmation status
                        btn_text = "Confirm" if is_pending_delete else "Delete"
                        btn_type = "primary" if is_pending_delete else "secondary"
                        
                        if st.button(btn_text, key=f"delete_{book['id']}", use_container_width=True, type=btn_type):
                            on_delete(book['id'])
                
                # Knowledge base toggle 
                if on_toggle_kb and indexed_books is not None:
                    is_indexed = book['id'] in indexed_books
                    with st.container():
                        st.write("")  # Add a little spacing
                        toggle_label = "Remove from KB" if is_indexed else "Add to KB"
                        if st.toggle(
                            toggle_label, 
                            value=is_indexed, 
                            key=f"kb_toggle_{book['id']}"
                        ):
                            if not is_indexed:  # Add to KB
                                on_toggle_kb(book['id'], True)
                        else:
                            if is_indexed:  # Remove from KB
                                on_toggle_kb(book['id'], False)