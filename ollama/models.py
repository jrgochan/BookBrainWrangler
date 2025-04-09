"""
Data models for the Ollama client
"""

from typing import Dict, List, Any, Optional, TypedDict, Union

# Type definitions for improved code readability and type safety
class ModelInfo(TypedDict, total=False):
    """Information about an Ollama model"""
    name: str
    parameters: int  # Number of parameters, e.g., 7B, 13B
    quantization: str  # Quantization type, e.g., "Q4_0"
    context_length: int  # Maximum context window size
    
class Message(TypedDict):
    """A chat message"""
    role: str  # 'user', 'assistant', or 'system'
    content: str  # The message content

# Response type for embeddings
EmbeddingVector = List[float]