"""
Base AI client for Book Knowledge AI application.
"""

from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod

from core.exceptions import AIClientError
from utils.logger import get_logger

# Get a logger for this module
logger = get_logger(__name__)

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
        self.logger = logger
        
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