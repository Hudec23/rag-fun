"""Redis pub/sub on channel 'events:{run_id}' (contracts/events/*.schema.json)."""

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any, Protocol


def channel(run_id: str) -> str:
    return f"events:{run_id}"


class EventBus(Protocol):
    async def publish(self, run_id: str, event: dict[str, Any]) -> None: ...

    def subscribe(self, run_id: str) -> AsyncIterator[dict[str, Any]]:
        """Yields every event published on the run's channel after subscribing, parsed from JSON."""
        ...


class RedisEventBus:
    def __init__(self, redis: Any) -> None:
        self.redis = redis  # redis.asyncio.Redis

    async def publish(self, run_id: str, event: dict[str, Any]) -> None:
        await self.redis.publish(channel(run_id), json.dumps(event))

    async def subscribe(self, run_id: str) -> AsyncIterator[dict[str, Any]]:
        """Yields every event published on the run's channel after subscribing, parsed from JSON."""
        pubsub = self.redis.pubsub()
        try:
            await pubsub.subscribe(channel(run_id))
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message is None:
                    await asyncio.sleep(0.01)
                    continue
                try:
                    event = json.loads(message["data"])
                except ValueError:
                    continue
                if isinstance(event, dict):
                    yield event
        finally:
            await pubsub.aclose()


def run_updated_event(run_id: str, run_kind: str, reason: str, ts: str) -> dict[str, Any]:
    """contracts/events/run.updated.schema.json"""
    return {
        "type": "run.updated",
        "run_id": run_id,
        "run_kind": run_kind,
        "reason": reason,
        "ts": ts,
    }
