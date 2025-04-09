"""
OCR (Optical Character Recognition) functionality for Book Knowledge AI.
Handles text extraction from images.
"""

import os
import tempfile
from typing import Dict, List, Union, Any, Optional, Callable
from pathlib import Path

try:
    import pytesseract
    from PIL import Image, ImageEnhance
except ImportError:
    # Log the import error, but allow the module to be imported
    import logging
    logging.getLogger(__name__).error("pytesseract or PIL not installed. OCR functionality will not be available.")

from utils.logger import get_logger
from core.exceptions import OCRError

# Get a logger for this module
logger = get_logger(__name__)

def extract_text_from_image(image: Union[str, bytes, Image.Image], 
                          lang: str = 'eng',
                          preprocess: bool = True,
                          confidence_threshold: float = 70.0) -> Dict[str, Any]:
    """
    Extract text from an image using OCR.
    
    Args:
        image: Path to image file, image data in bytes, or PIL Image
        lang: Language code for OCR (default: 'eng')
        preprocess: Whether to preprocess the image for better OCR results
        confidence_threshold: Minimum confidence level (percentage) for including text
        
    Returns:
        Dictionary with extracted content:
        {
            'text': str,  # Full extracted text
            'words': List[Dict],  # Words with positions and confidence scores
            'confidence': float  # Overall confidence score
        }
        
    Raises:
        OCRError: If OCR processing fails
    """
    logger.info(f"Extracting text from image (lang: {lang}, preprocess: {preprocess})")
    
    try:
        # Convert input to PIL Image
        img = _get_image(image)
        
        # Preprocess image if requested
        if preprocess:
            img = _preprocess_image(img)
        
        # Configure pytesseract to get detailed output
        custom_config = f'--oem 3 --psm 6 -l {lang}'
        
        # Extract text with detailed data
        data = pytesseract.image_to_data(img, config=custom_config, output_type=pytesseract.Output.DICT)
        
        # Filter words by confidence
        filtered_text = []
        words = []
        total_confidence = 0
        word_count = 0
        
        for i in range(len(data['text'])):
            # Skip empty text
            if not data['text'][i].strip():
                continue
            
            # Get word data
            word = data['text'][i]
            conf = float(data['conf'][i])
            
            # Only include words above confidence threshold
            if conf >= confidence_threshold:
                filtered_text.append(word)
                words.append({
                    'text': word,
                    'confidence': conf,
                    'left': data['left'][i],
                    'top': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i],
                    'line_num': data['line_num'][i],
                    'block_num': data['block_num'][i],
                    'page_num': data['page_num'][i]
                })
                
                total_confidence += conf
                word_count += 1
        
        # Calculate overall confidence
        overall_confidence = total_confidence / max(1, word_count)
        
        # Format the text with spaces and line breaks
        formatted_text = ''
        current_line = -1
        current_block = -1
        
        for i, word_data in enumerate(words):
            # Check if we're starting a new block
            if word_data['block_num'] != current_block:
                if i > 0:  # Add blank line between blocks (except before first block)
                    formatted_text += '\n\n'
                current_block = word_data['block_num']
                current_line = word_data['line_num']
            # Check if we're starting a new line in the same block
            elif word_data['line_num'] != current_line:
                formatted_text += '\n'
                current_line = word_data['line_num']
            # Same line, add space before word (except at start of line)
            elif i > 0 and words[i-1]['line_num'] == current_line:
                formatted_text += ' '
            
            # Add the word
            formatted_text += word_data['text']
        
        return {
            'text': formatted_text.strip(),
            'words': words,
            'confidence': overall_confidence
        }
    
    except Exception as e:
        logger.error(f"OCR processing failed: {str(e)}")
        raise OCRError(f"Failed to extract text from image: {str(e)}")

def extract_text_from_images(images: List[Union[str, bytes, Image.Image]], 
                           lang: str = 'eng',
                           preprocess: bool = True,
                           confidence_threshold: float = 70.0,
                           progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """
    Extract text from multiple images using OCR.
    
    Args:
        images: List of image paths, image data in bytes, or PIL Images
        lang: Language code for OCR (default: 'eng')
        preprocess: Whether to preprocess images for better OCR results
        confidence_threshold: Minimum confidence level (percentage) for including text
        progress_callback: Optional callback for progress updates
        
    Returns:
        Dictionary with extracted content:
        {
            'text': str,  # Combined extracted text from all images
            'pages': List[Dict],  # Text and confidence by page
            'confidence': float  # Overall confidence score
        }
    """
    logger.info(f"Extracting text from {len(images)} images")
    
    try:
        # Process each image
        results = []
        all_text = []
        total_confidence = 0
        
        for i, image in enumerate(images):
            # Update progress
            if progress_callback:
                progress_callback(i, len(images), {
                    "text": f"OCR processing image {i+1}/{len(images)}",
                    "type": "ocr_processing"
                })
            
            # Process image
            result = extract_text_from_image(image, lang, preprocess, confidence_threshold)
            results.append(result)
            
            # Add text and update confidence
            all_text.append(result['text'])
            total_confidence += result['confidence']
        
        # Calculate overall confidence
        overall_confidence = total_confidence / max(1, len(images))
        
        # Format combined text with page breaks
        combined_text = '\n\n------ Page Break ------\n\n'.join(all_text)
        
        return {
            'text': combined_text,
            'pages': [{'text': r['text'], 'confidence': r['confidence']} for r in results],
            'confidence': overall_confidence
        }
    
    except Exception as e:
        logger.error(f"OCR processing failed for multiple images: {str(e)}")
        raise OCRError(f"Failed to extract text from images: {str(e)}")

def extract_text_from_pdf(pdf_path: str,
                        lang: str = 'eng',
                        preprocess: bool = True,
                        confidence_threshold: float = 70.0,
                        max_pages: Optional[int] = None,
                        page_range: Optional[tuple] = None,
                        progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """
    Extract text from a PDF using OCR.
    
    Args:
        pdf_path: Path to PDF file
        lang: Language code for OCR (default: 'eng')
        preprocess: Whether to preprocess images for better OCR results
        confidence_threshold: Minimum confidence level (percentage) for including text
        max_pages: Maximum number of pages to process (None for all)
        page_range: Optional tuple (start, end) for page range to process (0-based)
        progress_callback: Optional callback for progress updates
        
    Returns:
        Dictionary with extracted content:
        {
            'text': str,  # Combined extracted text from all pages
            'pages': List[Dict],  # Text and confidence by page
            'confidence': float  # Overall confidence score
        }
    """
    logger.info(f"Extracting text from PDF: {pdf_path}")
    
    try:
        # Convert PDF pages to images
        from pdf2image import convert_from_path
        
        # Determine page range
        first_page = None
        last_page = None
        
        if page_range:
            first_page = page_range[0] + 1  # pdf2image uses 1-based indexing
            last_page = page_range[1] + 1
        
        # Convert PDF to images
        images = convert_from_path(
            pdf_path,
            dpi=300,  # Higher DPI for better OCR
            first_page=first_page,
            last_page=last_page
        )
        
        # Limit number of pages if specified
        if max_pages is not None and max_pages > 0:
            images = images[:max_pages]
        
        # Process images
        return extract_text_from_images(images, lang, preprocess, 
                                      confidence_threshold, progress_callback)
    
    except ImportError:
        logger.error("pdf2image is not installed. Cannot extract text from PDF.")
        raise OCRError("Missing dependency: pdf2image is required for PDF OCR")
    
    except Exception as e:
        logger.error(f"OCR processing failed for PDF: {str(e)}")
        raise OCRError(f"Failed to extract text from PDF: {str(e)}")

def _get_image(image: Union[str, bytes, Image.Image]) -> Image.Image:
    """
    Convert various image inputs to PIL Image.
    
    Args:
        image: Path to image file, image data in bytes, or PIL Image
        
    Returns:
        PIL Image object
    """
    if isinstance(image, str):
        # Path to image file
        return Image.open(image)
    
    elif isinstance(image, bytes):
        # Image data in bytes
        import io
        return Image.open(io.BytesIO(image))
    
    elif isinstance(image, Image.Image):
        # Already a PIL Image
        return image
    
    else:
        raise ValueError("Unsupported image type. Expected file path, bytes, or PIL Image.")

def _preprocess_image(image: Image.Image) -> Image.Image:
    """
    Preprocess image for better OCR results.
    
    Args:
        image: PIL Image object
        
    Returns:
        Preprocessed PIL Image
    """
    # Convert to grayscale
    img = image.convert('L')
    
    # Increase contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    
    # Increase sharpness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(2.0)
    
    # Resize if too small (below 1000px width)
    width, height = img.size
    if width < 1000:
        ratio = 1000 / width
        new_width = 1000
        new_height = int(height * ratio)
        img = img.resize((new_width, new_height), Image.LANCZOS)
    
    return img