"""
Configuration module for Book Knowledge AI.
Centralizes application settings and config management.
"""

import os
from typing import Dict, Any, Optional

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

# Application configurations
_config = {
    'ocr': DEFAULT_OCR_SETTINGS,
    'thumbnail': {
        'size': DEFAULT_THUMBNAIL_SIZE,
        'bg_color': DEFAULT_THUMBNAIL_BG_COLOR,
        'text_color': DEFAULT_THUMBNAIL_TEXT_COLOR
    },
    'ollama': {
        'host': DEFAULT_OLLAMA_HOST,
        'model': DEFAULT_OLLAMA_MODEL
    },
    'word_cloud': DEFAULT_WORD_CLOUD_SETTINGS,
    'database': {
        'file': DATABASE_FILE
    },
    'dirs': {
        'temp': TEMP_DIR,
        'exports': EXPORTS_DIR,
        'knowledge_base': KNOWLEDGE_BASE_DIR
    }
}

def get_config(section: Optional[str] = None) -> Dict[str, Any]:
    """
    Get application configuration.
    
    Args:
        section: Optional section name to retrieve specific config
        
    Returns:
        Dictionary with config values
    """
    if section is not None:
        return _config.get(section, {})
    return _config

def update_config(section: str, key: str, value: Any) -> None:
    """
    Update a config value.
    
    Args:
        section: Config section name
        key: Config key
        value: New value
    """
    if section in _config:
        if isinstance(_config[section], dict):
            _config[section][key] = value
        else:
            # If the section isn't a dict, replace it entirely
            _config[section] = value