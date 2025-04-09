"""
Embedding module for Book Knowledge AI.
Provides functions for creating and using embeddings.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Union, Callable

from utils.logger import get_logger
from knowledge_base.config import DEFAULT_EMBEDDING_DIMENSION
from core.exceptions import EmbeddingError

# Initialize logger
logger = get_logger(__name__)

class SimpleEmbedding:
    """
    Simple embedding class for development/testing purposes.
    Creates random embeddings of fixed dimensionality.
    """
    
    def __init__(self, dimension: int = DEFAULT_EMBEDDING_DIMENSION):
        """
        Initialize simple embedding function.
        
        Args:
            dimension: Embedding dimension
        """
        self.dimension = dimension
        logger.warning("Using SimpleEmbedding for development/testing only")
    
    def __call__(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate random embeddings for texts.
        
        Args:
            texts: Single text or list of texts to embed
            
        Returns:
            Embeddings as vectors
        """
        if isinstance(texts, str):
            # Single text input
            return self._generate_random_embedding()
        else:
            # List of texts
            return [self._generate_random_embedding() for _ in texts]
    
    def _generate_random_embedding(self) -> List[float]:
        """
        Generate a random embedding vector.
        
        Returns:
            Random embedding vector
        """
        # Generate random vector
        vector = np.random.randn(self.dimension)
        
        # Normalize to unit length
        vector = vector / np.linalg.norm(vector)
        
        return vector.tolist()

def get_embedding_function(
    model_name: Optional[str] = None
) -> Callable:
    """
    Get an embedding function based on the model name.
    
    Args:
        model_name: Name of the embedding model to use
        
    Returns:
        Embedding function
    """
    # Try to load actual embedding models if available
    try:
        # Try sentence transformers first
        from sentence_transformers import SentenceTransformer
        
        model = model_name or "all-MiniLM-L6-v2"
        logger.info(f"Loading SentenceTransformer model: {model}")
        
        encoder = SentenceTransformer(model)
        
        def sentence_transformer_embedder(texts):
            # Handle both single string and list inputs
            if isinstance(texts, str):
                return encoder.encode(texts).tolist()
            else:
                return encoder.encode(texts).tolist()
                
        return sentence_transformer_embedder
        
    except ImportError:
        try:
            # Try langchain embeddings
            from langchain.embeddings import HuggingFaceEmbeddings
            
            model = model_name or "all-MiniLM-L6-v2"
            logger.info(f"Loading HuggingFaceEmbeddings model: {model}")
            
            encoder = HuggingFaceEmbeddings(model_name=model)
            
            def langchain_embedder(texts):
                # Handle both single string and list inputs
                if isinstance(texts, str):
                    return encoder.embed_query(texts)
                else:
                    return encoder.embed_documents(texts)
                    
            return langchain_embedder
            
        except ImportError:
            # Fallback to simple embeddings
            logger.warning("No embedding libraries found, using SimpleEmbedding")
            return SimpleEmbedding()
    
    except Exception as e:
        logger.error(f"Error loading embedding model: {str(e)}")
        logger.warning("Falling back to SimpleEmbedding")
        return SimpleEmbedding()

def get_embeddings(
    texts: Union[str, List[str]],
    model_name: Optional[str] = None
) -> Union[List[float], List[List[float]]]:
    """
    Get embeddings for texts.
    
    Args:
        texts: Single text or list of texts to embed
        model_name: Optional model name
        
    Returns:
        Embeddings as vectors
    """
    try:
        embedding_function = get_embedding_function(model_name)
        return embedding_function(texts)
    
    except Exception as e:
        logger.error(f"Error getting embeddings: {str(e)}")
        raise EmbeddingError(f"Failed to generate embeddings: {str(e)}")

# Default embedding function
default_embedding_function = get_embedding_function()