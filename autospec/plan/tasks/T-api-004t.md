---
id: T-api-004t
kind: test
feature: F-stage-flow
title: 'Write tests: ArqJobQueue.enqueue'
service: api
depends_on: []
edit:
- services/api/tests/integration/test_queue.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_queue.py && uv run --frozen ruff check tests/integration/test_queue.py && uv run --frozen pytest -q --collect-only tests/integration/test_queue.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_queue.py
max_attempts: 3
---

## Goal
Write unit tests for: ArqJobQueue.enqueue. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-004 implements it.

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

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. enqueue('chunk', {'stage_run_id': 'x1', 'a': 1}, 'ingest') with an ArqRedis from arq.create_pool(RedisSettings.from_dsn(REDIS_URL)) → a job with function 'chunk' is in queue 'ingest' (pool.queued_jobs(queue_name='ingest')) whose args == ({'stage_run_id': 'x1', 'a': 1},)
2. job id equals payload['stage_run_id'] ('x1')
3. enqueuing the same stage_run_id twice leaves exactly one queued job
4. payload without stage_run_id (e.g. drop_collection {'qdrant_name': 'rf_…'}) is enqueued on queue 'query' with a generated id

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
