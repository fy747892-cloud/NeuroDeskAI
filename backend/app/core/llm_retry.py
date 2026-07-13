import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")

DEFAULT_BACKOFF_SECONDS: tuple[float, ...] = (1.0, 4.0)


async def with_retry(
    fn: Callable[[], Awaitable[T]],
    *,
    attempts: int = 2,
    backoff_seconds: tuple[float, ...] = DEFAULT_BACKOFF_SECONDS,
) -> T:
    """Retry an async LLM call with fixed backoff (CILT_5 §9.1: 2 attempts, 1s/4s backoff).

    Re-raises the last exception once attempts are exhausted so existing callers'
    error handling (RuntimeError -> ProviderError / job failure) is unaffected.
    """
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            return await fn()
        except Exception as exc:  # noqa: BLE001 - intentionally broad, re-raised below
            last_exc = exc
            if attempt < attempts - 1:
                delay = backoff_seconds[min(attempt, len(backoff_seconds) - 1)]
                await asyncio.sleep(delay)
    assert last_exc is not None
    raise last_exc
