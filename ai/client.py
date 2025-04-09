"""
Base AI client for Book Knowledge AI application.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union

from ai.models.common import Message, ModelInfo, EmbeddingVector

class AIClient(ABC):
    """
    Abstract base class for AI clients.
    Provides a common interface for interacting with different AI models.
    """
    
    def __init__(self, model_name: str, **kwargs):
        """
        Initialize the AI client.
        
        Args:
            model_name: Name of the AI model to use
            **kwargs: Additional arguments for the client
        """
        self.model_name = model_name
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the AI service is available.
        
        Returns:
            bool: True if the service is available, False otherwise
        """
        pass
    
    @abstractmethod
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a response from the AI model.
        
        Args:
            prompt: The prompt to send to the model
            **kwargs: Additional arguments for generation
            
        Returns:
            Generated response text
        """
        pass
    
    @abstractmethod
    def generate_chat_response(self, 
                            messages: List[Dict[str, str]], 
                            system_prompt: Optional[str] = None,
                            **kwargs) -> str:
        """
        Generate a response in a chat context.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            system_prompt: Optional system prompt to guide the AI
            **kwargs: Additional arguments for generation
            
        Returns:
            Generated response text
        """
        pass
    
    @abstractmethod
    def list_models(self) -> List[str]:
        """
        List available models.
        
        Returns:
            List of model names
        """
        pass
    
    @abstractmethod
    def get_model_info(self, model_name: Optional[str] = None) -> ModelInfo:
        """
        Get information about a specific model.
        
        Args:
            model_name: Name of the model (defaults to the client's model)
            
        Returns:
            ModelInfo object with model details
        """
        pass
    
    def create_embedding(self, text: str, model: Optional[str] = None) -> EmbeddingVector:
        """
        Create an embedding vector for the given text.
        
        Args:
            text: The text to embed
            model: The model to use for embedding
            
        Returns:
            EmbeddingVector object
        """
        # Default implementation can be overridden by subclasses
        from ai.utils import create_fallback_embedding
        return create_fallback_embedding(text, "default-fallback")