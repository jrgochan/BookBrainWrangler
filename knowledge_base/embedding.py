"""
Embedding module for Book Knowledge AI.
Provides functions for creating and using embeddings.
"""

import numpy as np
import hashlib
import importlib.util
from typing import List, Dict, Any, Optional, Union, Callable, TypeVar, Tuple

from utils.logger import get_logger
from knowledge_base.config import DEFAULT_EMBEDDING_DIMENSION
from core.exceptions import EmbeddingError
from ai.utils import create_fallback_embedding as create_ai_fallback_embedding

# Initialize logger
logger = get_logger(__name__)

# Type variables
EmbeddingVector = Union[List[float], List[List[float]]]
T = TypeVar('T')

class SimpleEmbedding:
    """
    Simple embedding class for development/testing purposes.
    Creates deterministic embeddings based on text hash - provides consistency 
    but not semantic meaning.
    """
    
    def __init__(self, dimension: int = DEFAULT_EMBEDDING_DIMENSION):
        """
        Initialize simple embedding function.
        
        Args:
            dimension: Embedding dimension
        """
        self.dimension = dimension
        logger.warning("Using SimpleEmbedding for development/testing only")
    
    def __call__(self, texts: Union[str, List[str]]) -> EmbeddingVector:
        """
        Generate deterministic embeddings for texts.
        
        Args:
            texts: Single text or list of texts to embed
            
        Returns:
            Embeddings as vectors
        """
        if isinstance(texts, str):
            # Single text input
            return self._generate_deterministic_embedding(texts)
        else:
            # List of texts
            return [self._generate_deterministic_embedding(text) for text in texts]
    
    def _generate_deterministic_embedding(self, text: str) -> List[float]:
        """
        Generate a deterministic embedding vector based on text hash.
        This produces consistent embeddings for the same input text,
        but does not capture semantic meaning.
        
        Args:
            text: Text to embed
            
        Returns:
            Deterministic embedding vector
        """
        # Create a seed from the text hash
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        seed = int(text_hash, 16) % (2**32)
        
        # Use the seed for reproducible vector
        rng = np.random.RandomState(seed)
        vector = rng.randn(self.dimension)
        
        # Normalize to unit length
        vector = vector / np.linalg.norm(vector)
        
        return vector.tolist()

def check_embedding_dependencies() -> Tuple[bool, str]:
    """
    Check if embedding libraries are available.
    
    Returns:
        Tuple of (is_available, library_name)
    """
    # Check for sentence-transformers
    if importlib.util.find_spec("sentence_transformers"):
        return True, "sentence_transformers"
    
    # Check for langchain embeddings
    if (importlib.util.find_spec("langchain") and 
        importlib.util.find_spec("langchain.embeddings")):
        return True, "langchain"
    
    # Check for standard transformers
    if importlib.util.find_spec("transformers"):
        return True, "transformers"
    
    return False, "none"

def get_embedding_function(
    model_name: Optional[str] = None,
    force_simple: bool = False
) -> Callable:
    """
    Get an embedding function based on the model name.
    
    Args:
        model_name: Name of the embedding model to use
        force_simple: If True, force use of SimpleEmbedding
        
    Returns:
        Embedding function
    """
    if force_simple:
        logger.info("Using SimpleEmbedding as requested")
        return SimpleEmbedding()
    
    # Check if embedding libraries are available
    has_embeddings, library = check_embedding_dependencies()
    
    if not has_embeddings:
        logger.warning("No embedding libraries found, using SimpleEmbedding")
        return SimpleEmbedding()
    
    # Use the detected library
    try:
        if library == "sentence_transformers":
            # Use sentence transformers if available
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
            
        elif library == "langchain":
            # Use langchain embeddings if available
            from langchain_community.embeddings import HuggingFaceEmbeddings
            
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
            
        elif library == "transformers":
            # Use basic transformers pipeline
            from transformers import pipeline
            
            model = model_name or "sentence-transformers/all-MiniLM-L6-v2"
            logger.info(f"Loading Transformers pipeline for model: {model}")
            
            encoder = pipeline("feature-extraction", model=model)
            
            def transformers_embedder(texts):
                if isinstance(texts, str):
                    # Single text input
                    output = encoder(texts)
                    # Average pooling of token embeddings
                    embedding = np.mean(output[0], axis=0).tolist()
                    return embedding
                else:
                    # List of texts
                    embeddings = []
                    for text in texts:
                        output = encoder(text)
                        # Average pooling of token embeddings
                        embedding = np.mean(output[0], axis=0).tolist()
                        embeddings.append(embedding)
                    return embeddings
            
            return transformers_embedder
        
        else:
            # Fallback to simple embeddings
            logger.warning("No suitable embedding library found, using SimpleEmbedding")
            return SimpleEmbedding()
    
    except Exception as e:
        logger.error(f"Error loading embedding model: {str(e)}")
        logger.warning("Falling back to SimpleEmbedding")
        return SimpleEmbedding()

def get_embeddings(
    texts: Union[str, List[str]],
    model_name: Optional[str] = None,
    force_simple: bool = False
) -> EmbeddingVector:
    """
    Get embeddings for texts.
    
    Args:
        texts: Single text or list of texts to embed
        model_name: Optional model name
        force_simple: If True, force use of SimpleEmbedding
        
    Returns:
        Embeddings as vectors
    """
    if not texts:
        raise EmbeddingError("Cannot embed empty text")
    
    try:
        embedding_function = get_embedding_function(model_name, force_simple)
        return embedding_function(texts)
    
    except Exception as e:
        logger.error(f"Error getting embeddings: {str(e)}")
        
        # Create a fallback embedding as a last resort
        logger.warning("Using fallback embedding method")
        
        if isinstance(texts, str):
            return create_ai_fallback_embedding(texts).embedding
        else:
            return [create_ai_fallback_embedding(text).embedding for text in texts]

def safe_get_embeddings(
    texts: Union[str, List[str]],
    model_name: Optional[str] = None
) -> EmbeddingVector:
    """
    Safely get embeddings for texts, with fallback options.
    This function will never raise an exception.
    
    Args:
        texts: Single text or list of texts to embed
        model_name: Optional model name
        
    Returns:
        Embeddings as vectors
    """
    if not texts:
        if isinstance(texts, str):
            # Return zero vector for empty string
            return [0.0] * DEFAULT_EMBEDDING_DIMENSION
        else:
            # Return empty list for empty list
            return []
    
    try:
        return get_embeddings(texts, model_name)
    except Exception as e:
        logger.error(f"Error in safe_get_embeddings: {str(e)}")
        
        # Use simple embedding as a fallback
        try:
            return get_embeddings(texts, model_name, force_simple=True)
        except Exception as e2:
            logger.error(f"Error using simple embedding fallback: {str(e2)}")
            
            # Final fallback - deterministic embeddings from hash
            if isinstance(texts, str):
                return create_ai_fallback_embedding(texts).embedding
            else:
                return [create_ai_fallback_embedding(text).embedding for text in texts]

# Default embedding function
default_embedding_function = get_embedding_function()