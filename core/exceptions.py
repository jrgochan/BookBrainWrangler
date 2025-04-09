"""
Custom exceptions for the Book Knowledge AI application.
"""

class BookKnowledgeError(Exception):
    """Base exception for all application-specific errors."""
    pass


class DatabaseError(BookKnowledgeError):
    """Exception raised for database-related errors."""
    pass


class DocumentProcessingError(BookKnowledgeError):
    """Exception raised for document processing errors."""
    pass


class OCRError(DocumentProcessingError):
    """Exception raised for OCR-related errors."""
    pass


class AIClientError(BookKnowledgeError):
    """Exception raised for AI client-related errors."""
    pass


class KnowledgeBaseError(BookKnowledgeError):
    """Exception raised for knowledge base-related errors."""
    pass


class ConfigurationError(BookKnowledgeError):
    """Exception raised for configuration-related errors."""
    pass


class UIError(BookKnowledgeError):
    """Exception raised for UI-related errors."""
    pass


class ValidationError(BookKnowledgeError):
    """Exception raised for validation errors."""
    pass


class PermissionError(BookKnowledgeError):
    """Exception raised for permission-related errors."""
    pass