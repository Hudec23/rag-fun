"""RedisEventBus publish/subscribe against redis-test (REDIS_URL)."""

import asyncio
import json
import os
from collections.abc import AsyncIterator
from typing import Any

import pytest
import redis.asyncio as aioredis
from redis.asyncio import Redis

from rag_api.events import RedisEventBus, channel


@pytest.fixture
async def redis() -> AsyncIterator[Redis]:
    r = aioredis.from_url(os.environ["REDIS_URL"])
    yield r
    await r.aclose()


@pytest.fixture
def bus(redis: Redis) -> RedisEventBus:
    return RedisEventBus(redis)


async def next_message(pubsub: Any) -> dict[str, Any]:
    """First pub/sub message on an already-subscribed channel within 5 s."""

    async def poll() -> dict[str, Any]:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message is not None:
                return message
            await asyncio.sleep(0.01)

    return await asyncio.wait_for(poll(), 5)


async def wait_subscribed(redis: Redis, run_id: str) -> None:
    """Barrier: return once the run's channel has a subscriber (pubsub_numsub)."""

    async def poll() -> None:
        ch = channel(run_id)
        while True:
            counts = {name: count for name, count in await redis.pubsub_numsub(ch)}
            if counts.get(ch.encode(), 0) >= 1:
                return
            await asyncio.sleep(0.01)

    await asyncio.wait_for(poll(), 5)


async def read_events(events: AsyncIterator[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    return [await asyncio.wait_for(events.__anext__(), 5) for _ in range(count)]


async def test_publish_sends_json_to_run_channel(redis: Redis, bus: RedisEventBus) -> None:
    run_id = "019a4b2c-1d00-7b00-8000-0000000000aa"
    event = {"type": "run.updated", "x": 1}
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel(run_id))
    try:
        await bus.publish(run_id, event)
        message = await next_message(pubsub)
    finally:
        await pubsub.aclose()
    assert message["type"] == "message"
    assert message["channel"] == channel(run_id).encode()
    assert json.loads(message["data"]) == event


async def test_subscribe_yields_events_published_after_subscribing_in_order(
    redis: Redis, bus: RedisEventBus
) -> None:
    run_id = "019a4b2c-1d00-7b00-8000-0000000000ab"
    events = bus.subscribe(run_id)
    reader = asyncio.create_task(read_events(events, 2))
    try:
        await wait_subscribed(redis, run_id)
        await bus.publish(run_id, {"type": "run.updated", "seq": 1})
        await bus.publish(run_id, {"type": "run.updated", "seq": 2})
        got = await reader
    finally:
        await events.aclose()
        if not reader.done():
            reader.cancel()
    assert got == [
        {"type": "run.updated", "seq": 1},
        {"type": "run.updated", "seq": 2},
    ]


async def test_events_on_another_run_channel_are_not_yielded(
    redis: Redis, bus: RedisEventBus
) -> None:
    run_id = "019a4b2c-1d00-7b00-8000-0000000000ac"
    other_id = "019a4b2c-1d00-7b00-8000-0000000000ad"
    events = bus.subscribe(run_id)
    reader = asyncio.create_task(read_events(events, 1))
    try:
        await wait_subscribed(redis, run_id)
        await bus.publish(other_id, {"type": "run.updated", "seq": 9})
        await bus.publish(run_id, {"type": "run.updated", "seq": 1})
        got = await reader
    finally:
        await events.aclose()
        if not reader.done():
            reader.cancel()
    assert got == [{"type": "run.updated", "seq": 1}]


async def test_non_json_message_is_skipped(redis: Redis, bus: RedisEventBus) -> None:
    run_id = "019a4b2c-1d00-7b00-8000-0000000000ae"
    events = bus.subscribe(run_id)
    reader = asyncio.create_task(read_events(events, 1))
    try:
        await wait_subscribed(redis, run_id)
        await redis.publish(channel(run_id), "not json at all")
        await bus.publish(run_id, {"type": "run.updated", "seq": 1})
        got = await reader
    finally:
        await events.aclose()
        if not reader.done():
            reader.cancel()
    assert got == [{"type": "run.updated", "seq": 1}]
