"""
Document processing package for handling document content extraction.
"""

from document_processing.processor import DocumentProcessor
from document_processing.ocr import OCR_ENGINES, initialize_ocr_engine, perform_ocr, detect_tesseract_path
from document_processing.pdf_processor import process_pdf, get_page_count, extract_page_as_image
from document_processing.docx_processor import process_docx, extract_images_from_docx
from document_processing.metadata import extract_metadata

__all__ = [
    'DocumentProcessor',
    'OCR_ENGINES',
    'initialize_ocr_engine',
    'perform_ocr',
    'detect_tesseract_path',
    'process_pdf',
    'get_page_count',
    'extract_page_as_image',
    'process_docx',
    'extract_images_from_docx',
    'extract_metadata'
]