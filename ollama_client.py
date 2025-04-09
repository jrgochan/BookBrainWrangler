"""
Ollama Client for handling AI model interactions.
This client communicates with the Ollama API to perform operations like:
- Checking server status
- Listing available models
- Generating text responses
- Generating chat completions
- Creating embeddings
"""

import json
import logging
import requests
import time
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, server_url="http://localhost:11434", model="llama2", timeout=300):
        """
        Initialize the Ollama client.
        
        Args:
            server_url: URL of the Ollama server
            model: Default model to use for queries
            timeout: Default timeout for API requests in seconds (default: 5 minutes)
        """
        self.server_url = server_url
        self.model = model
        self.api_base = f"{server_url}/api"
        self.timeout = timeout  # Store timeout as instance variable (5 minutes by default)
        # Added for compatibility with chat_with_ai.py
        self.host = server_url
        logger.info(f"Initialized OllamaClient with server_url={server_url}, model={model}")
    
    def is_server_running(self) -> bool:
        """
        Check if the Ollama server is running.
        
        Returns:
            bool: True if the server is running, False otherwise
        """
        try:
            logger.debug(f"Checking Ollama server at {self.api_base}/tags")
            response = requests.get(f"{self.api_base}/tags", timeout=3)
            result = response.status_code == 200
            logger.debug(f"Ollama server check result: {result}")
            return result
        except Exception as e:
            logger.warning(f"Failed to connect to Ollama server: {str(e)}")
            return False
            
    def check_connection(self) -> bool:
        """
        Check if the Ollama server is running. Alias for is_server_running for compatibility.
        
        Returns:
            bool: True if the server is running, False otherwise
        """
        return self.is_server_running()
        
    def get_model_details(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get details about a specific model.
        
        Args:
            model_name: Name of the model to get details for
            
        Returns:
            dict: Dictionary with model details or None if not found
        """
        try:
            logger.debug(f"Getting details for model {model_name}")
            response = requests.get(f"{self.api_base}/show", params={"name": model_name}, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract relevant details from the response
                parameters = data.get("parameters", {})
                parameter_size = parameters.get("num_ctx", 0)
                
                model_details = {
                    "name": model_name,
                    "parameters": data.get("parameter_size", 7000000000),  # Default to 7B if unknown
                    "quantization": data.get("quantization_level", "unknown"),
                    "context_length": parameter_size
                }
                logger.debug(f"Retrieved model details: {model_details}")
                return model_details
            else:
                # If we can't get details, return basic info
                logger.warning(f"Failed to get model details, status code: {response.status_code}")
                return {
                    "name": model_name,
                    "parameters": 7000000000,  # 7B default
                    "quantization": "unknown"
                }
        except Exception as e:
            logger.error(f"Error getting model details: {str(e)}")
            return None
            
    def list_models(self) -> List[Dict[str, str]]:
        """
        List all available models in a format suitable for UI display.
        
        Returns:
            list: List of model dictionaries with name and other details
        """
        model_names = self.get_available_models()
        return [{"name": name} for name in model_names] if model_names else [{"name": "llama2"}]
    
    def get_available_models(self) -> List[str]:
        """
        Get a list of available models.
        
        Returns:
            list: List of model names
        """
        try:
            logger.debug(f"Getting available models from {self.api_base}/tags")
            response = requests.get(f"{self.api_base}/tags", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                logger.debug(f"Retrieved {len(models)} models")
                return models
            else:
                logger.warning(f"Failed to get models, status code: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return []
    
    def generate_response(self, prompt: str, context: Optional[str] = None, 
                         temperature: float = 0.7, max_tokens: int = 1000, 
                         model: Optional[str] = None) -> str:
        """
        Generate a response from the model using the Ollama /generate endpoint.
        
        Args:
            prompt: The prompt to send to the model
            context: Optional context from previous exchanges
            temperature: Sampling temperature (higher = more creative)
            max_tokens: Maximum tokens to generate in the response
            model: Model to use (if None, uses the default model)
            
        Returns:
            str: The generated response
        """
        model_to_use = model or self.model
        
        # First, check if Ollama server is running
        if not self.is_server_running():
            # Provide a fallback response when server is not available
            logger.warning("Ollama server is not available for generate_response request")
            return "Sorry, the Ollama AI server is not available right now. Please check your Ollama installation and configuration in the Settings tab."
        
        try:
            # Prepare the request payload
            payload = {
                "model": model_to_use,
                "prompt": prompt,
                "temperature": temperature,
                "num_predict": max_tokens,
            }
            
            # If context is provided, include it in the prompt
            if context:
                # Format the context to be part of the prompt
                context_prompt = (
                    "Here is some information that may be relevant to the user's question:\n\n"
                    f"{context}\n\n"
                    "Now please respond to the user's question based on this information:\n\n"
                    f"{prompt}"
                )
                payload["prompt"] = context_prompt
            
            logger.debug(f"Sending generate request to {self.api_base}/generate with model {model_to_use}")
            try:
                response = requests.post(f"{self.api_base}/generate", json=payload, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    generated_text = data.get("response", "")
                    logger.debug(f"Generated {len(generated_text)} chars of text")
                    return generated_text
                else:
                    error_message = f"Error from Ollama API: Status code {response.status_code}"
                    try:
                        error_data = response.json()
                        if "error" in error_data:
                            error_message += f" - {error_data['error']}"
                    except:
                        pass
                    
                    logger.error(error_message)
                    return f"Error: {error_message}"
            except requests.exceptions.RequestException as req_err:
                logger.error(f"Request error: {str(req_err)}")
                return f"Sorry, there was a problem connecting to the Ollama server: {str(req_err)}"
                
        except Exception as e:
            error_message = f"Failed to generate response: {str(e)}"
            logger.error(error_message)
            return f"Sorry, an unexpected error occurred: {str(e)}"
    
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7, 
            max_tokens: int = 1000, model: Optional[str] = None) -> Dict[str, str]:
        """
        Generate a chat response from the model using the Ollama /chat endpoint.
        
        Args:
            messages: List of message dictionaries [{"role": "user", "content": "..."}]
            temperature: Sampling temperature (higher = more creative)
            max_tokens: Maximum tokens to generate in the response
            model: Model to use (if None, uses the default model)
            
        Returns:
            dict: The chat response {"role": "assistant", "content": "..."}
        """
        model_to_use = model or self.model
        
        # Validate that we have at least one message
        if not messages:
            logger.warning("No messages provided to chat method")
            return {"role": "assistant", "content": "I didn't receive any messages to respond to."}
        
        # First, check if Ollama server is running
        if not self.is_server_running():
            # Provide a fallback response when server is not available
            logger.warning("Ollama server is not available for chat request")
            return {"role": "assistant", "content": "Sorry, the Ollama AI server is not available right now. Please check your Ollama installation and configuration in the Settings tab."}
        
        try:
            # Prepare the request payload
            payload = {
                "model": model_to_use,
                "messages": messages,
                "temperature": temperature,
                "num_predict": max_tokens,
            }
            
            logger.debug(f"Sending chat request to {self.api_base}/chat with model {model_to_use}")
            try:
                response = requests.post(f"{self.api_base}/chat", json=payload, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    message = data.get("message", {})
                    logger.debug(f"Received chat response with content length: {len(message.get('content', ''))}")
                    return message
                else:
                    error_message = f"Error from Ollama API: Status code {response.status_code}"
                    try:
                        error_data = response.json()
                        if "error" in error_data:
                            error_message += f" - {error_data['error']}"
                    except:
                        pass
                    
                    logger.error(error_message)
                    return {"role": "assistant", "content": f"Error: {error_message}"}
            except requests.exceptions.RequestException as req_err:
                logger.error(f"Request error in chat method: {str(req_err)}")
                return {"role": "assistant", "content": f"Sorry, there was a problem connecting to the Ollama server: {str(req_err)}"}
                
        except Exception as e:
            error_message = f"Failed to generate chat response: {str(e)}"
            logger.error(error_message)
            return {"role": "assistant", "content": f"Sorry, an unexpected error occurred: {str(e)}"}
    
    def generate_embeddings(self, text: str, model: Optional[str] = None) -> List[float]:
        """
        Generate embeddings for text using the Ollama /embeddings endpoint.
        
        Args:
            text: The text to embed
            model: Model to use for embeddings (if None, uses the default model)
            
        Returns:
            list: Vector embedding as a list of floats
        """
        model_to_use = model or self.model
        
        # First, check if Ollama server is running
        if not self.is_server_running():
            logger.warning("Ollama server is not available for embeddings request, using fallback")
            # Create a simple fallback embedding - we need to import numpy here
            try:
                import numpy as np
                fallback_embedding = list(np.zeros(384).astype(float))
                return fallback_embedding
            except ImportError:
                logger.error("Failed to import numpy for fallback embedding")
                # Super simple fallback if numpy is not available
                return [0.0] * 384
        
        try:
            # Prepare the request payload
            payload = {
                "model": model_to_use,
                "prompt": text,
            }
            
            logger.debug(f"Sending embeddings request for text of length {len(text)}")
            try:
                response = requests.post(f"{self.api_base}/embeddings", json=payload, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    embedding = data.get("embedding", [])
                    logger.debug(f"Generated embedding with {len(embedding)} dimensions")
                    return embedding
                else:
                    logger.error(f"Error generating embedding: Status code {response.status_code}")
                    # Create a zero embedding as fallback
                    try:
                        import numpy as np
                        fallback_embedding = list(np.zeros(384).astype(float))
                        return fallback_embedding
                    except ImportError:
                        logger.error("Failed to import numpy for fallback embedding")
                        # Super simple fallback if numpy is not available
                        return [0.0] * 384
            except requests.exceptions.RequestException as req_err:
                logger.error(f"Request error in embeddings method: {str(req_err)}")
                # Create a zero embedding as fallback
                try:
                    import numpy as np
                    fallback_embedding = list(np.zeros(384).astype(float))
                    return fallback_embedding
                except ImportError:
                    logger.error("Failed to import numpy for fallback embedding")
                    # Super simple fallback if numpy is not available
                    return [0.0] * 384
                
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            # Create a zero embedding as fallback
            try:
                import numpy as np
                fallback_embedding = list(np.zeros(384).astype(float))
                return fallback_embedding
            except ImportError:
                logger.error("Failed to import numpy for fallback embedding")
                # Super simple fallback if numpy is not available
                return [0.0] * 384