"""
PDF document processor for Book Knowledge AI.
Handles extraction of text and images from PDF files.
"""

import os
import io
import tempfile
from typing import Dict, List, Any, Optional, Callable

try:
    from PyPDF2 import PdfReader
    from pdf2image import convert_from_path, convert_from_bytes
except ImportError:
    # Log the import error, but allow the module to be imported
    import logging
    logging.getLogger(__name__).error("PyPDF2 or pdf2image not installed. PDF processing will not be available.")

from utils.logger import get_logger
from utils.image_helpers import image_to_base64, resize_image
from core.exceptions import DocumentProcessingError

# Get a logger for this module
logger = get_logger(__name__)

def process_pdf(file_path: str, include_images: bool = True, 
                progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """
    Process a PDF file and extract its content.
    
    Args:
        file_path: Path to the PDF file
        include_images: Whether to include images in the extraction
        progress_callback: Optional callback for progress updates
        
    Returns:
        Dictionary with extracted content:
        {
            'text': str,            # Full text content
            'images': List[bytes],  # List of image data in bytes
            'metadata': Dict        # Document metadata
        }
    """
    logger.info(f"Processing PDF file: {file_path}")
    
    try:
        # Extract text
        text_content, num_pages = extract_text_from_pdf(file_path, progress_callback)
        
        # Extract images if requested
        images = []
        if include_images:
            images = extract_images_from_pdf(file_path, progress_callback)
        
        # Extract metadata
        metadata = extract_metadata_from_pdf(file_path, num_pages)
        
        # Return the extracted content
        return {
            'text': text_content,
            'images': images,
            'metadata': metadata
        }
    
    except Exception as e:
        logger.error(f"Error processing PDF file: {str(e)}")
        raise DocumentProcessingError(f"Failed to process PDF file: {str(e)}")

def extract_text_from_pdf(file_path: str, 
                        progress_callback: Optional[Callable] = None) -> tuple[str, int]:
    """
    Extract text from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        progress_callback: Optional callback for progress updates
        
    Returns:
        Tuple of (extracted text, number of pages)
    """
    try:
        # Open the PDF file
        with open(file_path, 'rb') as file:
            reader = PdfReader(file)
            num_pages = len(reader.pages)
            
            # Extract text from each page
            full_text = []
            for i, page in enumerate(reader.pages):
                # Extract text from the page
                text = page.extract_text()
                if text:
                    full_text.append(text)
                
                # Update progress
                if progress_callback:
                    progress_callback(i, num_pages, {
                        "text": f"Extracting text from page {i+1}/{num_pages}",
                        "type": "text_extraction"
                    })
            
            # Join all page texts with double newlines
            return "\n\n".join(full_text), num_pages
    
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return "", 0

def extract_images_from_pdf(file_path: str, 
                          progress_callback: Optional[Callable] = None) -> List[bytes]:
    """
    Extract images from a PDF file using pdf2image.
    This extracts page images rather than embedded images.
    
    Args:
        file_path: Path to the PDF file
        progress_callback: Optional callback for progress updates
        
    Returns:
        List of image data in bytes
    """
    try:
        # Convert PDF pages to images
        images = convert_from_path(
            file_path,
            dpi=150,  # Lower DPI for reasonable file size
            fmt='jpeg',
            transparent=False,
            first_page=1,
            last_page=None  # All pages
        )
        
        # Convert PIL images to bytes
        image_bytes = []
        for i, img in enumerate(images):
            # Save image to byte array
            byte_arr = io.BytesIO()
            img.save(byte_arr, format='JPEG')
            image_bytes.append(byte_arr.getvalue())
            
            # Update progress
            if progress_callback:
                progress_callback(i, len(images), {
                    "text": f"Extracting image from page {i+1}/{len(images)}",
                    "type": "image_extraction"
                })
        
        return image_bytes
    
    except Exception as e:
        logger.error(f"Error extracting images from PDF: {str(e)}")
        return []

def extract_metadata_from_pdf(file_path: str, num_pages: int = 0) -> Dict[str, Any]:
    """
    Extract metadata from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        num_pages: Number of pages in the PDF (if already known)
        
    Returns:
        Dictionary with metadata
    """
    try:
        # Open the PDF file
        with open(file_path, 'rb') as file:
            reader = PdfReader(file)
            
            # Initialize metadata dictionary
            metadata = {}
            
            # Get document info
            info = reader.metadata
            if info:
                # Extract available metadata
                if info.title:
                    metadata['title'] = info.title
                if info.author:
                    metadata['author'] = info.author
                if info.subject:
                    metadata['subject'] = info.subject
                if info.creator:
                    metadata['creator'] = info.creator
                if hasattr(info, 'keywords') and info.keywords:
                    # Split keywords by commas or semicolons
                    keywords = info.keywords
                    keyword_list = [k.strip() for k in keywords.replace(';', ',').split(',') if k.strip()]
                    metadata['categories'] = keyword_list
            
            # Add page count
            if num_pages > 0:
                metadata['page_count'] = num_pages
            else:
                metadata['page_count'] = len(reader.pages)
        
        return metadata
    
    except Exception as e:
        logger.error(f"Error extracting metadata from PDF: {str(e)}")
        return {
            'page_count': num_pages if num_pages > 0 else 0
        }

def get_pdf_thumbnail(file_path: str, width: int = 200) -> Optional[str]:
    """
    Generate a thumbnail for a PDF file.
    
    Args:
        file_path: Path to the PDF file
        width: Width of the thumbnail in pixels
        
    Returns:
        Base64-encoded image data or None if generation fails
    """
    try:
        # Convert first page to image
        images = convert_from_path(
            file_path,
            dpi=72,  # Low DPI for thumbnail
            fmt='jpeg',
            transparent=False,
            first_page=1,
            last_page=1
        )
        
        if images:
            # Get the first page
            first_page = images[0]
            
            # Resize the image
            resized = resize_image(first_page, width=width)
            
            # Convert to base64
            if resized:
                return image_to_base64(resized)
        
        return None
    
    except Exception as e:
        logger.error(f"Error creating PDF thumbnail: {str(e)}")
        return None