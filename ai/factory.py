"""
AI client factory for Book Knowledge AI.
"""

import os
from typing import Dict, List, Any, Optional, Type, Union

from utils.logger import get_logger
from core.exceptions import AIClientError
from ai.client import AIClient

# Get logger for this module
logger = get_logger(__name__)

class AIClientFactory:
    """Factory class for creating AI clients"""
    
    # Dictionary mapping client types to their classes
    # These will be imported when needed to avoid circular imports
    _client_types = {}
    
    @classmethod
    def create_client(cls, client_type: str, **kwargs) -> AIClient:
        """
        Create an AI client of the specified type.
        
        Args:
            client_type: Type of client to create ('ollama', 'openai', 'huggingface', 'openrouter')
            **kwargs: Arguments to pass to the client constructor
            
        Returns:
            An instance of the requested AI client
            
        Raises:
            AIClientError: If the client type is not supported
        """
        # Import client classes dynamically when needed
        if not cls._client_types:
            # We import here to avoid circular import issues
            from ai.ollama import OllamaClient
            from ai.openai import OpenAIClient
            from ai.huggingface import HuggingFaceClient
            from ai.openrouter import OpenRouterClient
            
            cls._client_types = {
                'ollama': OllamaClient,
                'openai': OpenAIClient,
                'huggingface': HuggingFaceClient,
                'openrouter': OpenRouterClient
            }
        
        # Normalize client type name
        client_type = client_type.lower()
        
        # Check if client type is supported
        if client_type not in cls._client_types:
            raise AIClientError(f"Unsupported client type: {client_type}")
        
        # Create client instance
        client_class = cls._client_types[client_type]
        return client_class(**kwargs)
    
    @classmethod
    def get_available_client_types(cls) -> List[str]:
        """
        Get a list of available client types.
        
        Returns:
            List of available client type names
        """
        if not cls._client_types:
            # We import here to avoid circular import issues
            from ai.ollama import OllamaClient
            from ai.openai import OpenAIClient
            from ai.huggingface import HuggingFaceClient
            from ai.openrouter import OpenRouterClient
            
            cls._client_types = {
                'ollama': OllamaClient,
                'openai': OpenAIClient,
                'huggingface': HuggingFaceClient,
                'openrouter': OpenRouterClient
            }
            
        return list(cls._client_types.keys())
    
    @classmethod
    def register_client_type(cls, name: str, client_class: Type[AIClient]) -> None:
        """
        Register a new AI client type.
        
        Args:
            name: Name for the client type
            client_class: Client class to register
        """
        if not cls._client_types:
            # We import here to avoid circular import issues
            from ai.ollama import OllamaClient
            from ai.openai import OpenAIClient
            from ai.huggingface import HuggingFaceClient
            from ai.openrouter import OpenRouterClient
            
            cls._client_types = {
                'ollama': OllamaClient,
                'openai': OpenAIClient,
                'huggingface': HuggingFaceClient,
                'openrouter': OpenRouterClient
            }
            
        cls._client_types[name.lower()] = client_class
        logger.info(f"Registered new AI client type: {name}")
    
    @classmethod
    def create_default_client(cls) -> AIClient:
        """
        Create a default AI client based on available API keys and local services.
        
        Returns:
            An instance of the most appropriate AI client
        """
        # Check for API keys
        openai_key = os.environ.get("OPENAI_API_KEY")
        hf_key = os.environ.get("HF_API_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY")
        openrouter_key = os.environ.get("OPENROUTER_API_KEY")
        
        # Try to create a client in order of preference
        
        # 1. First try Ollama (local)
        try:
            from ai.ollama import OllamaClient
            ollama_client = OllamaClient()
            if ollama_client.is_available():
                logger.info("Using Ollama as default AI client")
                return ollama_client
        except Exception as e:
            logger.debug(f"Ollama not available: {str(e)}")
        
        # 2. Next try OpenAI if API key is available
        if openai_key:
            try:
                from ai.openai import OpenAIClient
                openai_client = OpenAIClient(api_key=openai_key)
                if openai_client.is_available():
                    logger.info("Using OpenAI as default AI client")
                    return openai_client
            except Exception as e:
                logger.debug(f"OpenAI not available: {str(e)}")
        
        # 3. Try HuggingFace if API key is available
        if hf_key:
            try:
                from ai.huggingface import HuggingFaceClient
                hf_client = HuggingFaceClient(api_key=hf_key)
                if hf_client.is_available():
                    logger.info("Using HuggingFace as default AI client")
                    return hf_client
            except Exception as e:
                logger.debug(f"HuggingFace not available: {str(e)}")
        
        # 4. Try OpenRouter if API key is available
        if openrouter_key:
            try:
                from ai.openrouter import OpenRouterClient
                openrouter_client = OpenRouterClient(api_key=openrouter_key)
                if openrouter_client.is_available():
                    logger.info("Using OpenRouter as default AI client")
                    return openrouter_client
            except Exception as e:
                logger.debug(f"OpenRouter not available: {str(e)}")
        
        # If all else fails, return Ollama without checking availability
        logger.warning("No AI services available, returning Ollama client but it may not work")
        from ai.ollama import OllamaClient
        return OllamaClient()