"""
Text chunking module for the Knowledge Base.
Handles splitting documents into manageable chunks for embedding.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.logger import get_logger

# Get logger
logger = get_logger(__name__)

class TextChunker:
    """
    Handles the chunking of text documents for embedding.
    """
    def __init__(self, chunk_size=1000, chunk_overlap=200, 
                 length_function=len, is_separator_regex=False, separator=None):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            length_function: Function to measure chunk size (default: len)
            is_separator_regex: Whether separator is a regex pattern
            separator: Custom separator pattern (if provided)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function
        self.is_separator_regex = is_separator_regex
        self.separator = separator
        
        self._initialize_splitter()
    
    def _initialize_splitter(self):
        """Initialize the text splitter with current settings."""
        kwargs = {
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "length_function": self.length_function,
            "is_separator_regex": self.is_separator_regex,
        }
        
        if self.separator:
            kwargs["separator"] = self.separator
            
        self.text_splitter = RecursiveCharacterTextSplitter(**kwargs)
        logger.debug(f"Initialized text splitter with chunk_size={self.chunk_size}, "
                     f"chunk_overlap={self.chunk_overlap}")
        
    def split_text(self, text):
        """
        Split text into chunks.
        
        Args:
            text: The text to split
            
        Returns:
            List of text chunks
        """
        if not text:
            logger.warning("Attempted to split empty text")
            return []
            
        try:
            chunks = self.text_splitter.split_text(text)
            logger.debug(f"Split text into {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logger.error(f"Error splitting text: {str(e)}")
            raise
    
    def split_texts(self, texts):
        """
        Split multiple texts into chunks.
        
        Args:
            texts: List of texts to split
            
        Returns:
            List of lists of text chunks
        """
        all_chunks = []
        for i, text in enumerate(texts):
            try:
                chunks = self.split_text(text)
                all_chunks.append(chunks)
            except Exception as e:
                logger.error(f"Error splitting text {i}: {str(e)}")
                # Skip this text but continue with others
                all_chunks.append([])
                
        return all_chunks
    
    def update_settings(self, chunk_size=None, chunk_overlap=None, 
                        is_separator_regex=None, separator=None):
        """
        Update chunking settings and reinitialize the splitter.
        
        Args:
            chunk_size: New chunk size (if provided)
            chunk_overlap: New chunk overlap (if provided)
            is_separator_regex: New is_separator_regex value (if provided)
            separator: New separator value (if provided)
        """
        if chunk_size is not None:
            self.chunk_size = chunk_size
        if chunk_overlap is not None:
            self.chunk_overlap = chunk_overlap
        if is_separator_regex is not None:
            self.is_separator_regex = is_separator_regex
        if separator is not None:
            self.separator = separator
            
        # Reinitialize the splitter with new settings
        self._initialize_splitter()
        logger.info(f"Updated text chunker settings: chunk_size={self.chunk_size}, "
                   f"chunk_overlap={self.chunk_overlap}")
