import asyncio
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")

async def retry_async(action: Callable[[], Awaitable[T]], max_retries: int) -> tuple[T, int]:
    attempts = 0
    last_error = None
    for attempt in range(max_retries + 1):
        attempts = attempt + 1
        try:
            return await action(), attempts
        except Exception as exc:
            last_error = exc
            if attempt >= max_retries:
                break
            await asyncio.sleep(0.4 * (2 ** attempt))
    raise last_error
