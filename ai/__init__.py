"""
AI module for Book Knowledge AI application.
Contains AI clients and utility functions for interacting with AI models.
"""

from ai.client import AIClient
from ai.ollama import OllamaClient

__all__ = [
    'AIClient',
    'OllamaClient',
]