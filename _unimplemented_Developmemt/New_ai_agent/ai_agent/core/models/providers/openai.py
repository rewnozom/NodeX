"""
ai_agent/core/models/providers/openai.py - OpenAI model implementation
"""

import json
import aiohttp
from typing import AsyncGenerator, Dict, Any
import tiktoken
from ..base import BaseModel, ModelConfig

class OpenAIModel(BaseModel):
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = "https://api.openai.com/v1"
        self.encoding = tiktoken.encoding_for_model(config.model_name)
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
                    if b"data: " in line:
                        chunk = line.decode().split("data: ")[1]
                        if chunk.strip() and chunk.strip() != "[DONE]":
                            content = json.loads(chunk)["choices"][0]["delta"].get("content")
                            if content:
                                yield content

    async def generate(self, prompt: str) -> AsyncGenerator[str, None]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/completions",
                headers=self.headers,
                json={
                    "model": self.config.model_name,
                    "prompt": prompt,
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                    "stream": True
                }
            ) as response:
                async for line in response.content:
                    if b"data: " in line:
                        chunk = line.decode().split("data: ")[1]
                        if chunk.strip() and chunk.strip() != "[DONE]":
                            content = json.loads(chunk)["choices"][0]["text"]
                            if content:
                                yield content

    async def embed(self, text: str) -> list[float]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/embeddings",
                headers=self.headers,
                json={
                    "model": self.config.model_name,
                    "input": text
                }
            ) as response:
                data = await response.json()
                return data["data"][0]["embedding"]

    async def get_token_count(self, text: str) -> int:
        return len(self.encoding.encode(text))

    @property
    def token_limit(self) -> int:
        limits = {
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384
        }
        return limits.get(self.config.model_name, 4096)