import json
import secrets
import uuid

from redis.asyncio import Redis

STATE_TTL_SECONDS = 600
STATE_KEY_PREFIX = "gmail_oauth_state:"


class OAuthStateStore:
    """Short-lived, single-use OAuth state tokens backed by Redis (CSRF protection)."""

    def __init__(self, redis: Redis):
        self._redis = redis

    async def generate(
        self, *, user_id: uuid.UUID, tenant_id: uuid.UUID, organization_id: uuid.UUID
    ) -> str:
        state = secrets.token_urlsafe(32)
        payload = json.dumps(
            {
                "user_id": str(user_id),
                "tenant_id": str(tenant_id),
                "organization_id": str(organization_id),
            }
        )
        await self._redis.set(f"{STATE_KEY_PREFIX}{state}", payload, ex=STATE_TTL_SECONDS)
        return state

    async def consume(self, state: str) -> dict | None:
        # GETDEL is atomic: a state token can only ever be consumed once,
        # closing the replay window between reading and deleting it.
        payload = await self._redis.getdel(f"{STATE_KEY_PREFIX}{state}")
        if payload is None:
            return None
        return json.loads(payload)
