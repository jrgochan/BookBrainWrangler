"""
UI components for the Archive Search page.
"""
import streamlit as st
from typing import Dict, List, Any

def load_custom_css():
    styles = """
    <style>
    /* Modern card styling */
    .modern-card {
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s, box-shadow 0.2s;
        background-color: white;
    }
    .modern-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
    }
    .search-form {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        margin-bottom: 2rem;
    }
    .book-item {
        background-color: white;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        transition: box-shadow 0.2s;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .book-item:hover {
        box-shadow: 0 4px 15px rgba(30, 136, 229, 0.15);
    }
    .book-cover-container {
        position: relative;
        padding-top: 0;
        overflow: hidden;
        text-align: center;
        background-color: #f5f8fa;
    }
    .book-details {
        padding: 0.8rem;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
    }
    .book-title {
        font-size: 1rem;
        font-weight: bold;
        margin-bottom: 0.4rem;
        color: #2c3e50;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }
    .book-author {
        font-size: 0.8rem;
        color: #546e7a;
        margin-bottom: 0.4rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .book-meta {
        font-size: 0.75rem;
        color: #78909c;
        margin-bottom: 0.6rem;
    }
    .book-actions {
        padding: 0.6rem;
        border-top: 1px solid #f1f1f1;
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        margin-top: auto;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 4px;
        margin-right: 0.5rem;
    }
    .badge-success {
        background-color: #e3fcef;
        color: #0c7742;
    }
    .badge-info {
        background-color: #e1f5fe;
        color: #0277bd;
    }
    .badge-warning {
        background-color: #fff8e1;
        color: #ff8f00;
    }
    .console-container {
        border-radius: 8px;
        margin-top: 1.5rem;
        position: relative;
    }
    .search-container {
        position: relative;
    }
    .search-icon {
        position: absolute;
        left: 10px;
    }
    </style>
    """
    st.markdown(styles, unsafe_allow_html=True)

def display_results_grid(
    results: List[Dict[str, Any]],
    covers: Dict[str, str],
    archive_client,
    document_processor,
    book_manager,
    knowledge_base,
    add_log,
):
    # Implementation goes here (moved from archive_search_new.py)
    pass

def display_book_card(
    book: Dict[str, Any],
    cover_url: str,
    already_exists: bool,
    archive_client,
    document_processor,
    book_manager,
    knowledge_base,
    add_log,
):
    # Implementation goes here (moved from archive_search_new.py)
    pass

def show_download_modal(
    book: Dict[str, Any],
    format_type: str,
    archive_client,
    document_processor,
    book_manager,
    knowledge_base,
    add_log,
):
    # Implementation goes here (moved from archive_search_new.py)
    pass

def bulk_download_modal(
    results: List[Dict[str, Any]],
    archive_client,
    document_processor,
    book_manager,
    knowledge_base,
    add_log,
):
    # Implementation goes here (moved from archive_search_new.py)
    pass
