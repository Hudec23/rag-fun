"""Worker heartbeat against redis-test: beat_once SETs the liveness key (EX 30) with schema-valid
JSON; heartbeat_loop beats every interval, reads running() each beat, and survives redis errors."""

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

import pytest
from redis import asyncio as redis_asyncio
from redis.exceptions import ConnectionError

from rag_worker.heartbeat import beat_once, heartbeat_key, heartbeat_loop
from tests.contract import errors

SCHEMA = "events/worker.heartbeat.schema.json"
KEY = "ragfun:worker:ingest:heartbeat"
TS = "2026-11-01T18:22:05.123Z"


@pytest.fixture
async def redis(ctx: dict[str, Any]) -> AsyncIterator[redis_asyncio.Redis]:
    client = redis_asyncio.from_url(ctx["settings"].redis_url)
    yield client
    await client.aclose()


async def test_beat_once_writes_expiring_valid_key(
    redis: redis_asyncio.Redis, frozen_now: datetime
) -> None:
    await redis.delete(KEY)
    await beat_once(redis, "ingest", "fake", 2)
    assert heartbeat_key("ingest") == KEY
    raw = await redis.get(KEY)
    assert raw is not None
    value = json.loads(raw)
    assert errors(value, SCHEMA) == []
    assert value == {
        "queue": "ingest",
        "ts": TS,
        "model_backend": "fake",
        "jobs_running": 2,
    }
    ttl = await redis.ttl(KEY)
    assert 25 <= ttl <= 30


async def test_loop_writes_key_and_reads_running_each_beat(
    redis: redis_asyncio.Redis, frozen_now: datetime
) -> None:
    beats = 0

    def running() -> int:
        nonlocal beats
        beats += 1
        return 7

    await redis.delete(KEY)
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(
            heartbeat_loop(redis, "ingest", "fake", running, interval=0.05), timeout=0.2
        )
    assert beats >= 2
    value = json.loads(await redis.get(KEY))
    assert errors(value, SCHEMA) == []
    assert value == {
        "queue": "ingest",
        "ts": TS,
        "model_backend": "fake",
        "jobs_running": 7,
    }


class _FailOnceRedis:
    """Stand-in redis client: the second SET raises, the rest succeed (and are recorded)."""

    def __init__(self) -> None:
        self.attempts = 0
        self.ok: list[tuple[str, str, Any]] = []

    async def set(self, name: str, value: str, *args: Any, **kwargs: Any) -> bool:
        self.attempts += 1
        if self.attempts == 2:
            raise ConnectionError("connection lost")
        ex = kwargs["ex"] if "ex" in kwargs else args[0]
        self.ok.append((name, value, ex))
        return True


async def test_loop_survives_redis_error_and_keeps_going(frozen_now: datetime) -> None:
    fake = _FailOnceRedis()
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(
            heartbeat_loop(fake, "ingest", "fake", lambda: 3, interval=0.05), timeout=0.2
        )
    assert fake.attempts >= 3  # kept beating after the failed one
    assert len(fake.ok) == fake.attempts - 1  # exactly one failed set
    for name, value, ex in fake.ok:
        doc = json.loads(value)
        assert name == KEY
        assert ex == 30
        assert errors(doc, SCHEMA) == []
        assert doc["jobs_running"] == 3
