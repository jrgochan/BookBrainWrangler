import requests
import json
import time
import os

class OllamaClient:
    def __init__(self, host=None, model=None):
        """
        Initialize the Ollama client.
        
        Args:
            host: The Ollama API host (default: uses environment variable or "http://localhost:11434")
            model: The default model to use (default: uses environment variable or "llama2")
        """
        # Get host from env var or use default
        self.host = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.api_endpoint = f"{self.host}/api"
        
        # Get default model from env var or use default
        self.default_model = model or os.environ.get("OLLAMA_MODEL", "llama2")
    
    def list_models(self):
        """
        List available models from the Ollama server.
        
        Returns:
            List of model information dictionaries
        """
        try:
            response = requests.get(f"{self.api_endpoint}/tags")
            if response.status_code == 200:
                return response.json().get("models", [])
            else:
                print(f"Error listing models: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Error connecting to Ollama server: {e}")
            return []
    
    def generate_response(self, prompt, context=None, model=None):
        """
        Generate a response from the Ollama model.
        
        Args:
            prompt: The prompt/question to answer
            context: Optional context to inform the response
            model: The model to use (defaults to self.default_model)
            
        Returns:
            The generated response text
        """
        # Use the provided model or fall back to default
        model = model or self.default_model
        try:
            # Prepare the prompt with context if provided
            system_prompt = "You are a helpful AI assistant with knowledge from various books."
            
            if context:
                system_prompt += " Use the following information from books to inform your answer, but respond in a conversational manner without directly quoting the context unless explicitly asked."
                full_prompt = f"{prompt}\n\nRelevant information from books:\n{context}"
            else:
                full_prompt = prompt
            
            # Prepare the request payload
            payload = {
                "model": model,
                "prompt": full_prompt,
                "system": system_prompt,
                "stream": False  # We want the complete response at once
            }
            
            # Send the request
            response = requests.post(f"{self.api_endpoint}/generate", json=payload)
            
            if response.status_code == 200:
                return response.json().get("response", "I couldn't generate a response.")
            else:
                print(f"Error generating response: {response.status_code} - {response.text}")
                return "Error: Failed to get a response from the AI model."
                
        except Exception as e:
            print(f"Error connecting to Ollama server: {e}")
            return "Error: Could not connect to the AI service. Make sure Ollama is running."
    
    def check_connection(self):
        """
        Check if the Ollama server is reachable.
        
        Returns:
            Boolean indicating if the server is reachable
        """
        try:
            response = requests.get(f"{self.api_endpoint}/tags")
            return response.status_code == 200
        except:
            return False
            
    def update_settings(self, host=None, model=None):
        """
        Update client settings.
        
        Args:
            host: New Ollama API host URL
            model: New default model
            
        Returns:
            Boolean indicating success of update and connecting to new host
        """
        # Update host if provided
        if host and host != self.host:
            old_host = self.host
            self.host = host
            self.api_endpoint = f"{host}/api"
            
            # Test connection to new host
            if not self.check_connection():
                # Revert if can't connect
                self.host = old_host
                self.api_endpoint = f"{old_host}/api"
                return False
        
        # Update default model if provided
        if model:
            self.default_model = model
            
        return True
        
    def get_model_details(self, model_name):
        """
        Get details about a specific model.
        
        Args:
            model_name: The name of the model to query
            
        Returns:
            Dictionary containing model details or None if not found
        """
        try:
            response = requests.get(f"{self.api_endpoint}/show", params={"name": model_name})
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting model details: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error connecting to Ollama server: {e}")
            return None
