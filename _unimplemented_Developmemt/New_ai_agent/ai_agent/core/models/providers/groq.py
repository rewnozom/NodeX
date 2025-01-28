"""
ai_agent/core/models/providers/groq.py - Groq LLM implementation
"""
import json
import aiohttp
from typing import AsyncGenerator, Dict, Any
import tiktoken
from ..base import BaseModel, ModelConfig

class GroqModel(BaseModel):
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = "https://api.groq.com/v1"
        self.encoding = tiktoken.encoding_for_model("text-davinci-003")  # Fallback encoding
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }

    async def chat(self, messages: list[Dict[str, str]]) -> AsyncGenerator[str, None]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": self.config.model_name,
                    "messages": messages,
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                    "stream": True
                }
            ) as response:
                async for line in response.content:
                    chunk = line.decode().strip()
                    if chunk and chunk.startswith("data: "):
                        data = json.loads(chunk[6:])
                        if content := data["choices"][0]["delta"].get("content"):
                            yield content

    async def generate(self, prompt: str) -> AsyncGenerator[str, None]:
        async for chunk in self.chat([{"role": "user", "content": prompt}]):
            yield chunk

    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Groq does not provide embeddings API")

    async def get_token_count(self, text: str) -> int:
        return len(self.encoding.encode(text))

    @property
    def token_limit(self) -> int:
        limits = {
            "mixtral-8x7b-32768": 32768,
            "llama2-70b-4096": 4096,
            "gemma-7b-it": 8192
        }
        return limits.get(self.config.model_name, 4096)