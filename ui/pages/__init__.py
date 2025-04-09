"""
UI Pages package for Book Knowledge AI application.
Contains all application pages used in the Streamlit UI.
"""

# Import page rendering functions for easy access
from ui.pages.book_management import render_book_management_page
from ui.pages.knowledge_base import render_knowledge_base_page
from ui.pages.knowledge_base_explorer import render_knowledge_base_explorer_page
from ui.pages.word_cloud_generator import render_word_cloud_generator_page
from ui.pages.chat_with_ai import render_chat_with_ai_page
from ui.pages.settings import render_settings_page
from ui.pages.document_heatmap import render_document_heatmap_page

# Define what should be exported
__all__ = [
    'render_book_management_page',
    'render_knowledge_base_page',
    'render_knowledge_base_explorer_page',
    'render_word_cloud_generator_page',
    'render_chat_with_ai_page',
    'render_settings_page',
    'render_document_heatmap_page',
]