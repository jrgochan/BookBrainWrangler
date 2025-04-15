"""
HuggingFace client implementation for Book Knowledge AI.
"""

import os
import json
import time
from typing import Dict, List, Any, Optional, Union, Tuple

import requests

try:
    from huggingface_hub import InferenceClient, HfApi
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    # Define placeholder for type checking
    class InferenceClient:
        def __init__(self, **kwargs):
            pass
            
        def text_generation(self, prompt, **kwargs):
            return ""
            
        def feature_extraction(self, text, **kwargs):
            return []
    
    class HfApi:
        def __init__(self, **kwargs):
            pass
            
        def list_featured_models(self, **kwargs):
            return []
            
        def model_info(self, model_id):
            return None
    
    HUGGINGFACE_AVAILABLE = False

from utils.logger import get_logger
from core.exceptions import AIClientError, ModelNotFoundError, ResponseGenerationError
from ai.client import AIClient
from ai.models.common import Message, ModelInfo, EmbeddingVector
from ai.utils import format_context_prompt, create_fallback_embedding, retry_with_exponential_backoff, safe_parse_json

# Get logger for this module
logger = get_logger(__name__)

class HuggingFaceClient(AIClient):
    """Client for interacting with the HuggingFace Inference API"""
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model: str = "mistralai/Mistral-7B-Instruct-v0.1",
                 **kwargs):
        """
        Initialize the HuggingFace client.
        
        Args:
            api_key: HuggingFace API token (falls back to HF_API_TOKEN/HUGGINGFACE_API_KEY env var)
            model: Default model to use
            **kwargs: Additional arguments for initialization
        """
        super().__init__(model_name=model)
        
        # Use provided API key or fall back to environment variables
        self.api_key = api_key or os.environ.get("HF_API_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY")
        if not self.api_key:
            logger.warning("No HuggingFace API token provided. Set HF_API_TOKEN environment variable.")
        
        # Set up the HuggingFace client
        self.inference_client = InferenceClient(token=self.api_key)
        self.hf_api = HfApi(token=self.api_key)
        
        # Set model defaults for embeddings
        self.embedding_model = kwargs.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
        
        # Base URL for API requests
        self.api_base_url = "https://api-inference.huggingface.co/models"
        
        logger.info(f"Initialized HuggingFaceClient with model={model}")
    
    def is_available(self) -> bool:
        """
        Check if the HuggingFace API is available.
        
        Returns:
            bool: True if the API is available, False otherwise
        """
        try:
            # Make a simple request to check if the API is accessible
            response = requests.get(
                f"{self.api_base_url}/{self.embedding_model}",
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            )
            return response.status_code in (200, 401, 403)  # Even auth errors mean API is up
        except Exception as e:
            logger.error(f"Error checking HuggingFace API availability: {str(e)}")
            return False
    
    def list_models(self) -> List[str]:
        """
        List available models from HuggingFace Hub.
        Note: This returns featured models due to the large number of models on HF.
        
        Returns:
            List of model names
        """
        try:
            # Get featured models (limited set with good quality)
            featured_models = self.hf_api.list_featured_models(
                limit=50,
                filter="text-generation"
            )
            
            return [model.id for model in featured_models]
        except Exception as e:
            logger.error(f"Error listing HuggingFace models: {str(e)}")
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
            # Get model info from Hub
            model_info = self.hf_api.model_info(model)
            
            # Extract relevant information
            return ModelInfo(
                name=model,
                provider="HuggingFace",
                size=0,  # Not easily available
                modified_at=str(model_info.last_modified),
                details={
                    "author": model_info.author,
                    "tags": model_info.tags,
                    "pipeline_tag": model_info.pipeline_tag
                }
            )
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
        model = kwargs.get('model', self.model_name)
        temperature = kwargs.get('temperature', 0.7)
        max_tokens = kwargs.get('max_tokens', 1024)
        
        # Prepare generation parameters
        params = {
            "temperature": temperature,
            "max_new_tokens": max_tokens,
            "return_full_text": False
        }
        
        # Add any additional parameters
        for k, v in kwargs.items():
            if k not in ['model', 'temperature', 'max_tokens']:
                params[k] = v
        
        try:
            logger.debug(f"Generating response with model={model}, temp={temperature}")
            
            response = self.inference_client.text_generation(
                prompt,
                model=model,
                **params
            )
            
            return response
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
        model = kwargs.get('model', self.model_name)
        temperature = kwargs.get('temperature', 0.7)
        max_tokens = kwargs.get('max_tokens', 1024)
        context = kwargs.get('context', '')
        
        try:
            # Format the chat messages for HuggingFace models
            # Different models expect different formats, we'll use a common format
            # and let the HF API handle it
            formatted_prompt = ""
            
            # Add system prompt if provided
            if system_prompt:
                formatted_prompt += f"<|system|>\n{system_prompt}\n\n"
            
            # Format conversation
            for msg in messages:
                role = msg['role']
                content = msg['content']
                
                # Add context to first user message if provided
                if context and role == 'user' and not formatted_prompt.count("<|user|>") > 0:
                    content = format_context_prompt(content, context)
                
                # Map roles
                if role == 'user':
                    formatted_prompt += f"<|user|>\n{content}\n\n"
                elif role == 'assistant':
                    formatted_prompt += f"<|assistant|>\n{content}\n\n"
                else:
                    # Skip system message if already handled above
                    if role != 'system':
                        formatted_prompt += f"<|{role}|>\n{content}\n\n"
            
            # Add final assistant prompt
            formatted_prompt += "<|assistant|>\n"
            
            # Generate response
            logger.debug(f"Generating chat response with model={model}, temp={temperature}")
            
            response = self.inference_client.text_generation(
                formatted_prompt,
                model=model,
                temperature=temperature,
                max_new_tokens=max_tokens,
                return_full_text=False
            )
            
            return response.strip()
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
        embedding_model = model or self.embedding_model
        
        try:
            # HuggingFace feature-extraction task
            response = self.inference_client.feature_extraction(
                text,
                model=embedding_model
            )
            
            # Flatten if needed (some models return 2D arrays)
            if isinstance(response[0], list):
                # Take mean across sequence length
                import numpy as np
                embedding = np.mean(response, axis=0).tolist()
            else:
                embedding = response
            
            return EmbeddingVector(values=embedding, text=text, model=embedding_model)
        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}. Using fallback.")
            return create_fallback_embedding(text, f"hf-{embedding_model}")