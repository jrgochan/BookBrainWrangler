"""
Tests for Ollama text and chat generation functionality
"""

import time
from typing import Dict, Any, List, Optional

from ai.ollama.client import OllamaClient
from scripts.ollama.test_config import TestConfig
from utils.logger import get_logger

# Get logger
logger = get_logger(__name__)


def test_text_generation(client: OllamaClient, config: TestConfig) -> bool:
    """
    Test the text generation functionality.
    
    Args:
        client: Configured OllamaClient instance
        config: Test configuration
        
    Returns:
        bool: True if tests passed, False otherwise
    """
    logger.info("Testing text generation functionality")
    
    prompt = config.sample_prompt
    logger.info(f"Using prompt: {prompt}")
    
    try:
        # Generate a response
        start_time = time.time()
        response = client.generate_response(prompt)
        end_time = time.time()
        duration = end_time - start_time
        
        # Check if we got a non-empty response
        if not isinstance(response, str):
            logger.error(f"Expected a string response, got {type(response)}")
            return False
        
        if not response.strip():
            logger.error("Got an empty response from the model")
            return False
        
        # Log a preview of the response
        preview = response[:100] + "..." if len(response) > 100 else response
        logger.info(f"Response preview: {preview}")
        logger.info(f"Response length: {len(response)} characters")
        logger.info(f"Generation time: {duration:.2f} seconds")
        
        # Additional parameters test
        if config.verbose:
            logger.info("Testing text generation with additional parameters...")
            
            # Try with different temperature
            temp_response = client.generate_response(prompt, temperature=0.2)
            temp_preview = temp_response[:100] + "..." if len(temp_response) > 100 else temp_response
            logger.info(f"Response with temperature=0.2 preview: {temp_preview}")
        
        logger.info("Text generation functionality working - PASS")
        return True
        
    except Exception as e:
        logger.error(f"Error testing text generation: {str(e)}")
        return False


def test_chat_generation(client: OllamaClient, config: TestConfig) -> bool:
    """
    Test the chat generation functionality.
    
    Args:
        client: Configured OllamaClient instance
        config: Test configuration
        
    Returns:
        bool: True if tests passed, False otherwise
    """
    logger.info("Testing chat generation functionality")
    
    messages = config.sample_messages
    system_prompt = config.sample_system_prompt
    
    logger.info(f"Using system prompt: {system_prompt}")
    logger.info(f"Using messages: {messages}")
    
    try:
        # Generate a chat response
        start_time = time.time()
        response = client.generate_chat_response(
            messages=messages,
            system_prompt=system_prompt
        )
        end_time = time.time()
        duration = end_time - start_time
        
        # Check if we got a non-empty response
        if not isinstance(response, str):
            logger.error(f"Expected a string response, got {type(response)}")
            return False
        
        if not response.strip():
            logger.error("Got an empty response from the model")
            return False
        
        # Log a preview of the response
        preview = response[:100] + "..." if len(response) > 100 else response
        logger.info(f"Response preview: {preview}")
        logger.info(f"Response length: {len(response)} characters")
        logger.info(f"Generation time: {duration:.2f} seconds")
        
        # Test with context
        if config.verbose:
            logger.info("Testing chat generation with context...")
            
            context = "Germany is a country in Central Europe. Its capital is Berlin."
            context_response = client.generate_chat_response(
                messages=messages,
                system_prompt=system_prompt,
                context=context
            )
            
            context_preview = context_response[:100] + "..." if len(context_response) > 100 else context_response
            logger.info(f"Response with context preview: {context_preview}")
        
        logger.info("Chat generation functionality working - PASS")
        return True
        
    except Exception as e:
        logger.error(f"Error testing chat generation: {str(e)}")
        return False
