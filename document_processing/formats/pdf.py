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
from core.exceptions import DocumentProcessingError
from utils.logger import get_logger

# Get a logger for this module
logger = get_logger(__name__)

def process_pdf(pdf_path: str, use_ocr: bool = False, include_images: bool = True, 
               progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """
    Process a PDF file and extract text and optionally images.
    
    Args:
        pdf_path: Path to the PDF file
        use_ocr: Whether to use OCR for text extraction
        include_images: Whether to include images in the extraction
        progress_callback: Optional callback function for progress updates
        
    Returns:
        A dictionary with extracted content:
        {
            'text': Extracted text as a string,
            'images': List of image descriptions with embedded base64 data (if include_images=True),
            'page_count': Number of pages in the PDF
        }
    """
    # Define a function to send progress updates
    def send_progress(current, total, message):
        if progress_callback:
            progress_callback(current, total, message)
    
    # Initialize result dictionary
    result = {
        'text': '',
        'images': [],
        'page_count': 0
    }
    
    try:
        # Get page count
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            page_count = len(pdf_reader.pages)
            result['page_count'] = page_count
        
        send_progress(0, page_count, f"Starting PDF processing ({page_count} pages)")
        
        if use_ocr:
            # OCR-based extraction
            text_parts = []
            image_pages = []
            
            # Convert PDF to images for OCR processing
            try:
                # Convert first 3 pages for preview/thumbnail
                preview_count = min(3, page_count)
                send_progress(0, page_count, f"Converting first {preview_count} pages to images")
                preview_images = convert_from_path(
                    pdf_path, 
                    first_page=1, 
                    last_page=preview_count,
                    dpi=200
                )
                
                # Process all pages with progress updates
                for page_num in range(1, page_count + 1):
                    send_progress(page_num - 1, page_count, f"Processing page {page_num} with OCR")
                    
                    # Convert page to image
                    images = convert_from_path(
                        pdf_path, 
                        first_page=page_num, 
                        last_page=page_num,
                        dpi=300
                    )
                    
                    if not images:
                        logger.warning(f"Failed to convert page {page_num} to image")
                        continue
                    
                    # Extract text with OCR
                    page_image = images[0]
                    image_pages.append(page_image)
                    
                    page_text = perform_ocr(page_image)
                    if page_text:
                        text_parts.append(page_text)
                
                # Combine all extracted text
                result['text'] = "\n\n".join(text_parts)
                
                # Include images if requested
                if include_images:
                    for i, img in enumerate(preview_images):
                        # Convert images to base64 for embedding
                        buffered = io.BytesIO()
                        img.save(buffered, format="PNG")
                        img_str = base64.b64encode(buffered.getvalue()).decode()
                        
                        result['images'].append({
                            'page': i + 1,
                            'data': f"data:image/png;base64,{img_str}",
                            'width': img.width,
                            'height': img.height
                        })
            
            except Exception as e:
                logger.error(f"Error during OCR processing: {str(e)}")
                raise DocumentProcessingError(f"OCR processing failed: {str(e)}")
        
        else:
            # Default extraction using PyPDF2
            text_parts = []
            for i in range(page_count):
                send_progress(i, page_count, f"Extracting text from page {i+1}")
                
                page = pdf_reader.pages[i]
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"Error extracting text from page {i+1}: {str(e)}")
            
            # Combine all extracted text
            result['text'] = "\n\n".join(text_parts)
            
            # Include images if requested
            if include_images:
                send_progress(page_count, page_count + 1, "Extracting images")
                # Get a few pages as images for thumbnails
                try:
                    preview_count = min(3, page_count)
                    preview_images = convert_from_path(
                        pdf_path, 
                        first_page=1, 
                        last_page=preview_count,
                        dpi=200
                    )
                    
                    for i, img in enumerate(preview_images):
                        # Convert images to base64 for embedding
                        buffered = io.BytesIO()
                        img.save(buffered, format="PNG")
                        img_str = base64.b64encode(buffered.getvalue()).decode()
                        
                        result['images'].append({
                            'page': i + 1,
                            'data': f"data:image/png;base64,{img_str}",
                            'width': img.width,
                            'height': img.height
                        })
                except Exception as e:
                    logger.warning(f"Error generating preview images: {str(e)}")
        
        send_progress(page_count + 1, page_count + 1, "PDF processing complete")
        logger.info(f"PDF processing complete. Extracted {len(result['text'])} characters from {page_count} pages")
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing PDF file: {str(e)}")
        raise DocumentProcessingError(f"Failed to process PDF file: {str(e)}")

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
        page_number: Page number to extract (1-based indexing)
        
    Returns:
        PIL Image object or None if extraction fails
    """
    try:
        images = convert_from_path(
            pdf_path, 
            first_page=page_number, 
            last_page=page_number,
            dpi=300
        )
        
        if images:
            return images[0]
        return None
    except Exception as e:
        logger.error(f"Error extracting page {page_number} as image: {str(e)}")
        return None

def get_pdf_thumbnail(pdf_path: str, page_number: int = 1, 
                     width: int = 200, format: str = 'PNG') -> Optional[str]:
    """
    Generate a thumbnail image for a PDF page.
    
    Args:
        pdf_path: Path to the PDF file
        page_number: Page number for the thumbnail (1-based indexing)
        width: Width of the thumbnail in pixels
        format: Image format (PNG, JPEG, etc.)
        
    Returns:
        Base64-encoded image data string or None if generation fails
    """
    try:
        # Extract the page as an image
        page_image = extract_page_as_image(pdf_path, page_number)
        
        if page_image:
            # Calculate height to maintain aspect ratio
            aspect_ratio = page_image.height / page_image.width
            height = int(width * aspect_ratio)
            
            # Resize the image
            thumbnail = page_image.resize((width, height), Image.LANCZOS)
            
            # Convert to base64
            buffered = io.BytesIO()
            thumbnail.save(buffered, format=format)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return f"data:image/{format.lower()};base64,{img_str}"
        
        return None
    except Exception as e:
        logger.error(f"Error generating PDF thumbnail: {str(e)}")
        return None