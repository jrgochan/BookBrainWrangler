"""
UI Pages for Book Knowledge AI application.
"""

from pages.book_management import render_book_management_page
from pages.knowledge_base import render_knowledge_base_page
from pages.chat_with_ai import render_chat_with_ai_page
from pages.knowledge_base_explorer import render_knowledge_base_explorer_page
from pages.word_cloud_generator import render_word_cloud_generator_page
from pages.document_heatmap import render as render_document_heatmap_page
from pages.settings import render_settings_page

__all__ = [
    'render_book_management_page',
    'render_knowledge_base_page',
    'render_chat_with_ai_page',
    'render_knowledge_base_explorer_page',
    'render_word_cloud_generator_page',
    'render_document_heatmap_page',
    'render_settings_page',
]