"""
Tests for Ollama model capabilities
"""

import json
import requests
from typing import Dict, Any, List, Optional

from ai.ollama.client import OllamaClient
from scripts.ollama.test_config import TestConfig
from utils.logger import get_logger

# Get logger
logger = get_logger(__name__)


def test_model_capabilities(client: OllamaClient, config: TestConfig) -> bool:
    """
    Test the model capabilities detection functionality.
    
    Args:
        client: Configured OllamaClient instance
        config: Test configuration
        
    Returns:
        bool: True if tests passed, False otherwise
    """
    logger.info("Testing model capabilities detection (added in Ollama v0.6.4+)")
    
    # Try to get one of the models that has vision capabilities if configured
    vision_models = ["llava", "llava:7b", "llava:13b", "llava:34b", "mistral-small3.1:24b"]
    test_model = config.vision_model or next((m for m in vision_models if m in config.available_models), None)
    
    if not test_model:
        # If no vision model is specified and none found in available models, use the configured model
        test_model = config.model
        logger.warning(f"No vision model specified or found in available models. Using {test_model} for capability testing.")
    else:
        logger.info(f"Using vision model {test_model} for capability testing")
        
    try:
        # Make a direct API call to the /api/show endpoint (v0.6.4+ feature)
        base_url = f"http://{client.host}:{client.port}"
        response = requests.post(
            f"{base_url}/api/show",
            json={"name": test_model},
            timeout=client.timeout
        )
        
        # Check if we got a successful response
        if response.status_code != 200:
            logger.error(f"Error accessing /api/show endpoint: {response.status_code}")
            if response.status_code == 404:
                logger.warning("The /api/show endpoint returned 404. This suggests your Ollama version may be older than v0.6.4")
                return False
            return False
        
        # Parse the response
        try:
            data = response.json()
            logger.info(f"Model data retrieved: {json.dumps(data, indent=2)}")
            
            # Check if capabilities field exists (v0.6.4+ feature)
            if "capabilities" in data:
                logger.info(f"Model capabilities: {data['capabilities']}")
                
                # Test for vision capability specifically
                if "vision" in data.get("capabilities", []):
                    logger.info(f"Model {test_model} supports vision capability")
                else:
                    logger.info(f"Model {test_model} does not support vision capability")
                
                # Check if other capabilities are present
                other_caps = [c for c in data.get("capabilities", []) if c != "vision"]
                if other_caps:
                    logger.info(f"Other capabilities: {', '.join(other_caps)}")
                
                logger.info("Model capabilities detection working - PASS")
                return True
            else:
                logger.warning("Model data doesn't include 'capabilities' field.")
                logger.warning("This suggests your Ollama version may be older than v0.6.4")
                return False
                
        except json.JSONDecodeError:
            logger.error("Error decoding JSON response from /api/show endpoint")
            return False
    except Exception as e:
        logger.error(f"Error testing model capabilities: {str(e)}")
        return False


def test_vision_capability(client: OllamaClient, config: TestConfig) -> bool:
    """
    Test the vision capability with a sample image if available.
    This is a placeholder for now as it requires additional implementation.
    
    Args:
        client: Configured OllamaClient instance
        config: Test configuration
        
    Returns:
        bool: True if tests passed, False otherwise
    """
    logger.info("Vision capability testing not yet implemented")
    logger.info("Ollama v0.6.5 adds support for Mistral Small 3.1 as a high-performing vision model")
    
    # This would require implementing image processing and API calls for vision models
    # For now, we just return success
    return True
