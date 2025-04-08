"""
Document processor module for handling document content extraction.
"""

import os
import io
import re
import base64
import json
import time
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import PyPDF2
import pytesseract
from pdf2image import convert_from_path
import docx
from PIL import Image

from utils.logger import get_logger

# Get a logger for this module
logger = get_logger(__name__)

class DocumentProcessor:
    def __init__(self):
        """Initialize the document processor with default settings."""
        # Set the path to the Tesseract executable
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        self.metadata_patterns = {
            'title': [
                r'title:\s*([^\n]+)',
                r'^(?:book\s+)?title[:\s]+([^\n]+)',
                r'(?:^|\n)([A-Z][^\n]{5,50})(?:\n|$)',  # Capitalized line that could be a title
            ],
            'author': [
                r'(?:author|by)(?:s)?:\s*([^\n]+)',
                r'(?:written|published)\s+by\s+([^\n]+)',
                r'©\s*([^\n]+)',  # Copyright symbol followed by name
            ],
            'categories': [
                r'(?:category|categories|genre|genres|subject|subjects):\s*([^\n]+)',
                r'(?:keywords|tags):\s*([^\n]+)'
            ]
        }
    
    def extract_content(self, file_path, include_images=True, progress_callback=None):
        """
        Extract text and optionally images from a document file (PDF or DOCX).
        
        Args:
            file_path: Path to the document file
            include_images: Whether to include images in the extraction
            progress_callback: Optional callback function for progress updates
            
        Returns:
            A dictionary with extracted content:
            {
                'text': Extracted text as a string,
                'images': List of image descriptions with embedded base64 data (if include_images=True)
            }
        """
        # Determine file type from extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Extract content based on file type
        if file_ext == '.pdf':
            return self._process_pdf(file_path, include_images, progress_callback)
        elif file_ext == '.docx':
            return self._process_docx(file_path, include_images, progress_callback)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def extract_text(self, file_path, progress_callback=None):
        """
        Legacy method to extract only text from a document file.
        Maintained for backward compatibility.
        
        Args:
            file_path: Path to the document file
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Extracted text as a string
        """
        result = self.extract_content(file_path, include_images=False, progress_callback=progress_callback)
        if isinstance(result, dict):
            return result.get('text', '')
        return result
    
    def _process_pdf(self, pdf_path, include_images=True, progress_callback=None):
        """
        Process a PDF file and extract text and optionally images.
        
        Args:
            pdf_path: Path to the PDF file
            include_images: Whether to include images in the extraction
            progress_callback: Optional callback function for progress updates
            
        Returns:
            A dictionary with extracted content:
            {
                'text': Extracted text as a string,
                'images': List of image descriptions with embedded base64 data (if include_images=True)
            }
        """
        # We're using global imports now
        
        # Define a helper function for sending progress updates
        def send_progress(current, total, message):
            if progress_callback:
                progress_callback(current, total, message)
        
        # Get total pages
        total_pages = self.get_page_count(pdf_path)
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
                        images = convert_from_path(pdf_path, first_page=i+1, last_page=i+1)
                        if images:
                            # Use OCR to extract text from the image
                            img = images[0]
                            extracted_text = pytesseract.image_to_string(img)
                            confidence = float(pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)['conf'][0])
                            
                            # Save image for UI feedback
                            if include_images or progress_callback:
                                # Convert image to base64 for display
                                img_byte_arr = io.BytesIO()
                                img.save(img_byte_arr, format='PNG')
                                img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                                
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
                            images = convert_from_path(pdf_path, first_page=i+1, last_page=i+1)
                            if images:
                                img = images[0]
                                img_byte_arr = io.BytesIO()
                                img.save(img_byte_arr, format='PNG')
                                img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                                
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
    
    def _process_docx(self, docx_path, include_images=True, progress_callback=None):
        """
        Process a DOCX file and extract text and optionally images.
        
        Args:
            docx_path: Path to the DOCX file
            include_images: Whether to include images in the extraction
            progress_callback: Optional callback function for progress updates
            
        Returns:
            A dictionary with extracted content:
            {
                'text': Extracted text as a string,
                'images': List of image descriptions with embedded base64 data (if include_images=True)
            }
        """
        # We're using global imports now
        
        # Initialize result
        result = {
            'text': '',
            'images': []
        }
        
        # Define a helper function for sending progress updates
        def send_progress(current, total, message):
            if progress_callback:
                progress_callback(current, total, message)
        
        try:
            # Load the document
            document = docx.Document(docx_path)
            
            # Count total paragraphs and tables for progress reporting
            total_elements = len(document.paragraphs) + len(document.tables)
            send_progress(0, total_elements, "Starting DOCX processing...")
            
            # Extract text from paragraphs
            for i, paragraph in enumerate(document.paragraphs):
                para_text = paragraph.text
                result['text'] += para_text + "\n"
                
                # Report progress
                progress_text = f"Processing paragraph {i+1}/{len(document.paragraphs)}"
                send_progress(i, total_elements, {'text': progress_text, 'action': 'processing'})
            
            # Extract text from tables
            for i, table in enumerate(document.tables):
                table_text = ""
                for row in table.rows:
                    row_text = [cell.text for cell in row.cells]
                    table_text += " | ".join(row_text) + "\n"
                
                result['text'] += table_text + "\n\n"
                
                # Report progress
                progress_text = f"Processing table {i+1}/{len(document.tables)}"
                send_progress(len(document.paragraphs) + i, total_elements, 
                             {'text': progress_text, 'action': 'processing'})
            
            # Extract images if requested
            if include_images:
                # Get the relationship IDs for images
                image_rels = []
                for rel in document.part.rels.values():
                    if "image" in rel.target_ref:
                        image_rels.append(rel)
                
                # Process each image
                for i, rel in enumerate(image_rels):
                    try:
                        # Get image data
                        image_data = rel.target_part.blob
                        
                        # Convert to base64 for storage/display
                        img_base64 = base64.b64encode(image_data).decode('utf-8')
                        
                        # Add to result
                        result['images'].append({
                            'page': 1,  # DOCX doesn't have pages like PDF
                            'index': i,
                            'description': f"Image {i+1} from document",
                            'data': img_base64
                        })
                        
                        # For UI display, create an image
                        if progress_callback:
                            # Load image for UI display
                            img = Image.open(io.BytesIO(image_data))
                            
                            # Report progress with image
                            progress_text = f"Processing image {i+1}/{len(image_rels)}"
                            send_progress(total_elements - len(image_rels) + i, total_elements, {
                                'text': progress_text,
                                'current_image': img_base64,
                                'ocr_text': f"Image {i+1} from document",
                                'confidence': 100.0,  # Full confidence for embedded images
                                'action': 'extracting'
                            })
                    except Exception as e:
                        logger.error(f"Error processing image {i+1}: {str(e)}")
            
            # Final progress update
            send_progress(total_elements, total_elements, {'text': "DOCX processing complete", 'action': 'completed'})
            
        except Exception as e:
            error_msg = f"Error processing DOCX file: {str(e)}"
            logger.error(error_msg)
            if progress_callback:
                send_progress(0, 1, {'text': error_msg, 'action': 'error'})
        
        return result
    
    def extract_metadata(self, file_path, content=None):
        """
        Extract book metadata (title, author, categories) from a document.
        
        Args:
            file_path: Path to the document file
            content: Optional pre-extracted content to use instead of re-extracting
            
        Returns:
            A dictionary with metadata fields:
            {
                'title': Extracted title or None if not found,
                'author': Extracted author or None if not found,
                'categories': List of extracted categories or empty list if none found
            }
        """
        # Initialize result
        metadata = {
            'title': None,
            'author': None,
            'categories': []
        }
        
        # Get content if not provided
        if content is None:
            # Only extract the first few pages for metadata (faster)
            try:
                extracted = self.extract_content(file_path, include_images=False)
                if isinstance(extracted, dict):
                    content = extracted.get('text', '')
                else:
                    content = extracted
            except Exception as e:
                logger.error(f"Error extracting content for metadata: {e}")
                return metadata
        
        # Process content to extract metadata
        if content and isinstance(content, str):
            # Extract file name as fallback title (without extension)
            file_name = os.path.basename(file_path)
            file_name_no_ext = os.path.splitext(file_name)[0]
            metadata['title'] = file_name_no_ext  # Default to file name
            
            # Get first 1000 characters for metadata extraction (usually in the beginning)
            # Also check the entire content but prioritize matches near the beginning
            beginning = content[:1000]
            
            # Look for title
            for pattern in self.metadata_patterns['title']:
                # First check beginning of document
                match = re.search(pattern, beginning, re.IGNORECASE)
                if match:
                    metadata['title'] = match.group(1).strip()
                    break
                    
                # If not found in beginning, check full document
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    metadata['title'] = match.group(1).strip()
                    break
            
            # Look for author
            for pattern in self.metadata_patterns['author']:
                # Check beginning first
                match = re.search(pattern, beginning, re.IGNORECASE)
                if match:
                    metadata['author'] = match.group(1).strip()
                    break
                    
                # If not found in beginning, check full document
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    metadata['author'] = match.group(1).strip()
                    break
            
            # Look for categories
            for pattern in self.metadata_patterns['categories']:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    categories_str = match.group(1).strip()
                    # Split categories by common delimiters
                    categories = re.split(r'[,;|/]', categories_str)
                    metadata['categories'] = [cat.strip() for cat in categories if cat.strip()]
                    break
        
        return metadata
    
    def get_page_count(self, pdf_path):
        """
        Get the number of pages in a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Number of pages as an integer
        """
        # Use PyPDF2 to get the real page count
        try:
            # We're using global imports now
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return len(pdf_reader.pages)
        except Exception as e:
            logger.error(f"Error getting page count: {str(e)}")
            return 0
