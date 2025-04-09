"""
Utility functions for the Ollama client
"""

import json
import logging
import requests
from typing import Dict, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)

def safe_parse_json(response: requests.Response, endpoint_name: str) -> Dict[str, Any]:
    """
    Safely parse JSON from an HTTP response, with proper error handling.
    
    Args:
        response: requests.Response object to parse
        endpoint_name: Name of the endpoint (for logging purposes)
        
    Returns:
        dict: Parsed JSON data or None if parsing failed
        
    Raises:
        json.JSONDecodeError: If JSON parsing fails (caller should handle this)
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
            
            # If all attempts failed, re-raise the original error
            raise
    except json.JSONDecodeError as e:
        # Log the error and a sample of the problematic response
        logger.error(f"JSON parse error in {endpoint_name} response: {str(e)}")
        logger.debug(f"Raw response causing JSON error: {response.text[:500]}")
        raise  # Re-raise for handling by the caller

def create_fallback_embedding(dimensions: int = 384) -> list:
    """
    Create a fallback embedding vector of zeros with the specified dimensions.
    
    Args:
        dimensions: Number of dimensions for the embedding vector
        
    Returns:
        list: A list of zeros of the specified length
    """
    try:
        import numpy as np
        return list(np.zeros(dimensions).astype(float))
    except ImportError:
        logger.error("Failed to import numpy for fallback embedding")
        # Super simple fallback if numpy is not available
        return [0.0] * dimensions

def format_context_prompt(context: str, prompt: str) -> str:
    """
    Format a prompt with context information for the model.
    
    Args:
        context: The context information to include
        prompt: The user's prompt
        
    Returns:
        str: The formatted prompt with context
    """
    return (
        "Here is some information that may be relevant to the user's question:\n\n"
        f"{context}\n\n"
        "Now please respond to the user's question based on this information:\n\n"
        f"{prompt}"
    )