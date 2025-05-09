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
        
        # Check processor availability
        available_formats = []
        if self.pdf_processor.is_available():
            available_formats.append('pdf')
        if self.docx_processor.is_available():
            available_formats.extend(['docx', 'doc'])
            
        if not available_formats:
            logger.warning("No document processors are fully available. Document processing may be limited.")
        else:
            logger.info(f"Document processor initialized with available formats: {', '.join(available_formats)}")
    
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
            return {
                'text': '',
                'images': [],
                'error': error_msg,
                'warnings': [error_msg],
                'format': None,
                'filename': os.path.basename(file_path),
                'file_path': file_path
            }
        
        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip('.')
        
        # Check if format is supported
        if ext not in self.supported_formats:
            error_msg = f"Unsupported document format: {ext}"
            logger.error(error_msg)
            return {
                'text': '',
                'images': [],
                'error': error_msg,
                'warnings': [error_msg],
                'format': ext,
                'filename': os.path.basename(file_path),
                'file_path': file_path
            }
        
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
            
            # Ensure 'error' and 'warnings' fields are present
            if 'error' not in result:
                result['error'] = ''
            if 'warnings' not in result:
                result['warnings'] = []
            # Add metadata
            result['format'] = ext
            result['filename'] = os.path.basename(file_path)
            result['file_path'] = file_path
            
            # Log success or error
            if result['error']:
                logger.error(f"Error in processor result for {file_path}: {result['error']}")
            else:
                logger.info(f"Successfully processed document: {file_path}")
            return result
        except Exception as e:
            # Handle all errors gracefully
            error_msg = f"Error processing document {file_path}: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            return {
                'text': '',
                'images': [],
                'error': error_msg,
                'warnings': [error_msg],
                'format': ext,
                'filename': os.path.basename(file_path),
                'file_path': file_path
            }
    
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
        
        # Log the file info
        file_size = file.seek(0, os.SEEK_END)
        file.seek(0)  # Reset file pointer to beginning
        logger.info(f"Processing uploaded file: {filename}, format: {ext}, size: {file_size} bytes")
        
        # Create a temporary file
        try:
            with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as temp:
                # Write uploaded file to temp file
                file.seek(0)
                content = file.read()
                temp.write(content)
                temp_path = temp.name
                
                logger.info(f"Saved uploaded file to temporary path: {temp_path}, size: {len(content)} bytes")
                
                # For DOCX files, let's check if the file looks valid
                if ext in ['docx', 'doc']:
                    if len(content) < 100:
                        logger.warning(f"DOCX file is suspiciously small ({len(content)} bytes). May be corrupted.")
                    
                    # Check for DOCX signature (PKZip)
                    if not content.startswith(b'PK'):
                        logger.warning(f"DOCX file doesn't have the correct signature. May not be a valid DOCX file.")
            
            # Process the temporary file
            logger.info(f"Starting processing of temporary file: {temp_path}")
            result = self.process_file(
                temp_path,
                extract_images=extract_images,
                ocr_enabled=ocr_enabled,
                progress_callback=progress_callback
            )
            
            # Log the extraction results
            text_length = len(result.get('text', ''))
            images_count = len(result.get('images', []))
            logger.info(f"Extraction results: {text_length} characters of text, {images_count} images")
            
            # For debugging: if no text was extracted, provide extra details
            if text_length == 0:
                logger.warning(f"No text was extracted from {filename}. Check if file is corrupted or empty.")
                if ext in ['docx', 'doc']:
                    logger.info("For DOCX files with 0 characters, check if:") 
                    logger.info("1. The file is password-protected")
                    logger.info("2. The file contains only images or is a scanned document")
                    logger.info("3. The file is corrupted or in an unsupported format")
            
            # Update metadata
            result['filename'] = filename
            result['original_size'] = file_size
            
            # Delete temporary file
            try:
                os.unlink(temp_path)
                logger.debug(f"Deleted temporary file: {temp_path}")
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
            import traceback
            logger.error(f"Error traceback: {traceback.format_exc()}")
            
            # Create a result with error information
            result = {
                'text': '',
                'images': [],
                'error': str(e),
                'filename': filename,
                'format': ext
            }
            return result
    
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
            
    def process_document(
        self,
        file_path: str,
        include_images: bool = True,
        ocr_enabled: bool = False,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Process a document file and extract its content.
        This is an alias for process_file to maintain backward compatibility.
        
        Args:
            file_path: Path to the document file
            include_images: Whether to extract images
            ocr_enabled: Whether to use OCR for image-based documents
            progress_callback: Optional callback function for progress updates
            
        Returns:
            A dictionary with extracted content
        """
        # Just call process_file with the same parameters
        return self.process_file(
            file_path,
            extract_images=include_images,
            ocr_enabled=ocr_enabled,
            progress_callback=progress_callback
        )
