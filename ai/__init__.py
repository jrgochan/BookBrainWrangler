"""
AI module for Book Knowledge AI application.
Contains AI clients and utility functions for interacting with AI models.
"""

from typing import Optional, Dict, Any

from ai.client import AIClient
from ai.factory import AIClientFactory
from ai.models.common import Message, ModelInfo, EmbeddingVector

def get_default_client() -> AIClient:
    """
    Get the default AI client based on available services.
    
    Returns:
        An instance of the most appropriate AI client
    """
    return AIClientFactory.create_default_client()

def create_client(client_type: str, **kwargs) -> AIClient:
    """
    Create an AI client of the specified type.
    
    Args:
        client_type: Type of client to create ('ollama', 'openai', 'huggingface', 'openrouter')
        **kwargs: Arguments to pass to the client constructor
        
    Returns:
        An instance of the requested AI client
    """
    return AIClientFactory.create_client(client_type, **kwargs)

# Make common types available at the module level
__all__ = [
    'AIClient',
    'AIClientFactory',
    'Message',
    'ModelInfo',
    'EmbeddingVector',
    'get_default_client',
    'create_client'
]