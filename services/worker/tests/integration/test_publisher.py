"""RedisEventPublisher against redis-test (redis.asyncio.from_url(REDIS_URL)): events reach the raw
pub/sub channel 'events:{run_id}' as compact JSON; transport errors are swallowed (lossy by contract)."""

import json
from collections.abc import AsyncIterator
from typing import Any

import pytest
from redis import asyncio as redis_asyncio
from redis.asyncio.client import PubSub
from redis.exceptions import ConnectionError

from rag_worker.publisher import RedisEventPublisher


@pytest.fixture
async def redis(ctx: dict[str, Any]) -> AsyncIterator[redis_asyncio.Redis]:
    client = redis_asyncio.from_url(ctx["settings"].redis_url)
    yield client
    await client.aclose()


async def _next_message(sub: PubSub) -> dict[str, Any]:
    """First non-subscribe message on the channel (pub/sub delivery can lag by one poll)."""
    for _ in range(5):
        msg = await sub.get_message(ignore_subscribe_messages=True, timeout=1.0)
        if msg is not None:
            return msg
    raise AssertionError("no message received on the channel")


async def test_publish_delivers_json_to_run_channel(redis: redis_asyncio.Redis) -> None:
    event = {"type": "stage.started", "x": "ü"}
    sub = redis.pubsub()
    await sub.subscribe("events:r1")
    try:
        await RedisEventPublisher(redis).publish("r1", event)
        msg = await _next_message(sub)
    finally:
        await sub.aclose()
    assert msg["type"] == "message"
    assert msg["channel"] == b"events:r1"
    assert json.loads(msg["data"]) == event


async def test_message_is_compact_json(redis: redis_asyncio.Redis) -> None:
    event = {"type": "stage.started", "run_id": "r2", "version": 1}
    sub = redis.pubsub()
    await sub.subscribe("events:r2")
    try:
        await RedisEventPublisher(redis).publish("r2", event)
        msg = await _next_message(sub)
    finally:
        await sub.aclose()
    raw = msg["data"]
    assert raw == b'{"type":"stage.started","run_id":"r2","version":1}'
    assert json.loads(raw) == event


class _BrokenRedis:
    """Stand-in redis client whose publish always fails."""

    async def publish(self, *args: Any) -> int:
        raise ConnectionError("connection lost")


async def test_publish_swallows_connection_error() -> None:
    publisher = RedisEventPublisher(_BrokenRedis())
    assert await publisher.publish("r1", {"type": "stage.started"}) is None
