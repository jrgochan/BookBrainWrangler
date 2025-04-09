"""
Main document processor for Book Knowledge AI.
"""

import os
import io
from typing import Dict, List, Any, Optional, Callable, Union
from pathlib import Path

from utils.logger import get_logger
from core.exceptions import DocumentProcessingError
from document_processing.formats.pdf import process_pdf
# docx processor will be added later
# from document_processing.formats.docx import process_docx

# Get a logger for this module
logger = get_logger(__name__)

class DocumentProcessor:
    """
    Document processor class for handling various document formats.
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the document processor.
        
        Args:
            temp_dir: Directory for temporary files
        """
        self.temp_dir = temp_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        logger.info(f"Initialized DocumentProcessor with temp_dir: {self.temp_dir}")
    
    def process(self, file_path: str, file_type: Optional[str] = None, 
                use_ocr: bool = False, include_images: bool = True,
                progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Process a document file and extract content.
        
        Args:
            file_path: Path to the document file
            file_type: Type of document (auto-detected if None)
            use_ocr: Whether to use OCR for text extraction
            include_images: Whether to include images in the extraction
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary with extracted content
        """
        # Get file type from path if not provided
        if file_type is None:
            file_type = self._detect_file_type(file_path)
        
        logger.info(f"Processing document: {file_path} (type: {file_type})")
        
        # Process based on file type
        if file_type.lower() == 'pdf':
            return process_pdf(file_path, use_ocr, include_images, progress_callback)
        elif file_type.lower() in ['docx', 'doc']:
            # Temporary workaround until docx processor is implemented
            logger.warning(f"DOCX processing not fully implemented yet. Using fallback method for {file_path}")
            return {
                'text': f"DOCX processing not fully implemented yet. File: {file_path}",
                'images': []
            }
        else:
            raise DocumentProcessingError(f"Unsupported file type: {file_type}")
    
    def _detect_file_type(self, file_path: str) -> str:
        """
        Detect file type from path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File type as a string (pdf, docx, etc.)
        """
        file_extension = os.path.splitext(file_path)[1].lower().lstrip('.')
        
        # Map common extensions to standardized file types
        extension_map = {
            'pdf': 'pdf',
            'docx': 'docx',
            'doc': 'doc',
            'txt': 'txt',
            'md': 'md',
            'epub': 'epub'
        }
        
        return extension_map.get(file_extension, file_extension)
    
    def get_thumbnail(self, file_path: str, file_type: Optional[str] = None, 
                     page: int = 1, width: int = 200) -> Optional[str]:
        """
        Generate a thumbnail for a document.
        
        Args:
            file_path: Path to the document file
            file_type: Type of document (auto-detected if None)
            page: Page number for the thumbnail
            width: Width of the thumbnail in pixels
            
        Returns:
            Base64-encoded image data or None if generation fails
        """
        # Get file type from path if not provided
        if file_type is None:
            file_type = self._detect_file_type(file_path)
        
        # Generate thumbnail based on file type
        try:
            if file_type.lower() == 'pdf':
                from document_processing.formats.pdf import get_pdf_thumbnail
                return get_pdf_thumbnail(file_path, page, width)
            # Add handlers for other file types as needed
            else:
                logger.warning(f"Thumbnail generation not supported for file type: {file_type}")
                return None
        except Exception as e:
            logger.error(f"Error generating thumbnail: {str(e)}")
            return None