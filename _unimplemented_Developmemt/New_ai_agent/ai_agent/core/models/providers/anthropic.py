"""
ai_agent/core/models/providers/anthropic.py - Anthropic Claude implementation
"""

import aiohttp
import json
from typing import AsyncGenerator, Dict, Any
import anthropic
from ..base import BaseModel, ModelConfig

class AnthropicModel(BaseModel):
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.client = anthropic.Anthropic(api_key=config.api_key)

    async def chat(self, messages: list[Dict[str, str]]) -> AsyncGenerator[str, None]:
        formatted_messages = self._format_messages(messages)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "anthropic-version": "2023-06-01",
                    "x-api-key": self.config.api_key,
                    "content-type": "application/json",
                },
                json={
                    "model": self.config.model_name,
                    "messages": formatted_messages,
                    "max_tokens": self.config.max_tokens,
                    "stream": True
                }
            ) as response:
                async for line in response.content:
                    if line.strip():
                        data = json.loads(line)
                        if "content" in data:
                            yield data["content"][0]["text"]

    async def generate(self, prompt: str) -> AsyncGenerator[str, None]:
        async for chunk in self.chat([{"role": "user", "content": prompt}]):
            yield chunk

    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Anthropic does not provide embeddings API")

    async def get_token_count(self, text: str) -> int:
        return self.client.count_tokens(text)

    @property
    def token_limit(self) -> int:
        limits = {
            "claude-3-opus-20240229": 200000,
            "claude-3-sonnet-20240229": 200000,
            "claude-3-haiku-20240307": 200000,
        }
        return limits.get(self.config.model_name, 100000)

    def _format_messages(self, messages: list[Dict[str, str]]) -> list[Dict[str, str]]:
        formatted = []
        for msg in messages:
            if msg["role"] == "system":
                continue  # System messages handled differently for Claude
            formatted.append({
                "role": "assistant" if msg["role"] == "assistant" else "user",
                "content": msg["content"]
            })
        return formatted