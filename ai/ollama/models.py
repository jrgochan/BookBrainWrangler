"""
Data models for the Ollama client
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field

@dataclass
class ModelInfo:
    """Information about an Ollama model"""
    name: str
    size: int = 0  # Size in bytes
    modified_at: str = ""  # ISO timestamp
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Already initialized through field(default_factory=dict)
        pass

@dataclass
class Message:
    """A chat message"""
    role: str  # 'user', 'assistant', or 'system'
    content: str  # The message content
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format for API requests"""
        return {
            "role": self.role,
            "content": self.content
        }

@dataclass
class EmbeddingVector:
    """Vector embedding for a text"""
    values: List[float]
    text: str = ""
    model: str = ""
    
    def __len__(self):
        return len(self.values)
        
    def __getitem__(self, idx):
        return self.values[idx]