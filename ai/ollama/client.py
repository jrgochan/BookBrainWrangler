"""
Ollama client implementation for Book Knowledge AI.
"""

import json
import requests
import time
from typing import Dict, List, Any, Optional, Union

from utils.logger import get_logger
from core.exceptions import AIClientError
from ai.client import AIClient
from ai.ollama.models import ModelInfo, Message, EmbeddingVector
from ai.ollama.utils import safe_parse_json, create_fallback_embedding, format_context_prompt

# Get logger for this module
logger = get_logger(__name__)

class OllamaClient(AIClient):
    """Client for interacting with the Ollama API"""
    
    def __init__(self, server_url="http://localhost:11434", model="llama2:7b", timeout=300):
        """
        Initialize the Ollama client.
        
        Args:
            server_url: URL of the Ollama server
            model: Default model to use for queries
            timeout: Default timeout for API requests in seconds (default: 5 minutes)
        """
        super().__init__(model_name=model)
        self.server_url = server_url
        self.api_base = f"{server_url}/api"
        self.timeout = timeout 
        self.host = server_url  # Added for compatibility with existing code
        logger.info(f"Initialized OllamaClient with server_url={server_url}, model={model}")
    
    def is_server_running(self) -> bool:
        """
        Check if the Ollama server is running.
        
        Returns:
            bool: True if the server is running, False otherwise
        """
        try:
            logger.debug(f"Checking Ollama server at {self.api_base}/tags")
            response = requests.get(f"{self.api_base}/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error checking Ollama server status: {str(e)}")
            return False
    
    def list_models(self) -> List[str]:
        """
        List available models from the Ollama server.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.api_base}/tags", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            
            return models
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
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
            response = requests.post(
                f"{self.api_base}/show",
                json={"name": model},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            return ModelInfo(
                name=data.get('name', ''),
                size=data.get('size', 0),
                modified_at=data.get('modified_at', ''),
                details=data
            )
        except Exception as e:
            logger.error(f"Error getting model info for {model}: {str(e)}")
            raise AIClientError(f"Failed to get model info: {str(e)}")
    
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
        max_tokens = kwargs.get('max_tokens', 2048)
        
        try:
            logger.debug(f"Generating response with model={model}, temp={temperature}")
            response = requests.post(
                f"{self.api_base}/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **{k: v for k, v in kwargs.items() if k not in ['model', 'temperature', 'max_tokens']}
                },
                timeout=self.timeout,
                stream=False
            )
            response.raise_for_status()
            
            data = response.json()
            generated_text = data.get('response', '')
            
            return generated_text
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise AIClientError(f"Failed to generate response: {str(e)}")
    
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
        
        try:
            formatted_messages = [
                Message(role=msg['role'], content=msg['content'])
                for msg in messages
            ]
            
            # Add context to the first user message if provided
            if context and formatted_messages:
                for i, msg in enumerate(formatted_messages):
                    if msg.role == 'user':
                        formatted_messages[i].content = format_context_prompt(msg.content, context)
                        break
            
            request_data = {
                "model": model,
                "messages": [msg.to_dict() for msg in formatted_messages],
                "temperature": temperature,
                **{k: v for k, v in kwargs.items() if k not in ['model', 'temperature', 'context']}
            }
            
            if system_prompt:
                request_data["system"] = system_prompt
            
            logger.debug(f"Generating chat response with model={model}, temp={temperature}")
            response = requests.post(
                f"{self.api_base}/chat",
                json=request_data,
                timeout=self.timeout,
                stream=False
            )
            response.raise_for_status()
            
            data = response.json()
            generated_text = data.get('message', {}).get('content', '')
            
            return generated_text
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            raise AIClientError(f"Failed to generate chat response: {str(e)}")
    
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
            response = requests.post(
                f"{self.api_base}/embeddings",
                json={
                    "model": embedding_model,
                    "prompt": text
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                embedding = data.get('embedding', [])
                return EmbeddingVector(values=embedding, text=text, model=embedding_model)
            else:
                logger.warning(f"Failed to create embedding, status: {response.status_code}. Using fallback.")
                return create_fallback_embedding(text, embedding_model)
                
        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}. Using fallback.")
            return create_fallback_embedding(text, embedding_model)