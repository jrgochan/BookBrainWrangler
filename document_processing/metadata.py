"""
Metadata extraction utilities for document processing.
"""

import re
from typing import Dict, List, Any, Optional

from utils.logger import get_logger
from utils.text_processing import cleanup_text

# Get a logger for this module
logger = get_logger(__name__)

# Common metadata extraction patterns
DEFAULT_METADATA_PATTERNS = {
    'title': [
        r'title:\s*([^\n]+)',
        r'^(?:book\s+)?title[:\s]+([^\n]+)',
        r'(?:^|\n)([A-Z][^\n]{5,50})(?:\n|$)',  # Capitalized line that could be a title
    ],
    'author': [
        r'(?:author|by)(?:s)?:\s*([^\n]+)',
        r'(?:written|published)\s+by\s+([^\n]+)',
        r'©\s*([^\n]+)',  # Copyright symbol followed by name
    ],
    'categories': [
        r'(?:category|categories|genre|genres|subject|subjects):\s*([^\n]+)',
        r'(?:keywords|tags):\s*([^\n]+)'
    ]
}

def extract_metadata(content: Optional[str], patterns: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
    """
    Extract book metadata (title, author, categories) from document content.
    
    Args:
        content: The text content to extract metadata from, can be None
        patterns: Optional dictionary of regex patterns for metadata extraction
        
    Returns:
        A dictionary with metadata fields:
        {
            'title': Extracted title or None if not found,
            'author': Extracted author or None if not found,
            'categories': List of extracted categories or empty list if none found
        }
    """
    if not content:
        return {
            'title': None,
            'author': None,
            'categories': []
        }
    
    # Use default patterns if none provided
    if not patterns:
        patterns = DEFAULT_METADATA_PATTERNS
    
    # Initialize metadata dictionary
    metadata = {
        'title': None,
        'author': None,
        'categories': []
    }
    
    # Clean up the text for better matching
    clean_content = cleanup_text(content)
    
    # Extract title
    for pattern in patterns.get('title', []):
        match = re.search(pattern, clean_content, re.IGNORECASE | re.MULTILINE)
        if match:
            metadata['title'] = match.group(1).strip()
            break
            
    # Extract author
    for pattern in patterns.get('author', []):
        match = re.search(pattern, clean_content, re.IGNORECASE | re.MULTILINE)
        if match:
            metadata['author'] = match.group(1).strip()
            break
            
    # Extract categories
    for pattern in patterns.get('categories', []):
        match = re.search(pattern, clean_content, re.IGNORECASE | re.MULTILINE)
        if match:
            # Split categories by commas and clean up each one
            categories = [c.strip() for c in match.group(1).split(',')]
            # Filter out empty strings
            categories = [c for c in categories if c]
            # Limit to a reasonable number of categories
            metadata['categories'] = categories[:10]
            break
    
    # Fall back to simple heuristics for title if not found
    if not metadata['title'] and len(clean_content) > 20:
        # Try to use the first line as title if it's reasonably short
        first_line = clean_content.split('\n', 1)[0].strip()
        if 5 <= len(first_line) <= 100:
            metadata['title'] = first_line
    
    return metadata