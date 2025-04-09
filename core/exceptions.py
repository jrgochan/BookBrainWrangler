"""
Exceptions module for Book Knowledge AI application.
"""

class BaseError(Exception):
    """Base exception class for Book Knowledge AI."""
    pass

class DocumentProcessingError(BaseError):
    """Exception raised for errors in document processing."""
    pass

class DocumentFormatError(DocumentProcessingError):
    """Exception raised for unsupported document formats."""
    pass

class MetadataExtractionError(DocumentProcessingError):
    """Exception raised for metadata extraction errors."""
    pass

class OcrError(DocumentProcessingError):
    """Exception raised for OCR processing errors."""
    pass

class VectorStoreError(BaseError):
    """Exception raised for vector store operations."""
    pass

class EmbeddingError(VectorStoreError):
    """Exception raised for embedding operations."""
    pass

class SearchError(VectorStoreError):
    """Exception raised for search operations."""
    pass

class AIError(BaseError):
    """Exception raised for AI operations."""
    pass

class ModelNotFoundError(AIError):
    """Exception raised when an AI model is not found."""
    pass

class ResponseGenerationError(AIError):
    """Exception raised when generating a response fails."""
    pass

class DatabaseError(BaseError):
    """Exception raised for database operations."""
    pass

class ConfigurationError(BaseError):
    """Exception raised for configuration errors."""
    pass