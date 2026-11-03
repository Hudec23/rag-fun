---
id: T-worker-007
kind: impl
feature: F-live-progress
title: RedisEventPublisher
service: worker
depends_on:
- T-worker-007t
edit:
- services/worker/src/rag_worker/publisher.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/integration/test_publisher.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/publisher.py && uv run --frozen ruff check src/rag_worker/publisher.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/integration/test_publisher.py
max_attempts: 3
---

## Goal
Implement: RedisEventPublisher. The tests written by T-worker-007t define done.

## Context
Integration test against redis-test (redis.asyncio.from_url(REDIS_URL)).

Stub in `services/worker/src/rag_worker/publisher.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Progress events on Redis channel 'events:{run_id}' (contracts/events/*.schema.json)."""
from typing import Any, Protocol


class EventPublisher(Protocol):
    async def publish(self, run_id: str, event: dict[str, Any]) -> None: ...

class RedisEventPublisher:
    """redis.publish(f'events:{run_id}', json.dumps(event, separators=(',', ':'))). Errors are logged
    and swallowed (events are lossy by contract)."""

    def __init__(self, redis: Any) -> None:
        self.redis = redis

    async def publish(self, run_id: str, event: dict[str, Any]) -> None:
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
