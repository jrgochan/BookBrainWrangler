"""
PDF processing module for document extraction.

This module provides functionality for extracting text and images from PDF files.
"""

import os
import base64
import tempfile
from io import BytesIO
from typing import Dict, List, Any, Optional, Union, Callable, Tuple

from utils.logger import get_logger
from core.exceptions import DocumentProcessingError, DocumentFormatError

# Initialize logger
logger = get_logger(__name__)

# Try to import required libraries
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    logger.warning("PyPDF2 not available. PDF text extraction will be limited.")
    PYPDF2_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    logger.warning("pdf2image not available. PDF image extraction will be limited.")
    PDF2IMAGE_AVAILABLE = False

class PDFProcessor:
    """
    PDF processor for extracting text and images from PDF files.
    """
    
    def __init__(self):
        """Initialize the PDF processor."""
        # Check dependencies
        if not PYPDF2_AVAILABLE:
            logger.warning("PyPDF2 not available. PDF text extraction will be limited.")
        
        if not PDF2IMAGE_AVAILABLE:
            logger.warning("pdf2image not available. PDF image extraction will be limited.")
            
    def is_available(self) -> bool:
        """
        Check if the PDF processor is available.
        
        Returns:
            True if the processor is fully available, False otherwise
        """
        return PYPDF2_AVAILABLE and PDF2IMAGE_AVAILABLE
    
    def process(
        self, 
        file_path: str, 
        extract_images: bool = True,
        ocr_enabled: bool = False,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Process a PDF file and extract text and optionally images.
        
        Args:
            file_path: Path to the PDF file
            extract_images: Whether to extract images
            ocr_enabled: Whether to use OCR for image-based PDFs
            progress_callback: Optional callback function for progress updates
            
        Returns:
            A dictionary with extracted content:
            {
                'text': Extracted text as a string,
                'images': List of image descriptions with embedded base64 data (if extract_images=True),
                'page_count': Number of pages in the PDF
            }
        """
        if not os.path.exists(file_path):
            error_msg = f"PDF file not found: {file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        if not file_path.lower().endswith('.pdf'):
            error_msg = f"Not a PDF file: {file_path}"
            logger.error(error_msg)
            raise DocumentFormatError(error_msg)
        
        # Initialize result dictionary
        result = {
            'text': '',
            'images': [],
            'page_count': 0
        }
        
        try:
            # Define a progress callback handler
            def send_progress(current, total, message="Processing PDF"):
                if progress_callback:
                    progress_callback(current / total, message)
                    
            # Extract text from PDF
            text_result = self.extract_text(file_path, progress_callback=send_progress)
            result['text'] = text_result.get('text', '')
            result['page_count'] = text_result.get('page_count', 0)
            
            # Extract images if requested
            if extract_images:
                # Try PDF2Image for rendering pages as images
                if PDF2IMAGE_AVAILABLE:
                    logger.info(f"Extracting images from PDF: {file_path}")
                    images_result = self.extract_images(file_path, progress_callback=send_progress)
                    result['images'] = images_result.get('images', [])
                else:
                    logger.warning("Skipping image extraction: pdf2image not available")
            
            # Log success
            logger.info(f"Successfully processed PDF file: {file_path}")
            return result
            
        except Exception as e:
            error_msg = f"Error processing PDF file {file_path}: {str(e)}"
            logger.error(error_msg)
            raise DocumentProcessingError(error_msg) from e
    
    def extract_text(
        self, 
        file_path: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Extract text from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary with extracted text and page count
        """
        if not PYPDF2_AVAILABLE:
            return {'text': '', 'page_count': 0}
        
        try:
            # Open the PDF file
            with open(file_path, 'rb') as file:
                # Create a PDF reader object
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                # Extract text from each page
                text = ""
                for i, page in enumerate(pdf_reader.pages):
                    # Update progress
                    if progress_callback:
                        progress_callback(i / page_count, f"Extracting text from page {i+1}/{page_count}")
                    
                    try:
                        # Extract text from page
                        page_text = page.extract_text() or ""
                        
                        # Log page text length for debugging
                        if len(page_text) == 0:
                            logger.warning(f"No text extracted from page {i+1}")
                        else:
                            logger.debug(f"Extracted {len(page_text)} characters from page {i+1}")
                            
                        text += page_text + "\n\n"
                    except Exception as page_error:
                        logger.error(f"Error extracting text from page {i+1}: {str(page_error)}")
                        # Continue with next page despite error
                
                # Check if we actually extracted any text
                text = text.strip()
                if len(text) == 0:
                    logger.warning(f"No text extracted from PDF using PyPDF2, attempting OCR fallback")
                    try:
                        # Import OCR module for fallback
                        from document_processing.ocr import OCRProcessor
                        
                        # Create OCR processor
                        ocr = OCRProcessor()
                        
                        # Extract text using OCR
                        ocr_result = ocr.process_file(file_path, progress_callback=progress_callback)
                        
                        if ocr_result and 'text' in ocr_result and ocr_result['text']:
                            text = ocr_result['text']
                            logger.info(f"Successfully extracted {len(text)} characters using OCR fallback")
                        else:
                            logger.warning("OCR fallback also failed to extract text")
                    except Exception as ocr_error:
                        logger.error(f"Error during OCR fallback: {str(ocr_error)}")
                
                # Log result
                if len(text) > 0:
                    logger.info(f"Successfully extracted {len(text)} characters from {page_count} pages in {file_path}")
                else:
                    logger.warning(f"Failed to extract any text from {file_path}")
                    
                return {
                    'text': text,
                    'page_count': page_count
                }
                
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            return {'text': '', 'page_count': 0}
    
    def extract_images(
        self,
        file_path: str,
        dpi: int = 200,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Extract images from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            dpi: DPI for image extraction
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary with list of images as base64 encoded strings
        """
        if not PDF2IMAGE_AVAILABLE:
            return {'images': []}
        
        try:
            # Get page count
            page_count = 0
            if PYPDF2_AVAILABLE:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    page_count = len(pdf_reader.pages)
            
            # Convert PDF pages to images
            images = []
            pages = convert_from_path(
                file_path,
                dpi=dpi,
                fmt='jpeg',
                thread_count=4
            )
            
            # If we couldn't get page count from PyPDF2, use the length of pages
            if page_count == 0:
                page_count = len(pages)
            
            # Process each page
            for i, page_image in enumerate(pages):
                # Update progress
                if progress_callback:
                    progress_callback(i / page_count, f"Extracting image from page {i+1}/{page_count}")
                
                # Save image to a byte buffer
                buffered = BytesIO()
                page_image.save(buffered, format="JPEG")
                
                # Get base64 encoded string
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                # Add to result
                images.append({
                    'page': i + 1,
                    'type': 'page',
                    'format': 'jpeg',
                    'width': page_image.width,
                    'height': page_image.height,
                    'data': img_base64
                })
            
            # Log success
            logger.info(f"Extracted {len(images)} page images from {file_path}")
            return {'images': images}
            
        except Exception as e:
            logger.error(f"Error extracting images from PDF {file_path}: {str(e)}")
            return {'images': []}
    
    def extract_page_as_image(
        self,
        file_path: str,
        page_number: int = 0,
        dpi: int = 200
    ) -> Dict[str, Any]:
        """
        Extract a specific page as an image.
        
        Args:
            file_path: Path to the PDF file
            page_number: Page number to extract (0-indexed)
            dpi: DPI for image extraction
            
        Returns:
            Dictionary with image data
        """
        if not PDF2IMAGE_AVAILABLE:
            return {'image': None}
        
        try:
            # Convert specific page to image
            pages = convert_from_path(
                file_path,
                dpi=dpi,
                fmt='jpeg',
                first_page=page_number + 1,
                last_page=page_number + 1
            )
            
            if not pages:
                logger.warning(f"No page found at position {page_number} in {file_path}")
                return {'image': None}
            
            # Get the extracted page
            page_image = pages[0]
            
            # Save image to a byte buffer
            buffered = BytesIO()
            page_image.save(buffered, format="JPEG")
            
            # Get base64 encoded string
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # Log success
            logger.info(f"Extracted page {page_number} as image from {file_path}")
            return {
                'image': {
                    'page': page_number + 1,
                    'type': 'page',
                    'format': 'jpeg',
                    'width': page_image.width,
                    'height': page_image.height,
                    'data': img_base64
                }
            }
            
        except Exception as e:
            logger.error(f"Error extracting page {page_number} as image from {file_path}: {str(e)}")
            return {'image': None}
    
    def get_thumbnail(
        self,
        file_path: str,
        page_number: int = 0,
        width: int = 200,
        height: int = 300
    ) -> Optional[str]:
        """
        Get a thumbnail image for a PDF file.
        
        Args:
            file_path: Path to the PDF file
            page_number: Page number to use for thumbnail (0-indexed)
            width: Desired width of the thumbnail
            height: Desired height of the thumbnail
            
        Returns:
            Base64 encoded thumbnail image or None if failed
        """
        try:
            # Extract the page as an image
            page_result = self.extract_page_as_image(file_path, page_number, dpi=100)
            
            if not page_result.get('image'):
                return None
                
            # Import PIL for image processing
            try:
                from PIL import Image
                from io import BytesIO
                import base64
                
                # Decode the base64 image
                image_data = page_result['image']['data']
                image_bytes = base64.b64decode(image_data)
                
                # Open the image
                image = Image.open(BytesIO(image_bytes))
                
                # Resize the image while maintaining aspect ratio
                original_width, original_height = image.size
                aspect_ratio = original_width / original_height
                
                if width / height > aspect_ratio:
                    # Height is the limiting factor
                    new_height = height
                    new_width = int(aspect_ratio * new_height)
                else:
                    # Width is the limiting factor
                    new_width = width
                    new_height = int(new_width / aspect_ratio)
                
                # Resize the image
                resized_image = image.resize((new_width, new_height), Image.LANCZOS)
                
                # Create a new image with the desired dimensions and paste the resized image
                thumbnail = Image.new('RGB', (width, height), (255, 255, 255))
                paste_x = (width - new_width) // 2
                paste_y = (height - new_height) // 2
                thumbnail.paste(resized_image, (paste_x, paste_y))
                
                # Save the thumbnail to a byte buffer
                buffered = BytesIO()
                thumbnail.save(buffered, format="JPEG", quality=85)
                
                # Get base64 encoded string
                thumbnail_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                return thumbnail_base64
                
            except ImportError:
                logger.warning("PIL not available for thumbnail generation")
                return None
                
        except Exception as e:
            logger.error(f"Error creating thumbnail for {file_path}: {str(e)}")
            return None