"""
ai_agent/utils/rate_limiter.py - Rate limiting implementation
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class RateLimit:
    requests_per_minute: int = 0
    tokens_per_minute: int = 0

class RateLimiter:
    def __init__(self, limits: Dict[str, RateLimit]):
        self.limits = limits
        self.request_times: Dict[str, list[float]] = {}
        self.token_counts: Dict[str, list[tuple[float, int]]] = {}
        self._lock = asyncio.Lock()

    async def wait_if_needed(self, key: str, token_count: Optional[int] = None):
        """Wait if rate limit would be exceeded"""
        async with self._lock:
            now = time.time()
            limit = self.limits.get(key)
            if not limit:
                return

            # Clean old data
            self._cleanup_old_data(key, now)

            # Check request rate
            if limit.requests_per_minute > 0:
                while len(self.request_times.get(key, [])) >= limit.requests_per_minute:
                    sleep_time = 60 - (now - self.request_times[key][0])
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)
                    now = time.time()
                    self._cleanup_old_data(key, now)

            # Check token rate
            if token_count and limit.tokens_per_minute > 0:
                current_tokens = sum(count for _, count in self.token_counts.get(key, []))
                while current_tokens + token_count > limit.tokens_per_minute:
                    sleep_time = 60 - (now - self.token_counts[key][0][0])
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)
                    now = time.time()
                    self._cleanup_old_data(key, now)
                    current_tokens = sum(count for _, count in self.token_counts.get(key, []))

            # Record request
            if limit.requests_per_minute > 0:
                if key not in self.request_times:
                    self.request_times[key] = []
                self.request_times[key].append(now)

            # Record tokens
            if token_count and limit.tokens_per_minute > 0:
                if key not in self.token_counts:
                    self.token_counts[key] = []
                self.token_counts[key].append((now, token_count))

    def _cleanup_old_data(self, key: str, now: float):
        """Remove data older than 1 minute"""
        if key in self.request_times:
            self.request_times[key] = [
                t for t in self.request_times[key] 
                if now - t < 60
            ]

        if key in self.token_counts:
            self.token_counts[key] = [
                (t, count) for t, count in self.token_counts[key]
                if now - t < 60
            ]

    def get_current_usage(self, key: str) -> tuple[int, int]:
        """Get current request and token counts"""
        now = time.time()
        self._cleanup_old_data(key, now)
        
        requests = len(self.request_times.get(key, []))
        tokens = sum(count for _, count in self.token_counts.get(key, []))
        
        return requests, tokens