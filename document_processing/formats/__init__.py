"""
Document format-specific processing modules.
"""

from document_processing.formats.pdf import process_pdf, get_page_count, extract_page_as_image
from document_processing.formats.docx import process_docx, extract_images_from_docx

__all__ = [
    'process_pdf',
    'get_page_count',
    'extract_page_as_image',
    'process_docx',
    'extract_images_from_docx',
]