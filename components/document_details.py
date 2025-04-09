"""
Document details component for the application.
Provides a detailed view of a document from the knowledge base.
"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re
from typing import Dict, Any, List, Optional


def render_document_details(document_id: str, knowledge_base: Any, on_back: Optional[callable] = None):
    """
    Render a detailed view of a document in the knowledge base.
    
    Args:
        document_id: ID of the document to display
        knowledge_base: Knowledge base instance to retrieve the document
        on_back: Optional callback function to call when back button is clicked
    """
    document = knowledge_base.get_document(document_id)
    
    if not document:
        st.error("Document not found.")
        if st.button("Back to document list", key="back_from_error"):
            if on_back:
                on_back()
            else:
                st.session_state.selected_document = None
                st.rerun()
        return
    
    # Main document container with custom styling
    with st.container():
        # Document title and back button
        col1, col2 = st.columns([5, 1])
        with col1:
            doc_title = document.get("metadata", {}).get("title", "Document")
            st.title(f"{doc_title}")
            
        with col2:
            if st.button("← Back", key="back_to_document_list"):
                if on_back:
                    on_back()
                else:
                    st.session_state.selected_document = None
                    st.rerun()

        # Divider
        st.markdown("---")
        
        # Document stats
        st.subheader("Document Overview")
        
        # Create columns for stats
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        
        with stat_col1:
            text_length = len(document.get("text", ""))
            st.metric("Text Length", f"{text_length:,} chars")
        
        with stat_col2:
            chunk_count = len(document.get("chunks", []))
            st.metric("Knowledge Chunks", chunk_count)
        
        with stat_col3:
            # Get estimate of reading time (average reading speed: 200 words per minute)
            word_count = len(document.get("text", "").split())
            reading_time = max(1, round(word_count / 200))
            st.metric("Est. Reading Time", f"{reading_time} min")

        # Metadata section with better formatting
        st.subheader("Metadata")
        
        # Format metadata in a more readable way
        metadata = document.get("metadata", {})
        metadata_cols = st.columns(2)
        
        with metadata_cols[0]:
            if "title" in metadata:
                st.info(f"**Title:** {metadata['title']}")
            if "author" in metadata:
                st.info(f"**Author:** {metadata['author']}")
            if "date_created" in metadata:
                st.info(f"**Date Created:** {metadata['date_created']}")
                
        with metadata_cols[1]:
            if "pages" in metadata:
                st.info(f"**Pages:** {metadata['pages']}")
            if "language" in metadata:
                st.info(f"**Language:** {metadata['language']}")
            if "source" in metadata:
                st.info(f"**Source:** {metadata['source']}")
        
        # Show JSON if there are more metadata fields
        with st.expander("Show all metadata", expanded=False):
            st.json(metadata)
        
        # Content preview with word highlighting
        st.subheader("Content Preview")
        preview_text = document["text"][:500] + "..." if len(document["text"]) > 500 else document["text"]
        st.markdown(f"```\n{preview_text}\n```")
        
        # Full text with better formatting
        with st.expander("Show full text", expanded=False):
            # Add a search box
            search_term = st.text_input("Search in document", key="doc_search")
            full_text = document["text"]
            
            if search_term:
                # Highlight search term
                highlighted_text = re.sub(
                    f'({re.escape(search_term)})',
                    r'**\1**',
                    full_text,
                    flags=re.IGNORECASE
                )
                st.markdown(highlighted_text)
            else:
                # Split into paragraphs for better readability
                paragraphs = full_text.split('\n\n')
                for p in paragraphs:
                    if p.strip():
                        st.markdown(p)
                        st.markdown("---")
        
        # Knowledge chunks with visualization
        st.subheader("Knowledge Chunks")
        
        # Add tab view for different ways to explore chunks
        chunk_tab1, chunk_tab2 = st.tabs(["List View", "Analysis"])
        
        with chunk_tab1:
            # Enhanced chunk display
            for i, chunk in enumerate(document.get("chunks", [])):
                with st.expander(f"Chunk {i+1} ({len(chunk)} chars)", expanded=i==0 and len(document.get("chunks", [])) > 0):
                    st.markdown(f"```\n{chunk}\n```")
                    
                    # Add copy button
                    if st.button(f"Copy to clipboard", key=f"copy_chunk_{i}"):
                        st.info(f"Chunk {i+1} copied to clipboard!")
        
        with chunk_tab2:
            # Display a word frequency visualization or other analysis
            st.info("Chunk frequency analysis")
            
            # Calculate word frequencies
            if document.get("chunks", []):
                all_text = " ".join(document.get("chunks", []))
                
                # Use the analyze_word_frequency function from utils
                from utils.text_processing import analyze_word_frequency
                
                # Get the top 20 words with at least 3 characters
                top_words = analyze_word_frequency(
                    text=all_text,
                    min_length=3,
                    max_words=20,
                    exclude_stopwords=True
                )
                
                if top_words:
                    # Create a horizontal bar chart
                    df = pd.DataFrame(top_words, columns=['Word', 'Frequency'])
                    
                    # Create and display the chart
                    fig, ax = plt.subplots(figsize=(10, 5))
                    bars = ax.barh(df['Word'], df['Frequency'])
                    ax.set_title('Most Frequent Words')
                    ax.set_xlabel('Frequency')
                    plt.tight_layout()
                    
                    st.pyplot(fig)
        
        # Actions section
        st.subheader("Document Actions")
        action_col1, action_col2, action_col3 = st.columns(3)
        
        with action_col1:
            if st.button("📝 Edit Metadata", key="edit_doc_metadata"):
                st.session_state.editing_metadata = True
                st.info("Metadata editing is not implemented in this demo.")
        
        with action_col2:
            if st.button("🔍 Find Similar", key="find_similar_docs"):
                st.info("Similar document search is not implemented in this demo.")
        
        with action_col3:
            if st.button("🗑️ Delete Document", key="delete_doc_confirm"):
                # Add a confirmation dialog
                st.warning("Are you sure you want to delete this document?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Yes, delete", key="confirm_delete"):
                        knowledge_base.delete_document(document_id)
                        st.success(f"Document '{doc_title}' deleted from knowledge base.")
                        if on_back:
                            on_back()
                        else:
                            st.session_state.selected_document = None
                            st.rerun()
                with col2:
                    if st.button("Cancel", key="cancel_delete"):
                        st.info("Deletion cancelled.")