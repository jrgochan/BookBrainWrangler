"""
Document processor for Book Knowledge AI.
Handles extraction and processing of document content.
"""

import os
import io
import tempfile
from typing import Dict, List, Any, Optional, Union, BinaryIO, Tuple
from datetime import datetime

from utils.logger import get_logger
from core.exceptions import DocumentProcessingError

# Get a logger for this module
logger = get_logger(__name__)

class DocumentProcessor:
    """
    Document processor for handling different document formats.
    Provides a unified interface for extracting text, metadata, and images.
    """
    
    def __init__(self, temp_dir: str = None):
        """
        Initialize the document processor.
        
        Args:
            temp_dir: Directory for temporary files
        """
        self.temp_dir = temp_dir or "temp"
        
        # Create temp directory if it doesn't exist
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Initialize format handlers
        self._initialize_format_handlers()
    
    def _initialize_format_handlers(self):
        """Initialize format-specific handlers."""
        self.format_handlers = {}
        
        # Lazy-load format handlers to avoid circular imports
        def get_pdf_handler():
            from document_processing.formats.pdf import PDFProcessor
            return PDFProcessor()
        
        def get_docx_handler():
            from document_processing.formats.docx import DOCXProcessor
            return DOCXProcessor()
        
        def get_txt_handler():
            from document_processing.formats.text import TextProcessor
            return TextProcessor()
        
        # Register handlers
        self.format_handlers = {
            "pdf": get_pdf_handler,
            "docx": get_docx_handler,
            "txt": get_txt_handler
        }
    
    def save_uploaded_file(self, uploaded_file) -> str:
        """
        Save an uploaded file to a temporary location.
        
        Args:
            uploaded_file: Uploaded file object
            
        Returns:
            Path to the saved file
        """
        # Create a unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{uploaded_file.name}"
        filepath = os.path.join(self.temp_dir, filename)
        
        # Write the file
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        logger.info(f"Saved uploaded file to {filepath}")
        
        return filepath
    
    def get_format_handler(self, file_path: str):
        """
        Get the appropriate format handler for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Format handler
        """
        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip(".")
        
        # Check if we have a handler for this format
        if ext not in self.format_handlers:
            raise DocumentProcessingError(f"Unsupported file format: {ext}")
        
        # Get handler
        handler = self.format_handlers[ext]()
        
        return handler
    
    def process_document(
        self,
        file_path: str,
        include_images: bool = True,
        ocr_enabled: bool = False,
        extract_tables: bool = False
    ) -> Dict[str, Any]:
        """
        Process a document and extract content.
        
        Args:
            file_path: Path to the document
            include_images: Whether to extract images
            ocr_enabled: Whether to use OCR
            extract_tables: Whether to extract tables
            
        Returns:
            Dictionary with document content
        """
        try:
            # Get format handler
            handler = self.get_format_handler(file_path)
            
            # Extract text
            text = handler.extract_text(file_path)
            
            # Extract metadata
            from document_processing.metadata import extract_metadata
            metadata = extract_metadata(file_path)
            
            # Initialize result
            result = {
                "text": text,
                "metadata": metadata,
                "filename": os.path.basename(file_path),
                "file_path": file_path,
                "file_size": os.path.getsize(file_path),
                "format": metadata.get("format", "unknown"),
                "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Extract images if requested
            if include_images:
                images = handler.extract_images(file_path)
                result["images"] = images
            
            # Extract tables if requested
            if extract_tables and hasattr(handler, "extract_tables"):
                tables = handler.extract_tables(file_path)
                result["tables"] = tables
            
            # Perform OCR if requested
            if ocr_enabled and hasattr(handler, "perform_ocr"):
                ocr_text = handler.perform_ocr(file_path)
                result["ocr_text"] = ocr_text
            
            logger.info(f"Successfully processed document: {file_path}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise DocumentProcessingError(f"Error processing document: {str(e)}")
    
    def get_text_preview(self, file_path: str, max_length: int = 1000) -> str:
        """
        Get a preview of the document text.
        
        Args:
            file_path: Path to the document
            max_length: Maximum preview length in characters
            
        Returns:
            Text preview
        """
        try:
            # Get format handler
            handler = self.get_format_handler(file_path)
            
            # Extract text
            text = handler.extract_text(file_path)
            
            # Truncate text
            preview = text[:max_length]
            if len(text) > max_length:
                preview += "..."
            
            return preview
        
        except Exception as e:
            logger.error(f"Error getting text preview: {str(e)}")
            return f"Error: {str(e)}"
    
    def get_document_thumbnail(self, file_path: str, size: Tuple[int, int] = (200, 200)) -> bytes:
        """
        Get a thumbnail for the document.
        
        Args:
            file_path: Path to the document
            size: Thumbnail size (width, height)
            
        Returns:
            Thumbnail image bytes
        """
        try:
            # Get format handler
            handler = self.get_format_handler(file_path)
            
            # Check if handler supports thumbnails
            if hasattr(handler, "get_thumbnail"):
                return handler.get_thumbnail(file_path, size)
            else:
                # Generate generic thumbnail
                return self._generate_generic_thumbnail(file_path, size)
        
        except Exception as e:
            logger.error(f"Error getting document thumbnail: {str(e)}")
            return None
    
    def _generate_generic_thumbnail(self, file_path: str, size: Tuple[int, int]) -> bytes:
        """
        Generate a generic thumbnail for a document.
        
        Args:
            file_path: Path to the document
            size: Thumbnail size (width, height)
            
        Returns:
            Thumbnail image bytes
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            # Create a blank image
            img = Image.new("RGB", size, color=(240, 240, 240))
            draw = ImageDraw.Draw(img)
            
            # Get file extension
            _, ext = os.path.splitext(file_path)
            ext = ext.lower().lstrip(".")
            
            # Draw file extension
            font_size = min(size) // 4
            try:
                font = ImageFont.truetype("Arial", font_size)
            except IOError:
                font = ImageFont.load_default()
            
            text_width, text_height = draw.textsize(ext.upper(), font=font)
            position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
            
            draw.text(position, ext.upper(), fill=(100, 100, 100), font=font)
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            
            return buffer.getvalue()
        
        except Exception as e:
            logger.error(f"Error generating generic thumbnail: {str(e)}")
            return None