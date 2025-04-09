"""
Document processor module for Book Knowledge AI.

This module provides a unified interface for processing different document formats,
extracting text, images, and metadata.
"""

import os
import tempfile
import time
from typing import Dict, List, Any, Optional, Union, Callable, Tuple, BinaryIO, IO

from utils.logger import get_logger
from core.exceptions import DocumentProcessingError, DocumentFormatError

# Import format processors
from document_processing.formats import PDFProcessor, DOCXProcessor

# Initialize logger
logger = get_logger(__name__)

class DocumentProcessor:
    """
    Document processor for handling various document formats.
    Provides a unified interface for extracting text and images from documents.
    """
    
    def __init__(self):
        """Initialize the document processor."""
        # Initialize format processors
        self.pdf_processor = PDFProcessor()
        self.docx_processor = DOCXProcessor()
        
        # Initialize supported formats
        self.supported_formats = {
            'pdf': self.pdf_processor,
            'docx': self.docx_processor,
            'doc': self.docx_processor
        }
        
        logger.info("Document processor initialized")
    
    def process_file(
        self,
        file_path: str,
        extract_images: bool = True,
        ocr_enabled: bool = False,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Process a document file and extract its content.
        
        Args:
            file_path: Path to the document file
            extract_images: Whether to extract images
            ocr_enabled: Whether to use OCR for image-based documents
            progress_callback: Optional callback function for progress updates
            
        Returns:
            A dictionary with extracted content
        """
        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip('.')
        
        # Check if format is supported
        if ext not in self.supported_formats:
            error_msg = f"Unsupported document format: {ext}"
            logger.error(error_msg)
            raise DocumentFormatError(error_msg)
        
        try:
            # Get appropriate processor
            processor = self.supported_formats[ext]
            
            # Process the file
            logger.info(f"Processing {ext.upper()} file: {file_path}")
            
            if ext == 'pdf':
                result = processor.process(
                    file_path,
                    extract_images=extract_images,
                    ocr_enabled=ocr_enabled,
                    progress_callback=progress_callback
                )
            else:
                result = processor.process(
                    file_path,
                    extract_images=extract_images,
                    progress_callback=progress_callback
                )
            
            # Add metadata
            result['format'] = ext
            result['filename'] = os.path.basename(file_path)
            result['file_path'] = file_path
            
            # Log success
            logger.info(f"Successfully processed document: {file_path}")
            return result
            
        except DocumentProcessingError as e:
            # Re-raise document processing errors
            raise
            
        except Exception as e:
            # Handle other errors
            error_msg = f"Error processing document {file_path}: {str(e)}"
            logger.error(error_msg)
            raise DocumentProcessingError(error_msg) from e
    
    def process_file_object(
        self,
        file: BinaryIO,
        filename: str,
        extract_images: bool = True,
        ocr_enabled: bool = False,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Process a file object (like an uploaded file) and extract its content.
        
        Args:
            file: File object (bytes stream)
            filename: Original filename
            extract_images: Whether to extract images
            ocr_enabled: Whether to use OCR for image-based documents
            progress_callback: Optional callback function for progress updates
            
        Returns:
            A dictionary with extracted content
        """
        # Get file extension
        _, ext = os.path.splitext(filename)
        ext = ext.lower().lstrip('.')
        
        # Check if format is supported
        if ext not in self.supported_formats:
            error_msg = f"Unsupported document format: {ext}"
            logger.error(error_msg)
            raise DocumentFormatError(error_msg)
        
        # Create a temporary file
        try:
            with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as temp:
                # Write uploaded file to temp file
                file.seek(0)
                temp.write(file.read())
                temp_path = temp.name
            
            # Process the temporary file
            result = self.process_file(
                temp_path,
                extract_images=extract_images,
                ocr_enabled=ocr_enabled,
                progress_callback=progress_callback
            )
            
            # Update metadata
            result['filename'] = filename
            
            # Delete temporary file
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Could not delete temporary file {temp_path}: {str(e)}")
            
            return result
            
        except Exception as e:
            # Clean up temporary file if it exists
            try:
                if 'temp_path' in locals():
                    os.unlink(temp_path)
            except:
                pass
                
            # Handle error
            error_msg = f"Error processing uploaded file {filename}: {str(e)}"
            logger.error(error_msg)
            raise DocumentProcessingError(error_msg) from e
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported document formats.
        
        Returns:
            List of supported format extensions
        """
        return list(self.supported_formats.keys())
    
    def is_format_supported(self, filename: str) -> bool:
        """
        Check if a file format is supported.
        
        Args:
            filename: Filename to check
            
        Returns:
            True if format is supported, False otherwise
        """
        _, ext = os.path.splitext(filename)
        ext = ext.lower().lstrip('.')
        return ext in self.supported_formats
    
    def get_thumbnail(
        self,
        file_path: str,
        width: int = 200,
        height: int = 300
    ) -> Optional[str]:
        """
        Get a thumbnail image for a document.
        
        Args:
            file_path: Path to the document file
            width: Desired width of the thumbnail
            height: Desired height of the thumbnail
            
        Returns:
            Base64 encoded thumbnail image or None if failed
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found for thumbnail: {file_path}")
            return None
        
        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip('.')
        
        # Check if format is supported
        if ext not in self.supported_formats:
            logger.error(f"Unsupported document format for thumbnail: {ext}")
            return None
        
        try:
            # Get appropriate processor
            processor = self.supported_formats[ext]
            
            # Get thumbnail
            logger.info(f"Generating thumbnail for {file_path}")
            return processor.get_thumbnail(file_path, width=width, height=height)
            
        except Exception as e:
            logger.error(f"Error creating thumbnail for {file_path}: {str(e)}")
            return None
            
    def extract_page_as_image(
        self,
        file_path: str,
        page_number: int = 0,
        dpi: int = 200
    ) -> Dict[str, Any]:
        """
        Extract a specific page as an image (PDF only).
        
        Args:
            file_path: Path to the PDF file
            page_number: Page number to extract (0-indexed)
            dpi: DPI for image extraction
            
        Returns:
            Dictionary with image data
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found for page extraction: {file_path}")
            return {'image': None}
        
        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip('.')
        
        # Check if file is PDF
        if ext != 'pdf':
            logger.error(f"Page extraction only supported for PDF files, not {ext}")
            return {'image': None}
        
        try:
            # Extract page as image
            logger.info(f"Extracting page {page_number} from {file_path}")
            return self.pdf_processor.extract_page_as_image(
                file_path,
                page_number=page_number,
                dpi=dpi
            )
            
        except Exception as e:
            logger.error(f"Error extracting page from {file_path}: {str(e)}")
            return {'image': None}
            
    def save_uploaded_file(self, uploaded_file) -> str:
        """
        Save an uploaded file to a temporary directory and return the path.
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            Path to the saved file
        """
        try:
            # Create a temporary directory if it doesn't exist
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Generate a unique filename
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            temp_filename = f"upload_{int(time.time())}{file_ext}"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            # Write file content
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            logger.info(f"Saved uploaded file: {temp_path}")
            return temp_path
            
        except Exception as e:
            error_msg = f"Error saving uploaded file: {str(e)}"
            logger.error(error_msg)
            raise DocumentProcessingError(error_msg) from e