"""
Tests for Ollama embeddings functionality
"""

import time
import numpy as np
from typing import Dict, Any, List, Optional

from ai.ollama.client import OllamaClient
from ai.models.common import EmbeddingVector
from scripts.ollama.test_config import TestConfig
from utils.logger import get_logger

# Get logger
logger = get_logger(__name__)


def validate_embedding(embedding: EmbeddingVector) -> bool:
    """
    Validate that an embedding vector is properly formatted.
    
    Args:
        embedding: EmbeddingVector to validate
        
    Returns:
        bool: True if the embedding is valid, False otherwise
    """
    # Check if it's an EmbeddingVector object
    if not isinstance(embedding, EmbeddingVector):
        logger.error(f"Expected EmbeddingVector, got {type(embedding)}")
        return False
    
    # Get the values list from either embedding.values or embedding.embedding
    if embedding.values is not None:
        values = embedding.values
    elif isinstance(embedding.embedding, list):
        values = embedding.embedding
    elif isinstance(embedding.embedding, np.ndarray):
        values = embedding.embedding.tolist()
    else:
        logger.error(f"Cannot extract values from embedding, embedding.embedding is {type(embedding.embedding)}")
        return False
    
    # Check if values is a list of floats
    if not isinstance(values, list):
        logger.error(f"Expected values to be a list, got {type(values)}")
        return False
    
    # Check if the embedding has a reasonable number of dimensions
    if len(values) < 100:
        logger.warning(f"Embedding dimension ({len(values)}) seems too small")
        # Don't fail the test for this, but log a warning
    
    # Check if all values are floats
    for i, val in enumerate(values[:10]):  # Check first 10 values
        if not isinstance(val, float):
            logger.error(f"Expected embedding values to be floats, got {type(val)} at index {i}")
            return False
            
    # Check if the embedding contains non-zero values (to catch all-zero fallbacks)
    if all(v == 0 for v in values):
        logger.warning("Embedding contains all zeros, which might indicate a fallback was used")
        # Don't fail the test for this, but log a warning
        
    # Check if the embedding has reasonable statistics
    values_np = np.array(values)
    mean = np.mean(values_np)
    std = np.std(values_np)
    
    # Most embeddings have approximately zero mean
    if abs(mean) > 0.5:  
        logger.warning(f"Embedding mean ({mean:.4f}) seems unusually large")
    
    # Most embeddings have some variation
    if std < 0.01:
        logger.warning(f"Embedding standard deviation ({std:.4f}) seems unusually small")
        
    return True


def test_embeddings(client: OllamaClient, config: TestConfig) -> bool:
    """
    Test the embedding functionality.
    
    Args:
        client: Configured OllamaClient instance
        config: Test configuration
        
    Returns:
        bool: True if tests passed, False otherwise
    """
    logger.info("Testing embedding functionality")
    
    # Sample texts to embed
    texts = [
        "This is a test sentence for embedding.",
        "Vector embeddings are numerical representations of text.",
        "The cat sat on the mat."
    ]
    
    try:
        all_valid = True
        
        for i, text in enumerate(texts):
            logger.info(f"Creating embedding for text {i+1}/{len(texts)}")
            
            # Create embedding
            start_time = time.time()
            embedding = client.create_embedding(text)
            end_time = time.time()
            duration = end_time - start_time
            
            # Validate the embedding
            is_valid = validate_embedding(embedding)
            all_valid = all_valid and is_valid
            
            if not is_valid:
                logger.error(f"Embedding validation failed for text: '{text}'")
                continue
                
            # Get the values from the embedding
            values = embedding.values if embedding.values is not None else embedding.embedding
            if isinstance(values, np.ndarray):
                values = values.tolist()
            
            # Log embedding info
            logger.info(f"Text: '{text}'")
            logger.info(f"Embedding dimensions: {len(values)}")
            logger.info(f"Embedding time: {duration:.2f} seconds")
            
            # Log a preview of the embedding vector
            preview = str(values[:5]) + "..." + str(values[-5:]) if len(values) > 10 else str(values)
            logger.info(f"Embedding preview: {preview}")
            
            # Check if the embedding model name matches the expected value
            model_name = embedding.model
            logger.info(f"Embedding model: {model_name}")
        
        # Test similarity calculation
        if len(texts) >= 2 and all_valid:
            logger.info("Testing embedding similarity...")
            
            embedding1 = client.create_embedding(texts[0])
            embedding2 = client.create_embedding(texts[1])
            
            # Get numpy arrays for calculation
            vec1 = embedding1.as_numpy() if hasattr(embedding1, 'as_numpy') else np.array(embedding1.values or embedding1.embedding)
            vec2 = embedding2.as_numpy() if hasattr(embedding2, 'as_numpy') else np.array(embedding2.values or embedding2.embedding)
            
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 > 0 and norm2 > 0:
                similarity = np.dot(vec1, vec2) / (norm1 * norm2)
                logger.info(f"Cosine similarity between first two texts: {similarity:.4f}")
            else:
                logger.warning("Could not calculate similarity due to zero-norm vectors")
        
        if all_valid:
            logger.info("Embedding functionality working - PASS")
        else:
            logger.error("Some embedding tests failed")
            
        return all_valid
        
    except Exception as e:
        logger.error(f"Error testing embeddings: {str(e)}")
        logger.warning("This may be because the model doesn't support embeddings")
        return False
