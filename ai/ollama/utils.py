"""
Utility functions for the Ollama client
"""

import json
import requests
import numpy as np
from typing import Dict, Any, Optional, Union, List

from utils.logger import get_logger
from ai.ollama.models import EmbeddingVector

# Get logger for this module
logger = get_logger(__name__)

def safe_parse_json(response: requests.Response, endpoint_name: str) -> Dict[str, Any]:
    """
    Safely parse JSON from an HTTP response, with proper error handling.
    
    Args:
        response: requests.Response object to parse
        endpoint_name: Name of the endpoint (for logging purposes)
        
    Returns:
        Parsed JSON data or empty dict if parsing failed
    """
    try:
        # Log raw response for debugging (limited sample to avoid large logs)
        raw_sample = response.text[:200] + ("..." if len(response.text) > 200 else "")
        logger.debug(f"Raw response from {endpoint_name} endpoint: {raw_sample}")
        
        # Special handling for "Extra data" errors (common with line-delimited responses)
        try:
            # First try the standard JSON parsing
            return response.json()
        except json.JSONDecodeError as e:
            # If it's an "Extra data" error, try to extract just the first valid JSON object
            if "Extra data" in str(e):
                logger.warning(f"Detected possible line-delimited JSON response in {endpoint_name} endpoint")
                # Try to extract only the first JSON object by finding its end
                first_json_end = e.pos
                first_json_str = response.text[:first_json_end]
                
                try:
                    return json.loads(first_json_str)
                except json.JSONDecodeError:
                    # If that still fails, try a more aggressive approach to find a valid JSON
                    logger.warning(f"First JSON extraction failed, trying line-by-line parsing")
                    lines = response.text.splitlines()
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            return json.loads(line)
                        except json.JSONDecodeError:
                            continue
            
            # If all attempts failed, log the error and return an empty dict
            logger.error(f"JSON parse error in {endpoint_name} response: {str(e)}")
            return {}
    except Exception as e:
        # Log any other errors
        logger.error(f"Error parsing response from {endpoint_name}: {str(e)}")
        return {}

def create_fallback_embedding(text: str, model: str, dimensions: int = 384) -> EmbeddingVector:
    """
    Create a fallback embedding vector when the real embedding fails.
    
    Args:
        text: The text that was supposed to be embedded
        model: The model that was supposed to create the embedding
        dimensions: Number of dimensions for the embedding vector
        
    Returns:
        EmbeddingVector with all zeros
    """
    logger.warning(f"Using fallback embedding for text: '{text[:50]}...'")
    zeros = np.zeros(dimensions).astype(float).tolist()
    return EmbeddingVector(
        model=f"{model}(fallback)",
        dimensions=dimensions,
        embedding=zeros
    )

def format_context_prompt(prompt: str, context: str) -> str:
    """
    Format a prompt with context information for the model.
    
    Args:
        prompt: The user's prompt
        context: The context information to include
        
    Returns:
        The formatted prompt with context
    """
    if not context:
        return prompt
        
    return (
        "Here is some information that may be relevant to the user's question:\n\n"
        f"{context}\n\n"
        "Now please respond to the user's question based on this information:\n\n"
        f"{prompt}"
    )
