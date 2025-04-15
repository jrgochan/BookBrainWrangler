"""
Tests for Ollama model listing and model information
"""

from typing import Dict, Any, List, Optional

from ai.ollama.client import OllamaClient
from ai.models.common import ModelInfo
from scripts.ollama.test_config import TestConfig
from utils.logger import get_logger

# Get logger
logger = get_logger(__name__)


def test_list_models(client: OllamaClient, config: TestConfig) -> bool:
    """
    Test the list_models functionality.
    
    Args:
        client: Configured OllamaClient instance
        config: Test configuration
        
    Returns:
        bool: True if tests passed, False otherwise
    """
    logger.info("Testing list_models functionality")
    
    try:
        # Get the list of models
        models = client.list_models()
        
        # Check if we got a non-empty list
        if not isinstance(models, list):
            logger.error(f"Expected a list of models, got {type(models)}")
            return False
        
        # Log the models found
        if models:
            logger.info(f"Found {len(models)} models: {', '.join(models)}")
        else:
            logger.warning("No models found. You may need to pull a model using 'ollama pull <model>'")
            logger.info("For example: ollama pull llama2")
        
        # Success even if no models, as long as the API call worked
        logger.info("list_models functionality working - PASS")
        return True
        
    except Exception as e:
        logger.error(f"Error testing list_models: {str(e)}")
        return False


def test_model_info(client: OllamaClient, config: TestConfig) -> bool:
    """
    Test the get_model_info functionality.
    
    Args:
        client: Configured OllamaClient instance
        config: Test configuration
        
    Returns:
        bool: True if tests passed, False otherwise
    """
    logger.info("Testing get_model_info functionality")
    
    try:
        # First get available models to ensure we test with one that exists
        try:
            models = client.list_models()
            test_model = models[0] if models else config.model
        except Exception:
            # If listing models fails, use the configured model
            test_model = config.model
            
        logger.info(f"Getting info for model: {test_model}")
        
        try:
            # Get info for the test model
            model_info = client.get_model_info(test_model)
            
            # Check if we got a ModelInfo object
            if not isinstance(model_info, ModelInfo):
                logger.error(f"Expected ModelInfo, got {type(model_info)}")
                return False
            
            # Log model details
            logger.info(f"Model name: {model_info.name}")
            logger.info(f"Provider: {model_info.provider}")
            logger.info(f"Size: {model_info.size} bytes")
            logger.info(f"Modified at: {model_info.modified_at}")
            
            logger.info("get_model_info functionality working - PASS")
            return True
            
        except Exception as e:
            # Try with the client's default model if the first one failed
            if test_model != client.model_name:
                logger.warning(f"Error getting info for {test_model}, trying with {client.model_name}")
                model_info = client.get_model_info(client.model_name)
                logger.info(f"Successfully retrieved info for {client.model_name}")
                return True
            else:
                # If we're already using the default model, re-raise the exception
                raise
                
    except Exception as e:
        logger.error(f"Error testing get_model_info: {str(e)}")
        logger.warning("This may indicate that you need to pull a model first. Try: ollama pull llama2")
        return False
