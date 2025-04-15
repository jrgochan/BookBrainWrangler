#!/usr/bin/env python
"""
Main script for testing Ollama integration.
Runs a series of tests to verify Ollama client functionality.
"""

import os
import sys
import argparse
import time
from typing import List, Dict, Any, Optional, Union

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ai.ollama.client import OllamaClient
from utils.logger import get_logger

# Import test modules
from scripts.ollama.test_connectivity import test_connectivity
from scripts.ollama.test_models import test_list_models, test_model_info
from scripts.ollama.test_generation import test_text_generation, test_chat_generation
from scripts.ollama.test_embeddings import test_embeddings
from scripts.ollama.test_capabilities import test_model_capabilities, test_vision_capability
from scripts.ollama.test_config import TestConfig

# Get logger
logger = get_logger(__name__)

def setup_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Test Ollama integration')
    
    parser.add_argument(
        '--host',
        type=str,
        default=None,
        help='Ollama server host (default: from env or localhost)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=None,
        help='Ollama server port (default: from env or 11434)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='llama2',
        help='Model to test (default: llama2)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        help='Request timeout in seconds (default: 60)'
    )
    
    parser.add_argument(
        '--test',
        type=str,
        choices=['all', 'connectivity', 'models', 'generation', 'embeddings', 'capabilities'],
        default='all',
        help='Which tests to run (default: all)'
    )
    
    parser.add_argument(
        '--vision-model',
        type=str,
        default=None,
        help='Specific model to test vision capabilities with (e.g., llava:7b, mistral-small3.1:24b)'
    )
    
    parser.add_argument(
        '--wait-for-server',
        action='store_true',
        help='Wait for Ollama server to be available before starting tests'
    )
    
    parser.add_argument(
        '--wait-timeout',
        type=int,
        default=60,
        help='Maximum time to wait for server in seconds (default: 60)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser.parse_args()

def wait_for_server(client: OllamaClient, timeout: int = 60) -> bool:
    """
    Wait for the Ollama server to become available.
    
    Args:
        client: Configured OllamaClient
        timeout: Maximum time to wait in seconds
        
    Returns:
        bool: True if server became available, False if timeout reached
    """
    logger.info(f"Waiting for Ollama server at {client.host}:{client.port} (timeout: {timeout}s)")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        if client.is_available():
            logger.info(f"Ollama server is available")
            return True
        
        logger.info("Ollama server not available yet, waiting...")
        time.sleep(5)
    
    logger.error(f"Timeout reached waiting for Ollama server")
    return False

def run_tests(config: TestConfig) -> Dict[str, bool]:
    """
    Run the specified tests.
    
    Args:
        config: Test configuration
        
    Returns:
        Dictionary mapping test names to pass/fail results
    """
    results = {}
    client = OllamaClient(
        host=config.host,
        port=config.port,
        model=config.model,
        timeout=config.timeout
    )
    
    # Wait for server if requested
    if config.wait_for_server and not wait_for_server(client, config.wait_timeout):
        logger.error("Aborting tests because Ollama server not available")
        return {"server_available": False}
    
    # Store the list of available models in the config
    try:
        config.available_models = client.list_models()
        if config.available_models:
            logger.info(f"Found {len(config.available_models)} available models")
        else:
            logger.warning("No models found on the Ollama server")
    except Exception as e:
        logger.warning(f"Could not retrieve list of models: {str(e)}")
        config.available_models = []

    # Run connectivity tests
    if config.test in ['all', 'connectivity']:
        logger.info("--- Running connectivity tests ---")
        results["connectivity"] = test_connectivity(client, config)
    
    # Run model tests
    if config.test in ['all', 'models']:
        logger.info("--- Running model tests ---")
        results["list_models"] = test_list_models(client, config)
        results["model_info"] = test_model_info(client, config)
    
    # Run generation tests
    if config.test in ['all', 'generation']:
        logger.info("--- Running generation tests ---")
        results["text_generation"] = test_text_generation(client, config)
        results["chat_generation"] = test_chat_generation(client, config)
    
    # Run embedding tests
    if config.test in ['all', 'embeddings']:
        logger.info("--- Running embedding tests ---")
        results["embeddings"] = test_embeddings(client, config)
        
    # Run capabilities tests (v0.6.4+ features)
    if config.test in ['all', 'capabilities']:
        logger.info("--- Running capabilities tests (Ollama v0.6.4+) ---")
        results["model_capabilities"] = test_model_capabilities(client, config)
        
        # Only run vision capability test if model_capabilities passes
        if results.get("model_capabilities", False):
            results["vision_capability"] = test_vision_capability(client, config)
    
    return results

def print_results(results: Dict[str, bool]) -> None:
    """
    Print the test results in a readable format.
    
    Args:
        results: Dictionary mapping test names to pass/fail results
    """
    print("\n=== Ollama Test Results ===")
    
    passed = 0
    failed = 0
    
    for test, result in results.items():
        status = "PASS" if result else "FAIL"
        status_color = "\033[92m" if result else "\033[91m"  # Green for pass, red for fail
        print(f"{status_color}{status}\033[0m - {test}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nSummary: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\033[92mAll tests passed!\033[0m")
    else:
        print(f"\033[91m{failed} tests failed!\033[0m")

def main() -> None:
    """Main function to run the tests."""
    args = setup_args()
    
    # Create test configuration
    config = TestConfig(
        host=args.host,
        port=args.port,
        model=args.model,
        timeout=args.timeout,
        test=args.test,
        wait_for_server=args.wait_for_server,
        wait_timeout=args.wait_timeout,
        verbose=args.verbose,
        vision_model=args.vision_model
    )
    
    try:
        # Run the tests
        results = run_tests(config)
        
        # Print results
        print_results(results)
        
        # Exit with appropriate code
        if all(results.values()):
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
