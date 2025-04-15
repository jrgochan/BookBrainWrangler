"""
Test configuration for Ollama tests
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class TestConfig:
    """Configuration for Ollama tests"""
    
    # Server configuration
    host: Optional[str] = None
    port: Optional[int] = None
    model: str = "llama2:7b"
    timeout: int = 60
    
    # Test selection
    test: str = "all"
    
    # Server wait settings
    wait_for_server: bool = False
    wait_timeout: int = 60
    
    # Output settings
    verbose: bool = False
    
    # Test data
    sample_prompt: str = "Explain what a vector database is in one paragraph."
    sample_system_prompt: str = "You are a helpful AI assistant that provides concise answers."
    sample_messages = [
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "assistant", "content": "The capital of France is Paris."},
        {"role": "user", "content": "What about Germany?"}
    ]
    
    # Ollama v0.6.4+ specific settings
    vision_model: Optional[str] = None  # Specific model to test vision capabilities with
    available_models: List[str] = field(default_factory=list)  # List of models available on the server
