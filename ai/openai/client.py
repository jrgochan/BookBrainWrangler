"""
OpenAI client implementation for Book Knowledge AI.
"""

import os
import json
import time
from typing import Dict, List, Any, Optional, Union, Tuple

try:
    import openai
    from openai import OpenAI
    from openai.types.not_found_error import NotFoundError as OpenAINotFoundError
    OPENAI_AVAILABLE = True
except ImportError:
    # Define placeholder for type checking
    class OpenAI:
        def __init__(self, **kwargs):
            pass
        
        class models:
            @staticmethod
            def list(**kwargs):
                return []
                
            @staticmethod
            def retrieve(model_id):
                return None
        
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    return None
        
        class embeddings:
            @staticmethod
            def create(**kwargs):
                return None
    
    class OpenAINotFoundError(Exception):
        pass
    
    OPENAI_AVAILABLE = False

from utils.logger import get_logger
from core.exceptions import AIClientError, ModelNotFoundError, ResponseGenerationError
from ai.client import AIClient
from ai.models.common import Message, ModelInfo, EmbeddingVector
from ai.utils import format_context_prompt, create_fallback_embedding, retry_with_exponential_backoff

# Get logger for this module
logger = get_logger(__name__)

class OpenAIClient(AIClient):
    """Client for interacting with the OpenAI API"""
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model: str = "gpt-3.5-turbo",
                 organization: Optional[str] = None,
                 **kwargs):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key: OpenAI API key (falls back to OPENAI_API_KEY environment variable)
            model: Default model to use
            organization: OpenAI organization ID (optional)
            **kwargs: Additional arguments for initialization
        """
        super().__init__(model_name=model)
        
        # Use provided API key or fall back to environment variable
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("No OpenAI API key provided. Set OPENAI_API_KEY environment variable.")
            
        # Set up the OpenAI client
        self.client = OpenAI(
            api_key=self.api_key,
            organization=organization
        )
        
        # Set model defaults
        self.embedding_model = kwargs.get("embedding_model", "text-embedding-3-small")
        
        logger.info(f"Initialized OpenAIClient with model={model}")
    
    def is_available(self) -> bool:
        """
        Check if the OpenAI API is available.
        
        Returns:
            bool: True if the API is available, False otherwise
        """
        if not self.api_key:
            return False
            
        try:
            # Make a simple request to check if the API is accessible
            models = self.client.models.list(limit=1)
            return True
        except Exception as e:
            logger.error(f"Error checking OpenAI API availability: {str(e)}")
            return False
    
    @retry_with_exponential_backoff
    def list_models(self) -> List[str]:
        """
        List available models from OpenAI.
        
        Returns:
            List of model names
        """
        if not self.api_key:
            raise AIClientError("OpenAI API key not set")
        
        try:
            models_list = self.client.models.list()
            return [model.id for model in models_list.data]
        except Exception as e:
            logger.error(f"Error listing OpenAI models: {str(e)}")
            raise AIClientError(f"Failed to list models: {str(e)}")
    
    def get_model_info(self, model_name: Optional[str] = None) -> ModelInfo:
        """
        Get information about a specific model.
        
        Args:
            model_name: Name of the model (defaults to the client's model)
            
        Returns:
            ModelInfo object with model details
        """
        if not self.api_key:
            raise AIClientError("OpenAI API key not set")
            
        model = model_name or self.model_name
        
        try:
            model_data = self.client.models.retrieve(model)
            
            # Extract relevant information
            return ModelInfo(
                name=model_data.id,
                provider="OpenAI",
                size=0,  # Not provided by API
                modified_at="",  # Not provided by API
                details={"owned_by": model_data.owned_by}
            )
        except OpenAINotFoundError:
            raise ModelNotFoundError(f"Model '{model}' not found")
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
            raise AIClientError("OpenAI API key not set")
            
        model = kwargs.get('model', self.model_name)
        temperature = kwargs.get('temperature', 0.7)
        max_tokens = kwargs.get('max_tokens', 1024)
        top_p = kwargs.get('top_p', 1.0)
        
        # Convert to chat format for API consistency
        messages = [{"role": "user", "content": prompt}]
        
        try:
            logger.debug(f"Generating response with model={model}, temp={temperature}")
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                n=1
            )
            
            # Extract response text
            generated_text = response.choices[0].message.content
            
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
            raise AIClientError("OpenAI API key not set")
            
        model = kwargs.get('model', self.model_name)
        temperature = kwargs.get('temperature', 0.7)
        max_tokens = kwargs.get('max_tokens', 1024)
        top_p = kwargs.get('top_p', 1.0)
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
            response = self.client.chat.completions.create(
                model=model,
                messages=api_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                n=1
            )
            
            # Extract response text
            generated_text = response.choices[0].message.content
            
            return generated_text
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            raise ResponseGenerationError(f"Failed to generate chat response: {str(e)}")
    
    @retry_with_exponential_backoff
    def create_embedding(self, text: str, model: Optional[str] = None) -> EmbeddingVector:
        """
        Create an embedding vector for the given text.
        
        Args:
            text: The text to embed
            model: The model to use for embedding (defaults to the client's embedding model)
            
        Returns:
            EmbeddingVector object
        """
        if not self.api_key:
            logger.warning("OpenAI API key not set, using fallback embedding")
            return create_fallback_embedding(text, "openai-fallback")
            
        embedding_model = model or self.embedding_model
        
        try:
            response = self.client.embeddings.create(
                input=text,
                model=embedding_model
            )
            
            # Extract the embedding
            embedding = response.data[0].embedding
            
            return EmbeddingVector(values=embedding, text=text, model=embedding_model)
        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}. Using fallback.")
            return create_fallback_embedding(text, f"openai-{embedding_model}")