"""
Application configuration settings.
Contains constants and settings for the application.
"""

# Application information
APP_TITLE = "Book Knowledge AI"
APP_ICON = "📚"
APP_VERSION = "1.0.0"

# Layout settings
APP_LAYOUT = "wide"  # "wide" or "centered"
INITIAL_SIDEBAR_STATE = "expanded"  # "expanded" or "collapsed"

# Navigation modes
APP_MODES = [
    "Book Management",
    "Knowledge Base",
    "Chat with AI",
    "Knowledge Base Explorer",
    "Word Cloud Generator",
    "Document Heatmap",
    "Settings"
]

# Default paths
DEFAULT_DATA_PATH = "data"
DEFAULT_EXPORT_PATH = "exports"
DEFAULT_TEMP_PATH = "temp"
DEFAULT_KB_PATH = "knowledge_base_data"

# OCR settings
DEFAULT_OCR_ENGINE = "pytesseract"
DEFAULT_OCR_CONFIDENCE_THRESHOLD = 70.0  # percentage
DEFAULT_OCR_DISPLAY_INTERVAL = 5  # show every 5th page

# Ollama settings
DEFAULT_OLLAMA_MODEL = "llama2"
DEFAULT_OLLAMA_SERVER_URL = "http://localhost:11434"
DEFAULT_OLLAMA_TEMPERATURE = 0.7
DEFAULT_OLLAMA_CONTEXT_WINDOW = 4096

# Knowledge base settings
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_EMBEDDING_MODEL = "default"
DEFAULT_VECTOR_SIMILARITY_METRIC = "cosine"

# UI settings
DEFAULT_THUMBNAIL_SIZE = 150