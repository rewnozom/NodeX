"""
ai_agent/core/models/base.py - Base model interfaces and types
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

class ModelType(Enum):
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"

@dataclass
class ModelConfig:
    provider: str
    model_name: str
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    kwargs: Dict[str, Any] = None

class BaseModel(ABC):
    """Base class for all model implementations"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.total_tokens = 0
        self.last_response: Optional[Dict[str, Any]] = None

    @abstractmethod
    async def generate(self, prompt: str) -> AsyncGenerator[str, None]:
        """Generate text from prompt"""
        pass

    @abstractmethod
    async def chat(self, messages: list[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """Chat completion from messages"""
        pass

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for text"""
        pass

    @abstractmethod
    async def get_token_count(self, text: str) -> int:
        """Count tokens in text"""
        pass

    @property
    def token_limit(self) -> int:
        """Get model's token limit"""
        pass

    def parse_response(self, response: Any) -> Dict[str, Any]:
        """Parse provider response into standard format"""
        pass