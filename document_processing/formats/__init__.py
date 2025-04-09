"""
Document format processing modules.

This package contains modules for processing different document formats,
such as PDF, DOCX, etc.
"""

# Module-level imports for easier usage
from document_processing.formats.pdf import PDFProcessor
from document_processing.formats.docx import DOCXProcessor

__all__ = ['PDFProcessor', 'DOCXProcessor']