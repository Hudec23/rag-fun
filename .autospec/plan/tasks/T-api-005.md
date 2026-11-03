---
id: T-api-005
kind: impl
feature: F-live-progress
title: RedisEventBus publish/subscribe
service: api
depends_on:
- T-api-005t
edit:
- services/api/src/rag_api/events.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_event_bus.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/events.py && uv run --frozen ruff check src/rag_api/events.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_event_bus.py
max_attempts: 3
---

## Goal
Implement: RedisEventBus publish/subscribe. The tests written by T-api-005t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
