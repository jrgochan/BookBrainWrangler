"""
Metadata extraction utilities for document processing.
"""

import re
import os
from typing import Dict, List, Any, Optional

from utils.logger import get_logger
from utils.text_processing import cleanup_text

# Get a logger for this module
logger = get_logger(__name__)

# Common metadata extraction patterns with improved robustness
DEFAULT_METADATA_PATTERNS = {
    'title': [
        # Explicit title tags
        r'(?:^|\s)title[\s]*:[\s]*([^\n]+)',
        r'(?:^|\s)(?:book|document)\s+title[\s]*:[\s]*([^\n]+)',
        # Title in document properties (often at start or in header)
        r'^\s*([A-Z][a-zA-Z0-9\s\-\'\":]{10,70})\s*$',  # Document title as first line
        r'(?:^|\n)([A-Z][a-zA-Z0-9\s\'\-\"]{10,70})(?:\n|$)',  # Standalone capitalized line
        # Look for title in first paragraph if capitalized
        r'^.{0,200}?([A-Z][a-zA-Z0-9\s\'\-\"]{10,60})(?:\n|$)',
        # Microsoft Word document property pattern
        r'Title:\s*([^\n]+)',
    ],
    'author': [
        # Common author patterns with length constraints
        r'(?:^|\s)author[\s]*:[\s]*([^,\n]{2,50})',  # Common format with length limit
        r'(?:^|\s)by[\s]*:[\s]*([^,\n]{2,50})',
        r'(?:written|published|authored)\s+by\s+([^,\n]{2,50})',
        r'(?:^|\s)(?:author|written by)[\s]*(?::|name\s*:)\s*([^,\n]{2,50})',
        # Copyright patterns with length constraints
        r'©\s*(?:\d{4})?\s*([^,\n]{2,50})',  # Copyright symbol followed by name
        r'copyright\s+(?:\d{4})?\s+([^,\n]{2,50})',
        # Microsoft Word document property pattern
        r'Author:\s*([^,\n]{2,50})',
    ],
    'categories': [
        # Category-related keywords with improved patterns
        r'(?:^|\s)(?:category|categories)[\s]*:[\s]*([^\n]{2,100})',
        r'(?:^|\s)(?:genre|genres)[\s]*:[\s]*([^\n]{2,100})',
        r'(?:^|\s)(?:subject|subjects)[\s]*:[\s]*([^\n]{2,100})',
        r'(?:^|\s)(?:keywords|tags)[\s]*:[\s]*([^\n]{2,100})',
        r'(?:^|\s)(?:topics)[\s]*:[\s]*([^\n]{2,100})',
    ],
    # New pattern for additional metadata like published date
    'published_date': [
        r'(?:^|\s)(?:published|publication)\s+date[\s]*:[\s]*([^\n]{2,30})',
        r'(?:^|\s)(?:date\s+published)[\s]*:[\s]*([^\n]{2,30})',
        r'\(c\)\s*(\d{4})',  # Copyright year
        r'©\s*(\d{4})',      # Copyright year with symbol
    ]
}

def extract_metadata(content: Optional[str], patterns: Optional[Dict[str, List[str]]] = None, 
                  file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract book metadata (title, author, categories) from document content.
    
    Args:
        content: The text content to extract metadata from, can be None
        patterns: Optional dictionary of regex patterns for metadata extraction
        file_path: Optional path to the source file, used for format-specific extraction
        
    Returns:
        A dictionary with metadata fields:
        {
            'title': Extracted title or None if not found,
            'author': Extracted author or None if not found,
            'categories': List of extracted categories or empty list if none found,
            'published_date': Publication date if found, otherwise None
        }
    """
    if not content:
        return {
            'title': None,
            'author': None,
            'categories': [],
            'published_date': None
        }
    
    # Use default patterns if none provided
    if not patterns:
        patterns = DEFAULT_METADATA_PATTERNS
    
    # Initialize metadata dictionary
    metadata = {
        'title': None,
        'author': None,
        'categories': [],
        'published_date': None
    }
    
    # Clean up the text for better matching
    clean_content = cleanup_text(content)
    
    # Get file type if path is provided
    file_type = None
    if file_path:
        _, ext = os.path.splitext(file_path)
        file_type = ext.lower() if ext else None
    
    # Determine if it's likely a DOCX file based on content or extension
    is_docx = (file_type == '.docx') or ('Content-Type: application/vnd.openxmlformats' in content[:1000])
    
    # For DOCX files, limit the content to search
    search_content = clean_content
    if is_docx:
        # For DOCX files, focus on the first part of the document for metadata
        # This avoids matching author patterns in the body text
        content_limit = min(len(clean_content), 2000)  # Only search first 2000 chars for metadata
        search_content = clean_content[:content_limit]
        logger.debug(f"Processing as DOCX, limiting metadata search to first {content_limit} characters")
    
    # Extract title - prioritize explicit patterns
    title_found = False
    # First try explicit title markers
    for pattern in patterns.get('title', [])[:3]:  # First patterns are explicit title markers
        match = re.search(pattern, search_content, re.IGNORECASE | re.MULTILINE)
        if match:
            metadata['title'] = match.group(1).strip()
            title_found = True
            logger.debug(f"Title found with explicit pattern: {metadata['title']}")
            break
    
    # If no explicit title, try looser patterns
    if not title_found:
        for pattern in patterns.get('title', [])[3:]:  # Remaining patterns are more general
            match = re.search(pattern, search_content, re.IGNORECASE | re.MULTILINE)
            if match:
                metadata['title'] = match.group(1).strip()
                logger.debug(f"Title found with general pattern: {metadata['title']}")
                break
    
    # Extract author - with improved error checking
    for pattern in patterns.get('author', []):
        match = re.search(pattern, search_content, re.IGNORECASE | re.MULTILINE)
        if match:
            author_text = match.group(1).strip()
            # Skip if author seems too long (likely a false positive)
            if len(author_text) <= 50:
                metadata['author'] = author_text
                logger.debug(f"Author found: {metadata['author']}")
                break
            else:
                logger.debug(f"Skipping potential author (too long): {author_text[:30]}...")
    
    # Extract categories
    for pattern in patterns.get('categories', []):
        match = re.search(pattern, search_content, re.IGNORECASE | re.MULTILINE)
        if match:
            # Split categories by commas and clean up each one
            category_text = match.group(1).strip()
            categories = [c.strip() for c in category_text.split(',')]
            # Filter out empty strings
            categories = [c for c in categories if c]
            # Limit to a reasonable number of categories
            metadata['categories'] = categories[:10]
            logger.debug(f"Categories found: {metadata['categories']}")
            break
    
    # Extract published date
    for pattern in patterns.get('published_date', []):
        match = re.search(pattern, search_content, re.IGNORECASE | re.MULTILINE)
        if match:
            metadata['published_date'] = match.group(1).strip()
            logger.debug(f"Published date found: {metadata['published_date']}")
            break
    
    # Fall back to simple heuristics for title if not found
    if not metadata['title'] and len(clean_content) > 20:
        # For DOCX files, try to get the first paragraph as title if it's reasonable
        if is_docx:
            first_para = search_content.split('\n', 1)[0].strip()
            if 5 <= len(first_para) <= 100:
                metadata['title'] = first_para
                logger.debug(f"Using first paragraph as title (DOCX): {metadata['title']}")
        else:
            # For other files, use the first line if it's reasonable
            first_line = clean_content.split('\n', 1)[0].strip()
            if 5 <= len(first_line) <= 100:
                metadata['title'] = first_line
                logger.debug(f"Using first line as title: {metadata['title']}")
    
    # Add source file info if available
    if file_path:
        metadata['source_file'] = os.path.basename(file_path)
    
    return metadata

def extract_metadata_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Extract metadata from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary with metadata fields
    """
    try:
        import PyPDF2
        
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            info = reader.metadata
            
            if info:
                metadata = {
                    'title': info.get('/Title', ''),
                    'author': info.get('/Author', ''),
                    'subject': info.get('/Subject', ''),
                    'creator': info.get('/Creator', ''),
                    'producer': info.get('/Producer', ''),
                    'creation_date': info.get('/CreationDate', '')
                }
                return {k: v for k, v in metadata.items() if v}
            
        return {}
            
    except Exception as e:
        logger.error(f"Error extracting metadata: {e}")
        return {}