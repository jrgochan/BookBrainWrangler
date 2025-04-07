import requests
import json
import time

class OllamaClient:
    def __init__(self, host="http://localhost:11434"):
        """
        Initialize the Ollama client.
        
        Args:
            host: The Ollama API host
        """
        self.host = host
        self.api_endpoint = f"{host}/api"
    
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
    
    def generate_response(self, prompt, context=None, model="llama2"):
        """
        Generate a response from the Ollama model.
        
        Args:
            prompt: The prompt/question to answer
            context: Optional context to inform the response
            model: The model to use (default: llama2)
            
        Returns:
            The generated response text
        """
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
