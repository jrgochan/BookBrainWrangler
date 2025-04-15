"""
OCR module for Book Knowledge AI.

This module provides OCR (Optical Character Recognition) functionality
for extracting text from images and scanned documents.
"""

import os
import io
import tempfile
from typing import Dict, List, Any, Optional, Union, Callable, Tuple, BinaryIO

from utils.logger import get_logger
from core.exceptions import OcrError

# Initialize logger
logger = get_logger(__name__)

# Try to import required libraries
try:
    import pytesseract
    from PIL import Image, ImageEnhance
    OCR_AVAILABLE = True
except ImportError:
    logger.warning("pytesseract or PIL not available. OCR functionality will be limited.")
    OCR_AVAILABLE = False

class OCRProcessor:
    """
    OCR processor for extracting text from images.
    """
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize the OCR processor.
        
        Args:
            tesseract_cmd: Optional path to tesseract executable
        """
        if not OCR_AVAILABLE:
            logger.warning("OCR dependencies not available. OCR functionality will be limited.")
            return
            
        # Set tesseract command if provided
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            
        # Log OCR initialization
        try:
            # Try to get tesseract version
            version = pytesseract.get_tesseract_version()
            logger.info(f"Initialized OCR processor (Tesseract version: {version})")
        except Exception as e:
            logger.warning(f"Initialized OCR processor, but could not get Tesseract version: {str(e)}")
    
    def process_image(
        self,
        image_path: str,
        lang: str = 'eng',
        preprocessing: bool = True,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Process an image file with OCR.
        
        Args:
            image_path: Path to the image file
            lang: Language for OCR (ISO 639-2 code)
            preprocessing: Whether to preprocess the image
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary with extracted text
        """
        if not OCR_AVAILABLE:
            return {'text': ''}
            
        if not os.path.exists(image_path):
            error_msg = f"Image file not found: {image_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            # Update progress
            if progress_callback:
                progress_callback(0.1, "Loading image...")
                
            # Open the image
            image = Image.open(image_path)
            
            # Preprocess image if requested
            if preprocessing:
                if progress_callback:
                    progress_callback(0.3, "Preprocessing image...")
                image = self._preprocess_image(image)
            
            # Perform OCR
            if progress_callback:
                progress_callback(0.5, "Performing OCR...")
                
            text = pytesseract.image_to_string(image, lang=lang)
            
            # Log success
            logger.info(f"OCR completed on {image_path}")
            
            if progress_callback:
                progress_callback(1.0, "OCR completed")
                
            return {'text': text.strip()}
            
        except Exception as e:
            error_msg = f"Error processing image with OCR: {str(e)}"
            logger.error(error_msg)
            raise OcrError(error_msg) from e
    
    def process_image_object(
        self,
        image: Union[Image.Image, bytes, BinaryIO],
        lang: str = 'eng',
        preprocessing: bool = True,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Process an image object with OCR.
        
        Args:
            image: PIL Image object, bytes, or file-like object
            lang: Language for OCR (ISO 639-2 code)
            preprocessing: Whether to preprocess the image
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary with extracted text
        """
        if not OCR_AVAILABLE:
            return {'text': ''}
        
        try:
            # Update progress
            if progress_callback:
                progress_callback(0.1, "Loading image...")
                
            # Convert to PIL Image if needed
            if isinstance(image, bytes) or hasattr(image, 'read'):
                if hasattr(image, 'read'):
                    # File-like object
                    image_data = image.read()
                else:
                    # Bytes
                    image_data = image
                    
                # Create PIL Image
                image = Image.open(io.BytesIO(image_data))
            
            # Preprocess image if requested
            if preprocessing:
                if progress_callback:
                    progress_callback(0.3, "Preprocessing image...")
                image = self._preprocess_image(image)
            
            # Perform OCR
            if progress_callback:
                progress_callback(0.5, "Performing OCR...")
                
            text = pytesseract.image_to_string(image, lang=lang)
            
            # Log success
            logger.info("OCR completed on image object")
            
            if progress_callback:
                progress_callback(1.0, "OCR completed")
                
            return {'text': text.strip()}
            
        except Exception as e:
            error_msg = f"Error processing image object with OCR: {str(e)}"
            logger.error(error_msg)
            raise OcrError(error_msg) from e
    
    def process_pdf(
        self,
        pdf_path: str,
        lang: str = 'eng',
        preprocessing: bool = True,
        dpi: int = 300,
        pages: Optional[List[int]] = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Process a PDF file with OCR.
        
        Args:
            pdf_path: Path to the PDF file
            lang: Language for OCR (ISO 639-2 code)
            preprocessing: Whether to preprocess the images
            dpi: DPI for PDF to image conversion
            pages: Optional list of pages to process (0-indexed)
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary with extracted text
        """
        if not OCR_AVAILABLE:
            return {'text': ''}
            
        if not os.path.exists(pdf_path):
            error_msg = f"PDF file not found: {pdf_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            # Try to import pdf2image
            try:
                from pdf2image import convert_from_path
            except ImportError:
                error_msg = "pdf2image not available. Cannot process PDF with OCR."
                logger.error(error_msg)
                return {'text': ''}
            
            # Update progress
            if progress_callback:
                progress_callback(0.1, "Converting PDF to images...")
                
            # Convert PDF to images
            if pages is not None:
                # Convert only specified pages
                pdf_images = convert_from_path(
                    pdf_path,
                    dpi=dpi,
                    first_page=min(pages) + 1,  # pdf2image uses 1-indexed pages
                    last_page=max(pages) + 1
                )
                # Filter out pages not in the list
                if len(pdf_images) > len(pages):
                    pdf_images = [pdf_images[i] for i in range(len(pdf_images)) if i in pages]
            else:
                # Convert all pages
                pdf_images = convert_from_path(pdf_path, dpi=dpi)
            
            # Initialize result
            all_text = []
            total_pages = len(pdf_images)
            
            # Process each page
            for i, image in enumerate(pdf_images):
                # Update progress
                if progress_callback:
                    page_progress = 0.1 + (0.9 * (i / total_pages))
                    progress_callback(page_progress, f"Processing page {i+1}/{total_pages}...")
                
                # Preprocess image if requested
                if preprocessing:
                    image = self._preprocess_image(image)
                
                # Perform OCR
                text = pytesseract.image_to_string(image, lang=lang)
                all_text.append(text.strip())
            
            # Combine text from all pages
            combined_text = "\n\n".join(all_text)
            
            # Log success
            logger.info(f"OCR completed on {pdf_path} ({total_pages} pages)")
            
            if progress_callback:
                progress_callback(1.0, "OCR completed")
                
            return {'text': combined_text}
            
        except Exception as e:
            error_msg = f"Error processing PDF with OCR: {str(e)}"
            logger.error(error_msg)
            raise OcrError(error_msg) from e
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess an image for better OCR results.
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image object
        """
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too small
            min_width = 1000
            if image.width < min_width:
                ratio = min_width / image.width
                new_size = (min_width, int(image.height * ratio))
                image = image.resize(new_size, Image.LANCZOS)
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.5)
            
            # Convert to grayscale
            image = image.convert('L')
            
            return image
            
        except Exception as e:
            logger.warning(f"Error preprocessing image: {str(e)}")
            return image
    
    def is_available(self) -> bool:
        """
        Check if OCR functionality is available.
        
        Returns:
            True if OCR is available, False otherwise
        """
        if not OCR_AVAILABLE:
            return False
            
        try:
            # Try to get tesseract version
            version = pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
    
    def get_available_languages(self) -> List[str]:
        """
        Get list of available OCR languages.
        
        Returns:
            List of available language codes
        """
        if not OCR_AVAILABLE:
            return []
            
        try:
            # Try to get available languages
            langs = pytesseract.get_languages()
            return langs
        except Exception as e:
            logger.warning(f"Could not get available languages: {str(e)}")
            return ['eng']  # Default to English