"""
PDF processing utilities for document extraction.
"""

import os
import io
import base64
from typing import Dict, List, Any, Optional, Callable, Union
import PyPDF2
from pdf2image import convert_from_path
from PIL import Image

from document_processing.ocr import perform_ocr
from utils.logger import get_logger

# Get a logger for this module
logger = get_logger(__name__)

def get_page_count(pdf_path: str) -> int:
    """
    Get the number of pages in a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Number of pages as an integer
    """
    # Use PyPDF2 to get the real page count
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            return len(pdf_reader.pages)
    except Exception as e:
        logger.error(f"Error getting page count: {str(e)}")
        return 0

def extract_page_as_image(pdf_path: str, page_number: int) -> Optional[Image.Image]:
    """
    Extract a specific page from a PDF as an image.
    
    Args:
        pdf_path: Path to the PDF file
        page_number: The page number to extract (1-based index)
        
    Returns:
        PIL Image object or None if extraction failed
    """
    try:
        images = convert_from_path(pdf_path, first_page=page_number, last_page=page_number)
        if images:
            return images[0]
        else:
            logger.warning(f"No image extracted from page {page_number}")
            return None
    except Exception as e:
        logger.error(f"Error extracting page {page_number} as image: {str(e)}")
        return None

def image_to_base64(image: Image.Image, format: str = 'PNG') -> str:
    """
    Convert a PIL Image to base64 encoded string.
    
    Args:
        image: PIL Image object
        format: Image format (default: PNG)
        
    Returns:
        Base64 encoded string of the image
    """
    if image is None:
        return ""
        
    try:
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=format)
        img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        return img_base64
    except Exception as e:
        logger.error(f"Error converting image to base64: {str(e)}")
        return ""

def process_pdf(pdf_path: str, include_images: bool = True, 
               ocr_engine: str = "pytesseract", ocr_settings: Optional[Dict[str, Any]] = None,
               progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """
    Process a PDF file and extract text and optionally images.
    
    Args:
        pdf_path: Path to the PDF file
        include_images: Whether to include images in the extraction
        ocr_engine: The OCR engine to use
        ocr_settings: Dictionary of OCR settings
        progress_callback: Optional callback function for progress updates
        
    Returns:
        A dictionary with extracted content:
        {
            'text': Extracted text as a string,
            'images': List of image descriptions with embedded base64 data (if include_images=True)
        }
    """
    # Define a helper function for sending progress updates
    def send_progress(current, total, message):
        if progress_callback:
            progress_callback(current, total, message)
    
    # Get total pages
    total_pages = get_page_count(pdf_path)
    if total_pages == 0:
        return {'text': '', 'images': []}
    
    # Initialize result
    result = {
        'text': '',
        'images': []
    }
    
    send_progress(0, total_pages, "Starting document processing...")
    
    # Open the PDF file
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        
        # Process each page
        for i in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[i]
            progress_text = f"Processing page {i+1}/{total_pages}"
            send_progress(i, total_pages, {'text': progress_text, 'action': 'processing'})
            
            # Try to extract text directly from PDF
            extracted_text = page.extract_text()
            
            # If direct extraction didn't work well, use OCR
            if not extracted_text or len(extracted_text.strip()) < 50:  # Heuristic to determine if text extraction failed
                try:
                    # Convert PDF page to image
                    image = extract_page_as_image(pdf_path, i+1)
                    if image:
                        # Perform OCR on the image
                        extracted_text, confidence = perform_ocr(image, ocr_engine, ocr_settings)
                        
                        # Save image for UI feedback
                        if include_images or progress_callback:
                            # Convert image to base64 for display
                            img_base64 = image_to_base64(image)
                            
                            if include_images:
                                # Add image to result
                                result['images'].append({
                                    'page': i+1,
                                    'index': 0,  # First image on page
                                    'description': f"Image from page {i+1}",
                                    'data': img_base64
                                })
                            
                            # Send progress with image and text data
                            if progress_callback:
                                send_progress(i, total_pages, {
                                    'text': progress_text,
                                    'current_image': img_base64,
                                    'ocr_text': extracted_text,
                                    'confidence': confidence,
                                    'action': 'extracting'
                                })
                except Exception as e:
                    logger.error(f"OCR processing error on page {i+1}: {str(e)}")
                    # If OCR fails, use whatever text we could extract directly
                    if progress_callback:
                        send_progress(i, total_pages, {
                            'text': f"Error processing page {i+1}: {str(e)}",
                            'action': 'error'
                        })
            else:
                # Direct extraction worked, report good confidence
                confidence = 95.0  # High confidence for direct extraction
                
                # If we need to show progress with the page image
                if progress_callback:
                    try:
                        # Generate image from page for visualization
                        image = extract_page_as_image(pdf_path, i+1)
                        if image:
                            img_base64 = image_to_base64(image)
                            
                            send_progress(i, total_pages, {
                                'text': progress_text,
                                'current_image': img_base64,
                                'ocr_text': extracted_text,
                                'confidence': confidence,
                                'action': 'extracting'
                            })
                    except Exception as e:
                        # If image conversion fails, just report the text
                        logger.error(f"Image conversion error on page {i+1}: {str(e)}")
                        send_progress(i, total_pages, {
                            'text': progress_text,
                            'ocr_text': extracted_text,
                            'confidence': confidence,
                            'action': 'extracting'
                        })
            
            # Add extracted text to result
            result['text'] += extracted_text + "\n\n"
    
    # Finalizing
    send_progress(total_pages-1, total_pages, {'text': "Finalizing document processing...", 'action': 'completed'})
    
    return result