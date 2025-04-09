"""
UI module for Book Knowledge AI application.
Contains UI components, pages, and helper functions.
"""

# Import UI pages for easy access
from ui.pages import (
    render_book_management_page,
    render_knowledge_base_page,
    render_knowledge_base_explorer_page,
    render_word_cloud_generator_page,
    render_chat_with_ai_page,
    render_settings_page,
    render_document_heatmap_page,
)

# Export page rendering functions
__all__ = [
    'render_book_management_page',
    'render_knowledge_base_page',
    'render_knowledge_base_explorer_page',
    'render_word_cloud_generator_page',
    'render_chat_with_ai_page',
    'render_settings_page',
    'render_document_heatmap_page',
]