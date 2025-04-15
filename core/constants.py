"""
Application-wide constants for Book Knowledge AI.
"""

# Application version
APP_VERSION = "1.0.0"

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

# OCR engines
OCR_ENGINES = ["pytesseract", "easyocr"]

# File extensions
SUPPORTED_EXTENSIONS = {
    'pdf': ['pdf'],
    'docx': ['docx'],
    'image': ['jpg', 'jpeg', 'png', 'tiff', 'bmp']
}