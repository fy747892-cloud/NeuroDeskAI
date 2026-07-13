from redis.asyncio import Redis

from app.core.errors import RateLimitError


class RateLimiter:
    """Fixed-window rate limiter backed by Redis."""

    def __init__(self, redis: Redis):
        self._redis = redis

    async def check(self, *, key: str, limit: int, window_seconds: int) -> None:
        redis_key = f"rate_limit:{key}"
        current = await self._redis.incr(redis_key)
        if current == 1:
            await self._redis.expire(redis_key, window_seconds)
        if current > limit:
            raise RateLimitError("Too many requests, please try again later.")
