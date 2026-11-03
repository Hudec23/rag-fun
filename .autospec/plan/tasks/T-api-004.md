---
id: T-api-004
kind: impl
feature: F-stage-flow
title: ArqJobQueue.enqueue
service: api
depends_on:
- T-api-004t
edit:
- services/api/src/rag_api/queue.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_queue.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/queue.py && uv run --frozen ruff check src/rag_api/queue.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_queue.py
max_attempts: 3
---

## Goal
Implement: ArqJobQueue.enqueue. The tests written by T-api-004t define done.

## Context
Integration test against redis-test (REDIS_URL env). Flush the db (await pool.flushdb()) at the start of each test.

Stub in `services/api/src/rag_api/queue.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Enqueue worker jobs (contracts/jobs/*.schema.json) on arq queues 'ingest' / 'query'."""
from typing import Any, Protocol


class JobQueue(Protocol):
    async def enqueue(self, function: str, payload: dict[str, Any], queue: str) -> None:
        """function = job name (e.g. 'chunk'); payload = the job JSON; queue = 'ingest' | 'query'."""
        ...

class ArqJobQueue:
    """Wraps arq.connections.ArqRedis: enqueue_job(function, payload, _queue_name=queue).
    _job_id = payload['stage_run_id'] when present (arq then drops duplicates)."""

    def __init__(self, redis: Any) -> None:
        self.redis = redis

    async def enqueue(self, function: str, payload: dict[str, Any], queue: str) -> None:
        raise NotImplementedError("not implemented")
```

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or .autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
