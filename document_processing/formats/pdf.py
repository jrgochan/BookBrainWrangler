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
        """
        if not os.path.exists(file_path):
            error_msg = f"PDF file not found: {file_path}"
            logger.error(error_msg)
            return {
                'text': '', 'images': [], 'page_count': 0,
                'error': error_msg, 'warnings': []
            }
        if not file_path.lower().endswith('.pdf'):
            error_msg = f"Not a PDF file: {file_path}"
            logger.error(error_msg)
            return {
                'text': '', 'images': [], 'page_count': 0,
                'error': error_msg, 'warnings': []
            }
        result = {
            'text': '', 'images': [], 'page_count': 0,
            'error': None, 'warnings': []
        }
        try:
            def send_progress(current, total, message="Processing PDF"):
                if progress_callback:
                    progress_callback(current / total, message)
            text_result = self.extract_text(file_path, progress_callback=send_progress)
            result['text'] = text_result.get('text', '')
            result['page_count'] = text_result.get('page_count', 0)
            if text_result.get('warnings'):
                result['warnings'].extend(text_result['warnings'])
            if text_result.get('error'):
                result['error'] = text_result['error']
            if extract_images:
                if PDF2IMAGE_AVAILABLE:
                    logger.info(f"Extracting images from PDF: {file_path}")
                    images_result = self.extract_images(file_path, progress_callback=send_progress)
                    result['images'] = images_result.get('images', [])
                    if images_result.get('warnings'):
                        result['warnings'].extend(images_result['warnings'])
                    if images_result.get('error'):
                        result['error'] = images_result['error']
                else:
                    warn = "Skipping image extraction: pdf2image not available"
                    logger.warning(warn)
                    result['warnings'].append(warn)
            logger.info(f"Successfully processed PDF file: {file_path}")
            return result
        except Exception as e:
            error_msg = f"Error processing PDF file {file_path}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result['error'] = error_msg
            return result
    
    def extract_text(
        self, 
        file_path: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Extract text from a PDF file with enhanced error handling and fallback mechanisms.
        Always returns a dict with text, page_count, error, and warnings.
        """
        if not PYPDF2_AVAILABLE:
            logger.error("PyPDF2 is not available. Cannot extract text from PDF.")
            return {'text': '', 'page_count': 0, 'error': 'PyPDF2 unavailable', 'warnings': []}
        warnings = []
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                logger.info(f"PDF has {page_count} pages: {file_path}")
                pages_with_errors = []
                empty_pages = []
                text = ""
                for i, page in enumerate(pdf_reader.pages):
                    if progress_callback:
                        progress_callback(i / page_count, f"Extracting text from page {i+1}/{page_count}")
                    try:
                        page_text = ""
                        try:
                            page_text = page.extract_text() or ""
                        except Exception as e1:
                            logger.warning(f"Standard extraction failed on page {i+1}: {str(e1)}")
                            warnings.append(f"Standard extraction failed on page {i+1}: {str(e1)}")
                            try:
                                page_elements = getattr(page, "_objects", None)
                                if page_elements:
                                    page_text = " ".join([str(elem) for elem in page_elements if hasattr(elem, "get_text")])
                            except Exception as e2:
                                logger.warning(f"Alternative extraction failed on page {i+1}: {str(e2)}")
                                warnings.append(f"Alternative extraction failed on page {i+1}: {str(e2)}")
                        if len(page_text) == 0:
                            logger.warning(f"No text extracted from page {i+1}")
                            warnings.append(f"No text extracted from page {i+1}")
                            empty_pages.append(i+1)
                        else:
                            logger.info(f"Extracted {len(page_text)} characters from page {i+1}")
                        page_text = " ".join(page_text.split())
                        text += page_text + "\n\n"
                    except Exception as page_error:
                        logger.error(f"Error extracting text from page {i+1}: {str(page_error)}")
                        warnings.append(f"Error extracting text from page {i+1}: {str(page_error)}")
                        pages_with_errors.append(i+1)
                text = text.strip()
                if pages_with_errors:
                    logger.warning(f"Had errors extracting text from pages: {pages_with_errors}")
                    warnings.append(f"Had errors extracting text from pages: {pages_with_errors}")
                if empty_pages:
                    logger.warning(f"Extracted no text from pages: {empty_pages}")
                    warnings.append(f"Extracted no text from pages: {empty_pages}")
                # OCR fallback
                if len(text) < 100 or (empty_pages and len(empty_pages) > page_count / 2):
                    logger.warning(f"Extracted text may be insufficient ({len(text)} chars), attempting OCR fallback")
                    warnings.append(f"Extracted text may be insufficient ({len(text)} chars), attempting OCR fallback")
                    try:
                        from document_processing.ocr import OCRProcessor
                        ocr = OCRProcessor()
                        if progress_callback:
                            progress_callback(0.7, f"Standard extraction yielded insufficient text. Trying OCR...")
                        ocr_result = ocr.process_file(file_path, progress_callback=progress_callback)
                        if ocr_result and 'text' in ocr_result and ocr_result['text']:
                            ocr_text = ocr_result['text']
                            if len(ocr_text) > len(text):
                                logger.info(f"OCR extracted more text ({len(ocr_text)} chars) than PyPDF2 ({len(text)} chars). Using OCR result.")
                                warnings.append(f"OCR extracted more text than PyPDF2 on {file_path}")
                                text = ocr_text
                            else:
                                logger.info(f"PyPDF2 extracted more text ({len(text)} chars) than OCR ({len(ocr_text)} chars). Using PyPDF2 result.")
                        else:
                            logger.warning("OCR fallback also failed to extract text")
                            warnings.append("OCR fallback also failed to extract text")
                    except Exception as ocr_error:
                        logger.error(f"Error during OCR fallback: {str(ocr_error)}")
                        warnings.append(f"Error during OCR fallback: {str(ocr_error)}")
                import re
                text = re.sub(r'\n{3,}', '\n\n', text)
                if len(text) > 0:
                    logger.info(f"Successfully extracted {len(text)} characters from {page_count} pages in {file_path}")
                else:
                    logger.error(f"Failed to extract any text from {file_path}")
                    warnings.append(f"Failed to extract any text from {file_path}")
                return {
                    'text': text,
                    'page_count': page_count,
                    'error': None,
                    'warnings': warnings
                }
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            warnings.append(f"Error extracting text from PDF {file_path}: {str(e)}")
            # Try OCR as last resort
            try:
                from document_processing.ocr import OCRProcessor
                ocr = OCRProcessor()
                logger.info(f"PyPDF2 extraction failed completely. Using OCR as last resort.")
                if progress_callback:
                    progress_callback(0.5, "PDF extraction failed. Trying OCR as last resort...")
                ocr_result = ocr.process_file(file_path, progress_callback=progress_callback)
                if ocr_result and 'text' in ocr_result:
                    return {
                        'text': ocr_result['text'],
                        'page_count': ocr_result.get('page_count', 0),
                        'error': None,
                        'warnings': warnings + ["Used OCR fallback due to PyPDF2 failure"]
                    }
            except Exception as ocr_error:
                logger.error(f"Final OCR attempt also failed: {str(ocr_error)}")
                warnings.append(f"Final OCR attempt also failed: {str(ocr_error)}")
            return {'text': '', 'page_count': 0, 'error': 'Text extraction failed', 'warnings': warnings}
    
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