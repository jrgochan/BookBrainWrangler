"""
Common model classes for AI clients in Book Knowledge AI.
This module provides shared data structures used by all AI client implementations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union, Literal
import numpy as np
from datetime import datetime

@dataclass
class Message:
    """
    A message in a chat conversation.
    """
    role: Literal["system", "user", "assistant", "function"]
    content: str
    name: Optional[str] = None  # For function messages
    function_call: Optional[Dict[str, Any]] = None  # For function calls

@dataclass
class ModelInfo:
    """
    Information about an AI model.
    """
    id: str
    name: str
    provider: str
    description: str = ""
    size: Optional[int] = None  # Size in parameters or tokens
    modified_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    owned_by: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EmbeddingVector:
    """
    An embedding vector produced by an AI model.
    """
    model: str
    dimensions: int
    embedding: Union[List[float], np.ndarray]
    values: Optional[List[float]] = None  # For backward compatibility
    
    def __post_init__(self):
        # If embedding is a numpy array, make sure it's the right shape
        if isinstance(self.embedding, np.ndarray):
            self.embedding = self.embedding.reshape(self.dimensions)
        
        # For backward compatibility
        if self.values is None:
            if isinstance(self.embedding, np.ndarray):
                self.values = self.embedding.tolist()
            else:
                self.values = list(self.embedding)
    
    def as_list(self) -> List[float]:
        """Convert the embedding to a list of floats."""
        if isinstance(self.embedding, np.ndarray):
            return self.embedding.tolist()
        return list(self.embedding)
    
    def as_numpy(self) -> np.ndarray:
        """Convert the embedding to a numpy array."""
        if isinstance(self.embedding, np.ndarray):
            return self.embedding
        return np.array(self.embedding, dtype=np.float32)