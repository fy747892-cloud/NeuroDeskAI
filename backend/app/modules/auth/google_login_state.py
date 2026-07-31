import json
import secrets

from redis.asyncio import Redis

STATE_TTL_SECONDS = 600
STATE_KEY_PREFIX = "google_login_state:"
LOGIN_CODE_TTL_SECONDS = 60
LOGIN_CODE_KEY_PREFIX = "google_login_code:"


class GoogleLoginStateStore:
    """CSRF state and one-time token hand-off for the Google Sign-In flow, backed by Redis."""

    def __init__(self, redis: Redis):
        self._redis = redis

    async def generate_state(self) -> str:
        state = secrets.token_urlsafe(32)
        await self._redis.set(f"{STATE_KEY_PREFIX}{state}", "1", ex=STATE_TTL_SECONDS)
        return state

    async def consume_state(self, state: str) -> bool:
        # GETDEL is atomic: a state token can only ever be consumed once.
        return await self._redis.getdel(f"{STATE_KEY_PREFIX}{state}") is not None

    async def store_tokens(self, tokens: dict) -> str:
        code = secrets.token_urlsafe(32)
        await self._redis.set(
            f"{LOGIN_CODE_KEY_PREFIX}{code}", json.dumps(tokens), ex=LOGIN_CODE_TTL_SECONDS
        )
        return code

    async def consume_tokens(self, code: str) -> dict | None:
        payload = await self._redis.getdel(f"{LOGIN_CODE_KEY_PREFIX}{code}")
        if payload is None:
            return None
        return json.loads(payload)
