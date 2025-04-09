"""
Custom exceptions for Book Knowledge AI application.
"""

class BookKnowledgeAIError(Exception):
    """Base exception for all application errors."""
    pass


class DocumentProcessingError(BookKnowledgeAIError):
    """Exception raised when document processing fails."""
    pass


class OCRError(DocumentProcessingError):
    """Exception raised when OCR processing fails."""
    pass


class DatabaseError(BookKnowledgeAIError):
    """Exception raised for database errors."""
    pass


class KnowledgeBaseError(BookKnowledgeAIError):
    """Exception raised for knowledge base operations."""
    pass


class AIClientError(BookKnowledgeAIError):
    """Exception raised for AI client operations."""
    pass


class ConfigurationError(BookKnowledgeAIError):
    """Exception raised for configuration errors."""
    pass