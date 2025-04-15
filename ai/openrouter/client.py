"""
OpenRouter client implementation for Book Knowledge AI.
OpenRouter provides unified access to multiple AI providers through a single API.
"""

import os
import json
import time
from typing import Dict, List, Any, Optional, Union, Tuple

import requests

from utils.logger import get_logger
from core.exceptions import AIClientError, ModelNotFoundError, ResponseGenerationError
from ai.client import AIClient
from ai.models.common import Message, ModelInfo, EmbeddingVector
from ai.utils import format_context_prompt, create_fallback_embedding, retry_with_exponential_backoff, safe_parse_json

# Get logger for this module
logger = get_logger(__name__)

class OpenRouterClient(AIClient):
    """Client for interacting with the OpenRouter API"""
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model: str = "openai/gpt-3.5-turbo",
                 **kwargs):
        """
        Initialize the OpenRouter client.
        
        Args:
            api_key: OpenRouter API key (falls back to OPENROUTER_API_KEY environment variable)
            model: Default model to use (provider/model format)
            **kwargs: Additional arguments for initialization
        """
        super().__init__(model_name=model)
        
        # Use provided API key or fall back to environment variable
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            logger.warning("No OpenRouter API key provided. Set OPENROUTER_API_KEY environment variable.")
        
        # OpenRouter API URLs
        self.api_base = "https://openrouter.ai/api/v1"
        self.chat_endpoint = f"{self.api_base}/chat/completions"
        self.models_endpoint = f"{self.api_base}/models"
        
        # Default embedding model (OpenRouter doesn't have its own embedding endpoint)
        self.embedding_model = kwargs.get("embedding_model", "openai/text-embedding-3-small")
        
        # Set other client properties
        self.timeout = kwargs.get("timeout", 120)
        
        # App info for OpenRouter headers
        self.app_name = kwargs.get("app_name", "BookKnowledgeAI")
        self.app_version = kwargs.get("app_version", "1.0.0")
        self.app_url = kwargs.get("app_url", None)
        
        logger.info(f"Initialized OpenRouterClient with model={model}")
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for API requests.
        
        Returns:
            Dictionary of headers
        """
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Application info for proper attribution
        headers["HTTP-Referer"] = self.app_url or "https://github.com/bookknowledgeai"
        headers["X-Title"] = self.app_name
        
        return headers
    
    def is_available(self) -> bool:
        """
        Check if the OpenRouter API is available.
        
        Returns:
            bool: True if the API is available, False otherwise
        """
        try:
            # Make a simple request to check if the API is accessible
            response = requests.get(
                self.models_endpoint,
                headers=self._get_headers(),
                timeout=5
            )
            return response.status_code in (200, 401, 403)  # Even auth errors mean API is up
        except Exception as e:
            logger.error(f"Error checking OpenRouter API availability: {str(e)}")
            return False
    
    @retry_with_exponential_backoff
    def list_models(self) -> List[str]:
        """
        List available models from OpenRouter.
        
        Returns:
            List of model names in provider/model format
        """
        try:
            response = requests.get(
                self.models_endpoint,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            models = [model['id'] for model in data.get('data', [])]
            
            return models
        except Exception as e:
            logger.error(f"Error listing OpenRouter models: {str(e)}")
            raise AIClientError(f"Failed to list models: {str(e)}")
    
    def get_model_info(self, model_name: Optional[str] = None) -> ModelInfo:
        """
        Get information about a specific model.
        
        Args:
            model_name: Name of the model in provider/model format (defaults to the client's model)
            
        Returns:
            ModelInfo object with model details
        """
        model = model_name or self.model_name
        
        try:
            response = requests.get(
                self.models_endpoint,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            models = data.get('data', [])
            
            # Find the requested model
            model_data = next((m for m in models if m['id'] == model), None)
            
            if not model_data:
                raise ModelNotFoundError(f"Model '{model}' not found")
            
            # Extract and format provider info
            provider = model.split('/')[0] if '/' in model else "unknown"
            
            return ModelInfo(
                name=model_data['id'],
                provider=provider,
                size=0,  # Not provided
                modified_at="",  # Not provided
                details={
                    "context_length": model_data.get('context_length', 0),
                    "pricing": model_data.get('pricing', {}),
                    "capabilities": model_data.get('capabilities', [])
                }
            )
        except ModelNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting model info for {model}: {str(e)}")
            raise AIClientError(f"Failed to get model info: {str(e)}")
    
    @retry_with_exponential_backoff
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a response from the model.
        
        Args:
            prompt: The prompt to send to the model
            **kwargs: Additional arguments for generation
            
        Returns:
            Generated response text
        """
        if not self.api_key:
            raise AIClientError("OpenRouter API key not set")
            
        model = kwargs.get('model', self.model_name)
        temperature = kwargs.get('temperature', 0.7)
        max_tokens = kwargs.get('max_tokens', 1024)
        
        # Convert to chat format for API
        messages = [{"role": "user", "content": prompt}]
        
        try:
            logger.debug(f"Generating response with model={model}, temp={temperature}")
            
            response = requests.post(
                self.chat_endpoint,
                headers=self._get_headers(),
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **{k: v for k, v in kwargs.items() if k not in ['model', 'temperature', 'max_tokens']}
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            generated_text = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            return generated_text
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise ResponseGenerationError(f"Failed to generate response: {str(e)}")
    
    @retry_with_exponential_backoff
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
        if not self.api_key:
            raise AIClientError("OpenRouter API key not set")
            
        model = kwargs.get('model', self.model_name)
        temperature = kwargs.get('temperature', 0.7)
        max_tokens = kwargs.get('max_tokens', 1024)
        context = kwargs.get('context', '')
        
        try:
            # Prepare messages for the API
            api_messages = []
            
            # Add system prompt if provided
            if system_prompt:
                api_messages.append({"role": "system", "content": system_prompt})
            
            # Format user messages with context if needed
            for msg in messages:
                if context and msg['role'] == 'user':
                    content = format_context_prompt(msg['content'], context)
                    api_messages.append({"role": msg['role'], "content": content})
                    # Only add context to the first user message
                    context = ''
                else:
                    api_messages.append({"role": msg['role'], "content": msg['content']})
            
            logger.debug(f"Generating chat response with model={model}, temp={temperature}")
            
            response = requests.post(
                self.chat_endpoint,
                headers=self._get_headers(),
                json={
                    "model": model,
                    "messages": api_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **{k: v for k, v in kwargs.items() if k not in ['model', 'temperature', 'max_tokens', 'context']}
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            generated_text = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            return generated_text
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            raise ResponseGenerationError(f"Failed to generate chat response: {str(e)}")
    
    def create_embedding(self, text: str, model: Optional[str] = None) -> EmbeddingVector:
        """
        Create an embedding vector for the given text.
        Note: OpenRouter doesn't have a dedicated embedding endpoint,
        this will use OpenAI or a fallback method.
        
        Args:
            text: The text to embed
            model: The model to use for embedding (format: provider/model)
            
        Returns:
            EmbeddingVector object
        """
        logger.warning("OpenRouter doesn't support embeddings directly. Using fallback embedding.")
        return create_fallback_embedding(text, "openrouter-fallback", 1536)