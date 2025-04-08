"""
Ollama Client for handling AI model interactions.
"""

import json
import requests
import time
from typing import Dict, List, Any, Optional

class OllamaClient:
    def __init__(self, server_url="http://localhost:11434", model="llama2"):
        """
        Initialize the Ollama client.
        
        Args:
            server_url: URL of the Ollama server
            model: Default model to use for queries
        """
        self.server_url = server_url
        self.model = model
        self.api_base = f"{server_url}/api"
        # Added for compatibility with chat_with_ai.py
        self.host = server_url
    
    def is_server_running(self):
        """
        Check if the Ollama server is running.
        
        Returns:
            bool: True if the server is running, False otherwise
        """
        try:
            response = requests.get(f"{self.api_base}/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
            
    def check_connection(self):
        """
        Check if the Ollama server is running. Alias for is_server_running for compatibility.
        
        Returns:
            bool: True if the server is running, False otherwise
        """
        return self.is_server_running()
        
    def get_model_details(self, model_name):
        """
        Get details about a specific model.
        
        Args:
            model_name: Name of the model to get details for
            
        Returns:
            dict: Dictionary with model details or None if not found
        """
        try:
            # For now, just return a basic info dictionary
            return {
                "name": model_name,
                "parameters": 7000000000,  # 7B
                "quantization": "Q4_0"
            }
        except:
            return None
            
    def list_models(self):
        """
        List all available models. Alias for get_available_models with different return format.
        
        Returns:
            list: List of model dictionaries with name and other details
        """
        model_names = self.get_available_models()
        return [{"name": name} for name in model_names or ["llama2"]]
    
    def get_available_models(self):
        """
        Get a list of available models.
        
        Returns:
            list: List of model names
        """
        try:
            response = requests.get(f"{self.api_base}/tags")
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except:
            return []
    
    def generate_response(self, prompt, context=None, temperature=0.7, max_tokens=1000, model=None):
        """
        Generate a response from the model.
        
        Args:
            prompt: The prompt to send to the model
            context: Optional context from previous exchanges
            temperature: Sampling temperature (higher = more creative)
            max_tokens: Maximum tokens to generate in the response
            model: Model to use (if None, uses the default model)
            
        Returns:
            str: The generated response
        """
        # This is a placeholder implementation
        # In a real implementation, this would connect to an actual Ollama server
        
        # Use specified model or default
        model_to_use = model or self.model
        
        # Simulate a delay to mimic the model generating a response
        time.sleep(1)
        
        # Include context if provided
        if context:
            response = f"Based on the information from your books: {context[:100]}...\n\n"
            response += f"This is a placeholder response from {model_to_use} to your query: '{prompt}'"
            return response
        
        # Return a placeholder response
        return f"This is a placeholder response from {model_to_use} to your query: '{prompt}'"
    
    def chat(self, messages, temperature=0.7, max_tokens=1000):
        """
        Generate a chat response from the model.
        
        Args:
            messages: List of message dictionaries [{"role": "user", "content": "..."}]
            temperature: Sampling temperature (higher = more creative)
            max_tokens: Maximum tokens to generate in the response
            
        Returns:
            dict: The chat response {"role": "assistant", "content": "..."}
        """
        # This is a placeholder implementation
        # In a real implementation, this would connect to an actual Ollama server
        
        # Get the last user message
        last_message = next((m for m in reversed(messages) if m['role'] == 'user'), None)
        if not last_message:
            return {"role": "assistant", "content": "I didn't receive a valid message to respond to."}
        
        # Simulate a delay to mimic the model generating a response
        time.sleep(1.5)
        
        # Return a placeholder response
        return {
            "role": "assistant",
            "content": f"This is a placeholder response to your message: '{last_message['content']}'"
        }
    
    def generate_embeddings(self, text):
        """
        Generate embeddings for text.
        
        Args:
            text: The text to embed
            
        Returns:
            list: Vector embedding
        """
        # This is a placeholder implementation
        # In a real implementation, this would connect to an actual Ollama server
        
        # Return a placeholder embedding (just a list of random values)
        # A real embedding would be a list of float values
        import random
        return [random.random() for _ in range(384)]