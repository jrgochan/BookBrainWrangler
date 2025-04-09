"""
Document format processors package.
"""

# Import format-specific processors for easy access
from document_processing.formats.pdf import process_pdf, get_page_count, extract_page_as_image, get_pdf_thumbnail
# docx processor will be added later
# from document_processing.formats.docx import process_docx