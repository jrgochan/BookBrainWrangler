"""
Book list component for the application.
Provides UI components for rendering and interacting with a list of books.
"""

import os
from typing import List, Dict, Any, Optional, Callable, Union
import streamlit as st

def render_book_list(
    books: List[Dict[str, Any]], 
    on_select: Optional[Callable[[int], None]] = None, 
    on_delete: Optional[Callable[[int], None]] = None, 
    on_edit: Optional[Callable[[int], None]] = None, 
    on_toggle_kb: Optional[Callable[[int, bool], None]] = None, 
    indexed_books: Optional[List[int]] = None, 
    thumbnail_cache: Optional[Dict[int, Any]] = None,
    show_kb_status: bool = True,
    enable_sorting: bool = False,
    sort_by: str = "title",
    sort_order: str = "asc",
    key_prefix: str = "book_list"
):
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
        show_kb_status: Whether to show knowledge base status indicators
        enable_sorting: Whether to enable sorting controls
        sort_by: Default sort field (title, author, date_added)
        sort_order: Default sort order (asc, desc)
        key_prefix: Prefix for Streamlit keys to avoid conflicts
    """
    if not books:
        st.info("No books found matching your criteria.")
        return []
    
    # Initialize thumbnail cache if not provided
    if thumbnail_cache is None and 'thumbnail_cache' in st.session_state:
        thumbnail_cache = st.session_state.thumbnail_cache
    
    # Sort books if enabled
    if enable_sorting:
        col1, col2 = st.columns([2, 1])
        with col1:
            sort_options = {
                "title": "Title",
                "author": "Author",
                "date_added": "Date Added"
            }
            sort_by = st.selectbox(
                "Sort by", 
                options=list(sort_options.keys()),
                format_func=lambda x: sort_options[x],
                index=list(sort_options.keys()).index(sort_by) if sort_by in sort_options else 0,
                key=f"{key_prefix}_sort_by"
            )
        
        with col2:
            sort_order = st.selectbox(
                "Order", 
                options=["asc", "desc"],
                format_func=lambda x: "Ascending" if x == "asc" else "Descending",
                index=0 if sort_order == "asc" else 1,
                key=f"{key_prefix}_sort_order"
            )
        
        # Sort the books
        reverse = sort_order == "desc"
        sorted_books = sorted(
            books,
            key=lambda x: x.get(sort_by, "").lower() if isinstance(x.get(sort_by), str) else x.get(sort_by, 0),
            reverse=reverse
        )
    else:
        sorted_books = books
    
    # Initialize selected books list
    selected_books = []
    
    # Render books as a wide list
    for book in sorted_books:
        with st.container(border=True):
            # Use columns for a horizontal layout
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Book title and author
                st.markdown(f"### {book['title']}")
                st.caption(f"by {book['author']}")
                
                # Categories with better styling
                if book.get('categories'):
                    category_text = ", ".join(book['categories'])
                    st.markdown(f"<div style='margin-bottom:10px;'><em>{category_text}</em></div>", unsafe_allow_html=True)
                
                # Knowledge base status indicator with improved accessibility
                if indexed_books is not None and show_kb_status:
                    is_indexed = book['id'] in indexed_books
                    status_color = "green" if is_indexed else "gray"
                    status_text = "In Knowledge Base" if is_indexed else "Not in Knowledge Base"
                    status_symbol = "✓" if is_indexed else "○"
                    st.markdown(
                        f"""<div style='margin-top:5px;'>
                            <span style='color:{status_color};font-size:0.8em;' 
                                  aria-hidden='true'>{status_symbol}</span> 
                            <span style='font-size:0.8em;'>{status_text}</span>
                         </div>""", 
                        unsafe_allow_html=True
                    )
            
            with col2:
                # Actions column with stacked buttons
                button_cols = st.columns(3)
                
                # View button
                with button_cols[0]:
                    if on_select:
                        view_disabled = False
                        view_tooltip = "View book details"
                        if st.button(
                            "View", 
                            key=f"{key_prefix}_view_{book['id']}", 
                            use_container_width=True,
                            disabled=view_disabled,
                            help=view_tooltip
                        ):
                            selected_books.append(book['id'])
                            on_select(book['id'])
                
                # Edit button
                with button_cols[1]:
                    if on_edit:
                        # Use a primary button for edit to make it stand out
                        edit_disabled = False
                        edit_tooltip = "Edit book details"
                        if st.button(
                            "Edit", 
                            key=f"{key_prefix}_edit_{book['id']}", 
                            use_container_width=True, 
                            type="primary",
                            disabled=edit_disabled,
                            help=edit_tooltip
                        ):
                            on_edit(book['id'])
                
                # Delete button with confirmation
                with button_cols[2]:
                    if on_delete:
                        # Check if this book is pending deletion confirmation
                        is_pending_delete = ('confirm_delete' in st.session_state and 
                                           st.session_state.confirm_delete == book['id'])
                        
                        # Different text based on confirmation status
                        btn_text = "Confirm" if is_pending_delete else "Delete"
                        btn_type = "primary" if is_pending_delete else "secondary"
                        btn_tooltip = "Confirm book deletion" if is_pending_delete else "Delete this book"
                        
                        if st.button(
                            btn_text, 
                            key=f"{key_prefix}_delete_{book['id']}", 
                            use_container_width=True, 
                            type=btn_type,
                            help=btn_tooltip
                        ):
                            on_delete(book['id'])
                
                # Knowledge base toggle with better UI/UX
                if on_toggle_kb and indexed_books is not None:
                    is_indexed = book['id'] in indexed_books
                    with st.container():
                        st.write("")  # Add spacing
                        toggle_label = "Remove from KB" if is_indexed else "Add to KB"
                        toggle_tooltip = (
                            "Remove this book from your knowledge base" if is_indexed 
                            else "Add this book to your knowledge base for AI interactions"
                        )
                        
                        toggle_state = st.toggle(
                            toggle_label, 
                            value=is_indexed, 
                            key=f"{key_prefix}_kb_toggle_{book['id']}",
                            help=toggle_tooltip
                        )
                        
                        # Check for state changes
                        if toggle_state != is_indexed:
                            on_toggle_kb(book['id'], toggle_state)
    
    return selected_books

def render_book_grid(
    books: List[Dict[str, Any]], 
    on_select: Optional[Callable[[int], None]] = None,
    thumbnail_cache: Optional[Dict[int, Any]] = None,
    columns: int = 3,
    key_prefix: str = "book_grid"
):
    """
    Render books in a grid layout with cover images.
    
    Args:
        books: List of book dictionaries
        on_select: Optional callback when a book is selected
        thumbnail_cache: Optional cache dictionary for book thumbnails
        columns: Number of columns in the grid
        key_prefix: Prefix for Streamlit keys to avoid conflicts
    
    Returns:
        List of selected book IDs
    """
    if not books:
        st.info("No books found matching your criteria.")
        return []
    
    # Initialize selected books
    selected_books = []
    
    # Initialize thumbnail cache if not provided
    if thumbnail_cache is None and 'thumbnail_cache' in st.session_state:
        thumbnail_cache = st.session_state.thumbnail_cache
    
    # Create grid layout
    cols = st.columns(columns)
    
    # Render each book
    for i, book in enumerate(books):
        col_idx = i % columns
        
        with cols[col_idx]:
            with st.container(border=True):
                # Add book cover (placeholder for now)
                if thumbnail_cache and book['id'] in thumbnail_cache:
                    st.image(thumbnail_cache[book['id']], use_column_width=True)
                else:
                    # Placeholder image - grey box with book title
                    st.markdown(
                        f"""
                        <div style="background-color:#f0f0f0;height:150px;display:flex;
                                    align-items:center;justify-content:center;text-align:center;
                                    margin-bottom:10px;">
                            <span>{book['title']}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                # Book title and author
                st.markdown(f"**{book['title']}**")
                st.caption(f"by {book['author']}")
                
                # View button
                if on_select and st.button(
                    "View Details", 
                    key=f"{key_prefix}_grid_view_{book['id']}",
                    use_container_width=True
                ):
                    selected_books.append(book['id'])
                    on_select(book['id'])
    
    return selected_books

def render_book_filters(
    categories: List[str],
    on_filter: Callable[[str, List[str]], None],
    selected_categories: Optional[List[str]] = None,
    search_query: str = "",
    key_prefix: str = "book_filter"
):
    """
    Render filters for books (search and category selection).
    
    Args:
        categories: List of available categories
        on_filter: Callback when filters are changed, receives (search_query, selected_categories)
        selected_categories: Initially selected categories
        search_query: Initial search query
        key_prefix: Prefix for Streamlit keys
    """
    with st.container(border=True):
        st.markdown("### Filter Books")
        
        # Search box
        new_search = st.text_input(
            "Search by title or author",
            value=search_query,
            key=f"{key_prefix}_search"
        )
        
        # Category multiselect
        new_categories = st.multiselect(
            "Filter by categories",
            options=categories,
            default=selected_categories or [],
            key=f"{key_prefix}_categories"
        )
        
        # Apply filters button
        if st.button(
            "Apply Filters", 
            key=f"{key_prefix}_apply",
            use_container_width=True
        ):
            on_filter(new_search, new_categories)