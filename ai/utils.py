"""
Utility functions for AI clients.
"""

import os
import json
import time
import random
import hashlib
import functools
from typing import Dict, List, Any, Optional, Union, Callable, TypeVar

from utils.logger import get_logger
from ai.models.common import EmbeddingVector

# Get logger for this module
logger = get_logger(__name__)

# Type for retry decorator
F = TypeVar('F', bound=Callable[..., Any])

def retry_with_exponential_backoff(
    func: F,
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 5,
    errors: tuple = (Exception,),
) -> F:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: The function to retry
        initial_delay: Initial delay between retries in seconds
        exponential_base: Base of the exponential backoff
        jitter: Whether to add random jitter to the delay
        max_retries: Maximum number of retries
        errors: Tuple of exceptions to catch and retry on
        
    Returns:
        Wrapped function that will be retried
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        num_retries = 0
        delay = initial_delay
        
        while True:
            try:
                return func(*args, **kwargs)
            
            except errors as e:
                num_retries += 1
                
                if num_retries > max_retries:
                    logger.error(f"Maximum retries ({max_retries}) exceeded.")
                    raise
                
                delay *= exponential_base * (1 + jitter * random.random())
                
                logger.warning(
                    f"Retrying '{func.__name__}' in {delay:.2f}s after error: {str(e)}. "
                    f"Retry {num_retries}/{max_retries}."
                )
                
                time.sleep(delay)
    
    return wrapper

def format_context_prompt(prompt: str, context: str) -> str:
    """
    Format a prompt with context information.
    
    Args:
        prompt: The user prompt
        context: Context information to include
        
    Returns:
        Formatted prompt with context
    """
    if not context:
        return prompt
        
    formatted_prompt = (
        f"Context information is below.\n"
        f"---------------------\n"
        f"{context}\n"
        f"---------------------\n"
        f"Given the context information and not prior knowledge, "
        f"answer the following query:\n{prompt}"
    )
    
    return formatted_prompt

def safe_parse_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Safely parse JSON from text, handling errors.
    
    Args:
        text: JSON string to parse
        
    Returns:
        Parsed JSON as dictionary or None if parsing failed
    """
    try:
        # Find JSON-like content in the text
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = text[start_idx:end_idx+1]
            return json.loads(json_str)
        return None
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON from text: {text}")
        return None

def create_fallback_embedding(text: str, model_name: str = "fallback", dimensions: int = 384) -> EmbeddingVector:
    """
    Create a fallback embedding vector when no embedding service is available.
    This is a simple deterministic hash-based embedding that maintains consistency
    for the same input text but should not be used for semantic similarity.
    
    Args:
        text: Text to create an embedding for
        model_name: Name to assign to the embedding model
        dimensions: Number of dimensions for the embedding vector
        
    Returns:
        EmbeddingVector object
    """
    # Create a consistent hash of the text
    text_hash = hashlib.sha256(text.encode()).digest()
    
    # Generate a deterministic vector from the hash
    # This ensures the same text always produces the same vector
    random.seed(int.from_bytes(text_hash, byteorder='big'))
    
    # Create a vector with the specified number of dimensions
    vector = [(random.random() * 2 - 1) for _ in range(dimensions)]
    
    # Normalize the vector to unit length
    magnitude = sum(x*x for x in vector) ** 0.5
    if magnitude > 0:
        vector = [x / magnitude for x in vector]
    
    logger.warning(f"Using fallback embedding for '{text[:20]}...' with model '{model_name}'")
    
    return EmbeddingVector(values=vector, text=text, model=model_name)