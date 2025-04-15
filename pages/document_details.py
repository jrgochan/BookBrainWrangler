"""
Document details page.
This module renders a detailed view of a document from the knowledge base.
"""
import streamlit as st
from components.document_details import render_document_details

def document_details_page(document_id: str, knowledge_base, on_back=None):
    """
    Render the document details page.
    
    Args:
        document_id: ID of the document to display
        knowledge_base: Knowledge base instance
        on_back: Callback function to execute when back button is clicked
    """
    render_document_details(document_id, knowledge_base, on_back)