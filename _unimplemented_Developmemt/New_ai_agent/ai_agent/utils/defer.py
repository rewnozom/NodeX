# ai_agent/utils/defer.py
"""
ai_agent/utils/defer.py - Deferred execution utilities
"""

import asyncio
from typing import Callable, Any, Coroutine
from functools import wraps

def deferred(f: Callable[..., Any]) -> Callable[..., Coroutine[Any, Any, Any]]:
    """Decorator to defer the execution of a function"""
    @wraps(f)
    async def wrapped(*args: Any, **kwargs: Any) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, f, *args, **kwargs)
    return wrapped

async def defer_async(coroutine: Coroutine[Any, Any, Any]) -> Any:
    """Defer the execution of an async coroutine"""
    return await asyncio.create_task(coroutine)