"""
Ollama Client for handling AI model interactions.
This client communicates with the Ollama API to perform operations like:
- Checking server status
- Listing available models
- Generating text responses
- Generating chat completions
- Creating embeddings

This module is maintained for backward compatibility and imports from the refactored ollama package.
For new code, import directly from the ollama package instead.
"""

import logging
import warnings

# Log a deprecation warning
logger = logging.getLogger(__name__)
logger.warning(
    "Importing from ollama_client.py is deprecated. "
    "Please update your imports to use 'from ollama import OllamaClient' instead."
)

# Import from the refactored module
from ollama.client import OllamaClient

# For backward compatibility
__all__ = ['OllamaClient']