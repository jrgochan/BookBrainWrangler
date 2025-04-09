"""
Application configuration settings.
Contains constants and settings for the application.
"""

import os

# Application information
APP_TITLE = "Book Knowledge AI"
APP_ICON = "📚"
APP_LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "expanded"

# Application modes/pages
APP_MODES = [
    "Book Management", 
    "Knowledge Base", 
    "Chat with AI", 
    "Knowledge Base Explorer", 
    "Word Cloud Generator", 
    "Document Heatmap",
    "Settings"
]

# File paths and directories
TEMP_DIR = "temp"
EXPORTS_DIR = "exports"
KNOWLEDGE_BASE_DIR = "knowledge_base_data"

# Create directories if they don't exist
for directory in [TEMP_DIR, EXPORTS_DIR, KNOWLEDGE_BASE_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# OCR settings
DEFAULT_OCR_SETTINGS = {
    'display_interval': 1,
    'confidence_threshold': 70,
    'show_current_image': True,
    'show_extracted_text': True
}

# Thumbnail settings
DEFAULT_THUMBNAIL_SIZE = (200, 280)
DEFAULT_THUMBNAIL_BG_COLOR = (240, 240, 240)
DEFAULT_THUMBNAIL_TEXT_COLOR = (70, 70, 70)

# Ollama settings
DEFAULT_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama2")

# Word Cloud settings
DEFAULT_WORD_CLOUD_SETTINGS = {
    'width': 800,
    'height': 400,
    'max_words': 200,
    'background_color': 'white',
    'colormap': 'viridis',
    'min_font_size': 10
}

# Database settings
DATABASE_FILE = "book_manager.db"