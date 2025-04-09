"""
Document processing module for Book Knowledge AI application.
Contains utilities for extracting and processing text and metadata from documents.
"""

# Import key functions for easy access
from document_processing.ocr import perform_ocr, ocr_image_to_text, process_image_with_ocr
from document_processing.processor import DocumentProcessor