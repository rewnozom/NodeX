"""
ai_agent/core/models/providers/lmstudio.py - LMStudio model implementation
"""

import aiohttp
import json
from typing import AsyncGenerator, Dict, Any
import tiktoken

from ..base import BaseModel, ModelConfig

class LMStudioModel(BaseModel):
    """LMStudio API implementation"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = "http://localhost:1234/v1"
        self.encoding = tiktoken.get_encoding("cl100k_base")

    async def generate(self, prompt: str) -> AsyncGenerator[str, None]:
        """Generate text using LMStudio completion endpoint"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/completions",
                json={
                    "model": self.config.model_name,
                    "prompt": prompt,
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                    "stream": True
                }
            ) as response:
                async for line in response.content:
                    if line:
                        try:
                            json_line = json.loads(line.decode('utf-8').strip('data: '))
                            if json_line.get("choices"):
                                yield json_line["choices"][0]["text"]
                        except:
                            continue

    async def chat(self, messages: list[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """Chat completion using LMStudio chat endpoint"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.config.model_name,
                    "messages": messages,
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                    "stream": True
                }
            ) as response:
                async for line in response.content:
                    if line:
                        try:
                            json_line = json.loads(line.decode('utf-8').strip('data: '))
                            if json_line.get("choices"):
                                content = json_line["choices"][0]["delta"].get("content")
                                if content:
                                    yield content
                        except:
                            continue

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings using LMStudio embeddings endpoint"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/embeddings",
                json={
                    "model": self.config.model_name,
                    "input": text
                }
            ) as response:
                result = await response.json()
                return result["data"][0]["embedding"]

    async def get_token_count(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        return len(self.encoding.encode(text))

    @property
    def token_limit(self) -> int:
        """Get model's token limit"""
        # Use a default limit since LMStudio doesn't expose this
        return 8192

    def parse_response(self, response: Any) -> Dict[str, Any]:
        """Parse LMStudio response into standard format"""
        if not response:
            return {}
            
        try:
            if isinstance(response, str):
                return {"content": response}
                
            if "choices" in response:
                choice = response["choices"][0]
                if "text" in choice:
                    return {"content": choice["text"]}
                if "message" in choice:
                    return {"content": choice["message"]["content"]}
                    
            return {"content": str(response)}
            
        except Exception:
            return {"content": str(response)}