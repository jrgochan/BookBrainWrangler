"""
Ollama AI client module for Book Knowledge AI application.
"""

from ollama.client import OllamaClient
from ollama.models import ModelInfo, Message, EmbeddingVector

__all__ = [
    'OllamaClient',
    'ModelInfo',
    'Message',
    'EmbeddingVector',
]