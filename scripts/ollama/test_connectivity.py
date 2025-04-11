"""
Tests for Ollama server connectivity
"""

import time
from typing import Dict, Any

from ai.ollama.client import OllamaClient
from scripts.ollama.test_config import TestConfig
from utils.logger import get_logger

# Get logger
logger = get_logger(__name__)


def test_connectivity(client: OllamaClient, config: TestConfig) -> bool:
    """
    Test basic connectivity to the Ollama server.
    
    Args:
        client: Configured OllamaClient instance
        config: Test configuration
        
    Returns:
        bool: True if tests passed, False otherwise
    """
    logger.info(f"Testing connectivity to Ollama server at {client.host}:{client.port}")
    
    try:
        # Test 1: Check if the server is running (basic socket connection)
        logger.info("Testing server connection...")
        server_running = client.is_server_running()
        
        if not server_running:
            logger.error(f"Ollama server is not running at {client.host}:{client.port}")
            logger.error("Please ensure Ollama is installed and running")
            logger.error("Installation instructions: https://github.com/ollama/ollama")
            return False
        
        logger.info("Server is running - PASS")
        
        # Test 2: Check if the API is available
        logger.info("Testing API availability...")
        api_available = client.is_available()
        
        if not api_available:
            logger.error(f"Ollama API is not available at {client.host}:{client.port}")
            logger.error("The server is running but the API is not responding")
            return False
        
        logger.info("API is available - PASS")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during connectivity tests: {str(e)}")
        return False
