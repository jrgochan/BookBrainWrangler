"""
Main document processor module.
"""

import os
from typing import Dict, List, Any, Optional, Union, Tuple, Callable

from document_processing.ocr import OCR_ENGINES, initialize_ocr_engine
from document_processing.pdf_processor import process_pdf
from document_processing.docx_processor import process_docx  
from document_processing.metadata import extract_metadata
from utils.logger import get_logger
from utils.file_helpers import is_valid_document

# Get a logger for this module
logger = get_logger(__name__)

class DocumentProcessor:
    """
    Document processor for extracting text, images, and metadata from various document formats.
    """
    
    def __init__(self, ocr_engine="pytesseract", ocr_settings=None):
        """
        Initialize the document processor with specified settings.
        
        Args:
            ocr_engine: The OCR engine to use ('pytesseract' or 'easyocr')
            ocr_settings: Dictionary of OCR-specific settings
        """
        # Set default OCR settings if none provided
        self.ocr_settings = ocr_settings or {}
        
        # Set the OCR engine
        self.ocr_engine = ocr_engine if ocr_engine in OCR_ENGINES else "pytesseract"
        
        # Initialize OCR engine
        initialize_ocr_engine(self.ocr_engine, self.ocr_settings)
    
    def extract_content(self, file_path: str, include_images: bool = True, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Extract text and optionally images from a document file (PDF or DOCX).
        
        Args:
            file_path: Path to the document file
            include_images: Whether to include images in the extraction
            progress_callback: Optional callback function for progress updates
            
        Returns:
            A dictionary with extracted content:
            {
                'text': Extracted text as a string,
                'images': List of image descriptions with embedded base64 data (if include_images=True)
            }
        """
        if not is_valid_document(file_path):
            raise ValueError(f"Unsupported file format: {os.path.splitext(file_path)[1]}")
            
        # Determine file type from extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Extract content based on file type
        if file_ext == '.pdf':
            return process_pdf(
                file_path, 
                include_images, 
                self.ocr_engine, 
                self.ocr_settings, 
                progress_callback
            )
        elif file_ext == '.docx':
            return process_docx(file_path, include_images, progress_callback)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def extract_text(self, file_path: str, progress_callback: Optional[Callable] = None) -> str:
        """
        Legacy method to extract only text from a document file.
        Maintained for backward compatibility.
        
        Args:
            file_path: Path to the document file
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Extracted text as a string
        """
        result = self.extract_content(file_path, include_images=False, progress_callback=progress_callback)
        if isinstance(result, dict):
            return result.get('text', '')
        return result
    
    def extract_metadata(self, file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract book metadata (title, author, categories) from a document.
        
        Args:
            file_path: Path to the document file
            content: Optional pre-extracted content to use instead of re-extracting
            
        Returns:
            A dictionary with metadata fields:
            {
                'title': Extracted title or None if not found,
                'author': Extracted author or None if not found,
                'categories': List of extracted categories or empty list if none found
            }
        """
        # If content is not provided, extract it
        if content is None:
            extracted = self.extract_content(file_path, include_images=False)
            if isinstance(extracted, dict):
                content = extracted.get('text', '')
            else:
                content = extracted
        
        # Extract metadata from content using utility function
        return extract_metadata(content)
    
    def get_page_count(self, pdf_path: str) -> int:
        """
        Get the number of pages in a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Number of pages as an integer
        """
        from document_processing.pdf_processor import get_page_count
        return get_page_count(pdf_path)