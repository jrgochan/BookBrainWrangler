"""
OCR processing utilities for document extraction.
"""

import io
import os
from typing import Optional, Union, Dict, Any
from PIL import Image
import pytesseract

from utils.logger import get_logger
from core.exceptions import OCRError

# Get a logger for this module
logger = get_logger(__name__)

def perform_ocr(image: Union[str, Image.Image], ocr_engine: str = 'tesseract') -> str:
    """
    Perform OCR on an image to extract text.
    
    Args:
        image: Path to an image file or a PIL Image object
        ocr_engine: OCR engine to use ('tesseract' is currently the only supported option)
        
    Returns:
        Extracted text as a string
    """
    try:
        # Load the image if a path was provided
        if isinstance(image, str):
            img = Image.open(image)
        else:
            img = image
        
        if ocr_engine == 'tesseract':
            # Use pytesseract to extract text
            text = pytesseract.image_to_string(img)
            return text.strip()
        else:
            raise OCRError(f"Unsupported OCR engine: {ocr_engine}")
    
    except Exception as e:
        logger.error(f"OCR error: {str(e)}")
        raise OCRError(f"OCR processing failed: {str(e)}")

def ocr_image_to_text(image_path: str, lang: str = 'eng') -> str:
    """
    Extract text from an image file using OCR.
    
    Args:
        image_path: Path to the image file
        lang: Language code for OCR (default: 'eng' for English)
        
    Returns:
        Extracted text as a string
    """
    try:
        return pytesseract.image_to_string(Image.open(image_path), lang=lang)
    except Exception as e:
        logger.error(f"OCR error for {image_path}: {str(e)}")
        return ""

def process_image_with_ocr(
    image: Union[str, Image.Image], 
    lang: str = 'eng', 
    preprocessing: bool = False
) -> Dict[str, Any]:
    """
    Process an image with OCR and return the extracted text and metadata.
    
    Args:
        image: Path to an image file or a PIL Image object
        lang: Language code for OCR (default: 'eng' for English)
        preprocessing: Whether to apply preprocessing to enhance OCR results
        
    Returns:
        Dictionary with extracted text and metadata
    """
    try:
        # Load the image if a path was provided
        if isinstance(image, str):
            img = Image.open(image)
        else:
            img = image
        
        # Apply preprocessing if requested
        if preprocessing:
            # Convert to grayscale
            img = img.convert('L')
            # TODO: Add more preprocessing steps if needed
        
        # Perform OCR
        text = pytesseract.image_to_string(img, lang=lang)
        
        # Get additional OCR data
        ocr_data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)
        
        return {
            'text': text.strip(),
            'confidence': sum(ocr_data['conf']) / len(ocr_data['conf']) if ocr_data['conf'] else 0,
            'word_count': len([word for word in ocr_data['text'] if word.strip()]),
            'lang': lang
        }
    
    except Exception as e:
        logger.error(f"OCR processing error: {str(e)}")
        return {
            'text': '',
            'confidence': 0,
            'word_count': 0,
            'lang': lang,
            'error': str(e)
        }