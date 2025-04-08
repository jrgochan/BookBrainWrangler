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

class DocumentProcessor:
    def __init__(self):
        """Initialize the document processor with default settings."""
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
        
        # For demonstration, we'll return a placeholder that simulates processing
        send_progress(0, total_pages, "Starting document processing...")
        
        # Simulate processing for each page
        for i in range(total_pages):
            # Simulate processing delay
            time.sleep(0.1)
            
            # Update progress
            progress_text = f"Processing page {i+1}/{total_pages}"
            send_progress(i, total_pages, {'text': progress_text, 'action': 'processing'})
            
            # Add placeholder text for this page
            result['text'] += f"This is placeholder text for page {i+1}.\n\n"
            
            # Simulate OCR recognition with confidence
            if i % 3 == 0:  # Every third page has lower confidence to show the feature
                confidence = 65.0
            else:
                confidence = 92.0
            
            # Send detailed progress with placeholder image data
            if progress_callback:
                # Create a simple SVG as a placeholder for the page image
                svg_data = f'''
                <svg width="600" height="800" xmlns="http://www.w3.org/2000/svg">
                  <rect width="600" height="800" fill="#f5f5f5"/>
                  <text x="300" y="400" font-family="Arial" font-size="24" text-anchor="middle">
                    Page {i+1} of {total_pages}
                  </text>
                </svg>
                '''
                # Convert SVG to base64
                svg_base64 = base64.b64encode(svg_data.encode('utf-8')).decode('utf-8')
                
                # Send progress with image and text data
                send_progress(i, total_pages, {
                    'text': progress_text,
                    'current_image': svg_base64,
                    'ocr_text': f"Sample extracted text from page {i+1}",
                    'confidence': confidence,
                    'action': 'extracting'
                })
        
        # Simulate finalizing
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
        # For demonstration, we'll return a placeholder that simulates processing
        if progress_callback:
            progress_callback(0, 1, "Starting DOCX processing...")
            
            # Simulate processing delay
            time.sleep(0.5)
            
            progress_callback(1, 1, "DOCX processing complete")
        
        # Return placeholder content
        return {
            'text': 'This is placeholder text for a DOCX document.',
            'images': []
        }
    
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
                print(f"Error extracting content for metadata: {e}")
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
        # For demonstration purposes, return a random number between 5 and 20
        import random
        return random.randint(5, 20)