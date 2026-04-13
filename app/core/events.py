"""Redis PubSub event bus for real-time SSE streaming."""

from __future__ import annotations

import json
from typing import AsyncGenerator

import redis.asyncio as aioredis

from app.core.config import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    return _redis


async def publish_event(tenant_id: str, event_type: str, data: dict):
    """Publish an event to the tenant's channel."""
    r = await get_redis()
    payload = json.dumps({"type": event_type, "data": data})
    await r.publish(f"tenant:{tenant_id}:events", payload)


async def subscribe_events(tenant_id: str) -> AsyncGenerator[str, None]:
    """Subscribe to a tenant's event channel. Yields SSE-formatted strings."""
    r = await get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(f"tenant:{tenant_id}:events")
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                payload = json.loads(message["data"])
                yield f"event: {payload['type']}\ndata: {json.dumps(payload['data'])}\n\n"
    finally:
        await pubsub.unsubscribe(f"tenant:{tenant_id}:events")
        await pubsub.close()
