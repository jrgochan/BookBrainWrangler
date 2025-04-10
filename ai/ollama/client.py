"""
Ollama client implementation for Book Knowledge AI.
Ollama provides local execution of various AI models.
"""

import os
import json
import time
import socket
import requests
from typing import Dict, List, Any, Optional, Union, Tuple

from utils.logger import get_logger
from core.exceptions import AIClientError, ModelNotFoundError, ResponseGenerationError
from ai.client import AIClient
from ai.models.common import Message, ModelInfo, EmbeddingVector
from ai.utils import format_context_prompt, create_fallback_embedding, retry_with_exponential_backoff, safe_parse_json

# Get logger for this module
logger = get_logger(__name__)

class OllamaClient(AIClient):
    """Client for interacting with Ollama API"""
    
    DEFAULT_OLLAMA_HOST = "localhost"
    DEFAULT_OLLAMA_PORT = 11434
    
    def __init__(self, 
                 host: Optional[str] = None, 
                 port: Optional[int] = None, 
                 model: str = "llama2",
                 **kwargs):
        """
        Initialize the Ollama client.
        
        Args:
            host: Ollama server host (falls back to OLLAMA_HOST or DEFAULT_OLLAMA_HOST)
            port: Ollama server port (falls back to OLLAMA_PORT or DEFAULT_OLLAMA_PORT)
            model: Default model to use (default: llama2)
            **kwargs: Additional arguments for initialization
        """
        super().__init__(model_name=model)
        
        self.host = host or os.environ.get("OLLAMA_HOST") or self.DEFAULT_OLLAMA_HOST
        self.port = port or int(os.environ.get("OLLAMA_PORT", self.DEFAULT_OLLAMA_PORT))
        
        # Set base URL for API requests
        self.base_url = f"http://{self.host}:{self.port}"
        
        # Other client parameters
        self.timeout = kwargs.get("timeout", 60)
        
        logger.info(f"Initialized OllamaClient with model={model}, host={self.host}, port={self.port}")
        
    def is_server_running(self) -> bool:
        """
        Check if the Ollama server is running.
        
        Returns:
            bool: True if the server is running, False otherwise
        """
        try:
            # Try to connect to the server
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((self.host, self.port))
            s.close()
            return True
        except (socket.error, socket.timeout, ConnectionRefusedError):
            logger.warning(f"Ollama server not running at {self.host}:{self.port}")
            return False
    
    def is_available(self) -> bool:
        """
        Check if the Ollama API is available.
        
        Returns:
            bool: True if the API is available, False otherwise
        """
        if not self.is_server_running():
            return False
            
        try:
            # Make a simple request to check if the API is accessible
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error checking Ollama API availability: {str(e)}")
            return False
    
    @retry_with_exponential_backoff(max_retries=2)
    def list_models(self) -> List[str]:
        """
        List available models from Ollama.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            
            return models
        except Exception as e:
            logger.error(f"Error listing Ollama models: {str(e)}")
            raise AIClientError(f"Failed to list models: {str(e)}")
    
    def get_model_info(self, model_name: Optional[str] = None) -> ModelInfo:
        """
        Get information about a specific model.
        
        Args:
            model_name: Name of the model (defaults to the client's model)
            
        Returns:
            ModelInfo object with model details
        """
        model = model_name or self.model_name
        
        try:
            # Ollama doesn't have a dedicated endpoint for model info
            # We'll get the list of models and find the requested one
            response = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            models = data.get('models', [])
            
            # Find the requested model
            model_data = next((m for m in models if m['name'] == model), None)
            
            if not model_data:
                raise ModelNotFoundError(f"Model '{model}' not found")
            
            # Extract model details
            size = model_data.get('size', 0)
            modified_at = model_data.get('modified_at', '')
            details = {
                'digest': model_data.get('digest', ''),
                'parent_model': model_data.get('parent_model', ''),
                'details': model_data.get('details', {})
            }
            
            return ModelInfo(
                name=model,
                provider="Ollama",
                size=size,
                modified_at=modified_at,
                details=details
            )
        except ModelNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting model info for {model}: {str(e)}")
            raise AIClientError(f"Failed to get model info: {str(e)}")
    
    @retry_with_exponential_backoff(max_retries=2)
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a response from the model.
        
        Args:
            prompt: The prompt to send to the model
            **kwargs: Additional arguments for generation
            
        Returns:
            Generated response text
        """
        model = kwargs.get('model', self.model_name)
        temperature = kwargs.get('temperature', 0.7)
        
        # Prepare the request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        # Add temperature and other parameters if provided
        if temperature is not None:
            payload["temperature"] = temperature
            
        # Add any other parameters
        for k, v in kwargs.items():
            if k not in ['model', 'prompt', 'stream']:
                payload[k] = v
        
        try:
            logger.debug(f"Generating response with model={model}, temp={temperature}")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get('response', '')
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise ResponseGenerationError(f"Failed to generate response: {str(e)}")
    
    @retry_with_exponential_backoff(max_retries=2)
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
        model = kwargs.get('model', self.model_name)
        temperature = kwargs.get('temperature', 0.7)
        context = kwargs.get('context', '')
        
        # Prepare the messages in Ollama's format
        formatted_messages = []
        
        # Add the system prompt if provided
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        
        # Process the conversation messages
        for msg in messages:
            role = msg['role']
            content = msg['content']
            
            # Add context to first user message if provided
            if context and role == 'user' and not any(m['role'] == 'user' for m in formatted_messages):
                content = format_context_prompt(content, context)
            
            formatted_messages.append({"role": role, "content": content})
        
        # Prepare the request payload
        payload = {
            "model": model,
            "messages": formatted_messages,
            "stream": False
        }
        
        # Add temperature and other parameters if provided
        if temperature is not None:
            payload["temperature"] = temperature
            
        # Add any other parameters
        for k, v in kwargs.items():
            if k not in ['model', 'messages', 'stream', 'context']:
                payload[k] = v
        
        try:
            logger.debug(f"Generating chat response with model={model}, temp={temperature}")
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get('message', {}).get('content', '')
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            raise ResponseGenerationError(f"Failed to generate chat response: {str(e)}")
    
    def create_embedding(self, text: str, model: Optional[str] = None) -> EmbeddingVector:
        """
        Create an embedding vector for the given text.
        
        Args:
            text: The text to embed
            model: The model to use for embedding (defaults to the client's model)
            
        Returns:
            EmbeddingVector object
        """
        embedding_model = model or self.model_name
        
        try:
            # Prepare the request payload
            payload = {
                "model": embedding_model,
                "prompt": text
            }
            
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            embedding = data.get('embedding', [])
            
            return EmbeddingVector(values=embedding, text=text, model=embedding_model)
        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}. Using fallback.")
            return create_fallback_embedding(text, f"ollama-{embedding_model}")
