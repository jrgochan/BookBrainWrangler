"""
Knowledge Base management page for the application.
This page allows users to manage which books are included in the knowledge base.
"""

import streamlit as st
import time
from typing import List, Dict, Any

from utils.logger import get_logger
from ui.components.book_list import render_book_list

# Get a logger for this module
logger = get_logger(__name__)

def render_knowledge_base_page(book_manager, knowledge_base):
    """
    Render the Knowledge Base management page.
    
    Args:
        book_manager: The BookManager instance
        knowledge_base: The KnowledgeBase instance
    """
    logger.info("Rendering Knowledge Base page")
    st.title("Knowledge Base")
    
    # Display basic information about the knowledge base
    render_kb_info(knowledge_base)
    
    # Display books section for knowledge base management
    render_kb_books_section(book_manager, knowledge_base)

def render_kb_info(knowledge_base):
    """
    Render information about the knowledge base.
    
    Args:
        knowledge_base: The KnowledgeBase instance
    """
    logger.debug("Rendering knowledge base info")
    
    # Create info metrics in columns
    col1, col2, col3 = st.columns(3)
    
    # Get document IDs from knowledge base
    try:
        kb_doc_ids = knowledge_base.get_document_ids()
        book_ids = [doc_id for doc_id in kb_doc_ids if doc_id.startswith("book_")]
        
        with col1:
            st.metric("Books in Knowledge Base", len(book_ids))
        
        with col2:
            # Additional metrics could go here in the future
            st.metric("Vector Database Size", f"{len(kb_doc_ids)} documents")
        
        with col3:
            # Placeholder for future metrics
            st.metric("Status", "Active")
    
    except Exception as e:
        logger.error(f"Error getting knowledge base stats: {str(e)}")
        st.error(f"Error retrieving knowledge base information: {str(e)}")
    
    # Information about the knowledge base
    with st.expander("About the Knowledge Base", expanded=False):
        st.markdown("""
        The knowledge base is a collection of documents that are indexed for AI retrieval and analysis.
        
        When a book is added to the knowledge base:
        
        1. Its text is processed and divided into smaller chunks
        2. Each chunk is converted into a numerical vector that represents its meaning
        3. These vectors are stored in a vector database for efficient retrieval
        4. The AI can then find and use relevant portions of these documents during conversations
        
        Only books that are added to the knowledge base will be available during chat interactions.
        """)

def render_kb_books_section(book_manager, knowledge_base):
    """
    Render the section for managing books in the knowledge base.
    
    Args:
        book_manager: The BookManager instance
        knowledge_base: The KnowledgeBase instance
    """
    logger.debug("Rendering knowledge base books section")
    
    st.subheader("Manage Books in Knowledge Base")
    
    # Get all books
    all_books = book_manager.get_all_books()
    
    # Get indexed books
    try:
        indexed_book_ids = knowledge_base.get_document_ids()
        indexed_book_ids = [id.replace("book_", "") for id in indexed_book_ids if id.startswith("book_")]
        indexed_book_ids = [int(id) for id in indexed_book_ids if id.isdigit()]
    except Exception as e:
        logger.error(f"Error getting indexed book IDs: {str(e)}")
        indexed_book_ids = []
    
    # Check if any books exist
    if not all_books:
        st.info("No books found in your library. Upload a book in the Book Management page to get started!")
        return
    
    # Create tabs for different views
    kb_tabs = st.tabs(["All Books", "In Knowledge Base", "Not in Knowledge Base"])
    
    # Filter books based on selected tab
    with kb_tabs[0]:
        render_kb_book_list(all_books, indexed_book_ids, book_manager, knowledge_base, "all")
    
    with kb_tabs[1]:
        kb_books = [b for b in all_books if b["id"] in indexed_book_ids]
        if not kb_books:
            st.info("No books are currently in the knowledge base. Add books to enable AI interactions.")
        else:
            render_kb_book_list(kb_books, indexed_book_ids, book_manager, knowledge_base, "in_kb")
    
    with kb_tabs[2]:
        non_kb_books = [b for b in all_books if b["id"] not in indexed_book_ids]
        if not non_kb_books:
            st.success("All books are in the knowledge base!")
        else:
            render_kb_book_list(non_kb_books, indexed_book_ids, book_manager, knowledge_base, "not_in_kb")

def render_kb_book_list(books, indexed_book_ids, book_manager, knowledge_base, view_type):
    """
    Render a book list with knowledge base management controls.
    
    Args:
        books: List of book dictionaries
        indexed_book_ids: List of book IDs in the knowledge base
        book_manager: The BookManager instance
        knowledge_base: The KnowledgeBase instance
        view_type: Type of view ("all", "in_kb", "not_in_kb")
    """
    # Add bulk action controls for each view type
    if view_type == "not_in_kb" and books:
        if st.button("Add All to Knowledge Base", key=f"add_all_kb_{view_type}", type="primary"):
            with st.status("Adding books to knowledge base...", expanded=True) as status:
                success_count = 0
                for book in books:
                    try:
                        st.write(f"Processing: {book['title']}")
                        
                        # Get book content
                        content = book_manager.get_book_content(book["id"])
                        if not content:
                            st.error(f"Content not found for '{book['title']}'")
                            continue
                        
                        # Add to knowledge base
                        success = knowledge_base.add_document(
                            document_id=f"book_{book['id']}",
                            text=content,
                            metadata={
                                "title": book["title"],
                                "author": book["author"],
                                "categories": book["categories"],
                                "source": "book",
                                "book_id": book["id"]
                            }
                        )
                        
                        if success:
                            success_count += 1
                            st.write(f"✅ Added '{book['title']}' to knowledge base")
                            logger.info(f"Added book {book['id']} to knowledge base")
                        else:
                            st.error(f"Failed to add '{book['title']}' to knowledge base")
                            logger.error(f"Failed to add book {book['id']} to knowledge base")
                            
                    except Exception as e:
                        st.error(f"Error adding '{book['title']}' to knowledge base: {str(e)}")
                        logger.error(f"Error adding book {book['id']} to knowledge base: {str(e)}")
                
                # Final status update
                if success_count > 0:
                    status.update(label=f"Added {success_count} books to knowledge base", state="complete")
                    time.sleep(1)
                    st.rerun()
                else:
                    status.update(label="Failed to add any books to knowledge base", state="error")
    
    elif view_type == "in_kb" and books:
        if st.button("Remove All from Knowledge Base", key=f"remove_all_kb_{view_type}", type="primary"):
            with st.status("Removing books from knowledge base...", expanded=True) as status:
                success_count = 0
                for book in books:
                    try:
                        st.write(f"Processing: {book['title']}")
                        
                        # Remove from knowledge base
                        success = knowledge_base.remove_document(f"book_{book['id']}")
                        
                        if success:
                            success_count += 1
                            st.write(f"✅ Removed '{book['title']}' from knowledge base")
                            logger.info(f"Removed book {book['id']} from knowledge base")
                        else:
                            st.error(f"Failed to remove '{book['title']}' from knowledge base")
                            logger.error(f"Failed to remove book {book['id']} from knowledge base")
                            
                    except Exception as e:
                        st.error(f"Error removing '{book['title']}' from knowledge base: {str(e)}")
                        logger.error(f"Error removing book {book['id']} from knowledge base: {str(e)}")
                
                # Final status update
                if success_count > 0:
                    status.update(label=f"Removed {success_count} books from knowledge base", state="complete")
                    time.sleep(1)
                    st.rerun()
                else:
                    status.update(label="Failed to remove any books from knowledge base", state="error")
    
    # Define callback function for toggling KB status
    def on_toggle_kb(book_id, is_in_kb):
        if is_in_kb:
            # Remove from knowledge base
            try:
                success = knowledge_base.remove_document(f"book_{book_id}")
                if success:
                    st.success(f"Book removed from knowledge base")
                    logger.info(f"Book {book_id} removed from knowledge base")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Failed to remove book from knowledge base")
                    logger.error(f"Failed to remove book {book_id} from knowledge base")
            except Exception as e:
                st.error(f"Error removing book from knowledge base: {str(e)}")
                logger.error(f"Error removing book {book_id} from knowledge base: {str(e)}")
        else:
            # Add to knowledge base
            try:
                # Get book content
                content = book_manager.get_book_content(book_id)
                if not content:
                    st.error("Book content not found")
                    return
                
                # Get book details for metadata
                book = next((b for b in books if b["id"] == book_id), None)
                if not book:
                    st.error("Book details not found")
                    return
                
                # Add to knowledge base
                success = knowledge_base.add_document(
                    document_id=f"book_{book_id}",
                    text=content,
                    metadata={
                        "title": book["title"],
                        "author": book["author"],
                        "categories": book["categories"],
                        "source": "book",
                        "book_id": book_id
                    }
                )
                
                if success:
                    st.success(f"Book added to knowledge base")
                    logger.info(f"Book {book_id} added to knowledge base")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Failed to add book to knowledge base")
                    logger.error(f"Failed to add book {book_id} to knowledge base")
                    
            except Exception as e:
                st.error(f"Error adding book to knowledge base: {str(e)}")
                logger.error(f"Error adding book {book_id} to knowledge base: {str(e)}")
    
    # Initialize thumbnail cache if it doesn't exist
    if 'thumbnail_cache' not in st.session_state:
        st.session_state.thumbnail_cache = {}
    
    # Render the book list component
    render_book_list(
        books, 
        on_toggle_kb=on_toggle_kb,
        indexed_books=indexed_book_ids,
        thumbnail_cache=st.session_state.thumbnail_cache,
        show_toggle_kb=True
    )