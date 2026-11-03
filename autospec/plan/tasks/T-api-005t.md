---
id: T-api-005t
kind: test
feature: F-live-progress
title: 'Write tests: RedisEventBus publish/subscribe'
service: api
depends_on: []
edit:
- services/api/tests/integration/test_event_bus.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_event_bus.py && uv run --frozen ruff check tests/integration/test_event_bus.py && uv run --frozen pytest -q --collect-only tests/integration/test_event_bus.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_event_bus.py
max_attempts: 3
---

## Goal
Write unit tests for: RedisEventBus publish/subscribe. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-005 implements it.

## Context
Integration test against redis-test: `redis.asyncio.from_url(os.environ['REDIS_URL'])`. subscribe must use redis pubsub on channel events.channel(run_id) and json.loads each message.

Stub in `services/api/src/rag_api/events.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Redis pub/sub on channel 'events:{run_id}' (contracts/events/*.schema.json)."""
from collections.abc import AsyncIterator
from typing import Any, Protocol


class EventBus(Protocol):
    async def publish(self, run_id: str, event: dict[str, Any]) -> None: ...

    def subscribe(self, run_id: str) -> AsyncIterator[dict[str, Any]]:
        """Yields every event published on the run's channel after subscribing, parsed from JSON."""
        ...

class RedisEventBus:
    def __init__(self, redis: Any) -> None:
        self.redis = redis  # redis.asyncio.Redis

    async def publish(self, run_id: str, event: dict[str, Any]) -> None:
        raise NotImplementedError("not implemented")

    def subscribe(self, run_id: str) -> AsyncIterator[dict[str, Any]]:
        raise NotImplementedError("not implemented")
```

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. publish(run_id, {'type': 'run.updated', 'x': 1}) → a raw redis subscriber on 'events:<run_id>' receives the JSON string that json.loads to the same dict
2. subscribe(run_id) yields events published after subscribing, in order (publish two, read two with asyncio.wait_for 5 s)
3. events published on another run's channel are not yielded
4. a non-JSON message published raw on the channel is skipped, the next valid event is still yielded

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
