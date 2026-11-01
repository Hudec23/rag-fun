---
id: T-api-023t
kind: test
feature: F-status
title: 'Write tests: status of all components'
service: api
depends_on: []
edit:
- services/api/tests/integration/test_status_service.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_status_service.py && uv run --frozen ruff check tests/integration/test_status_service.py && uv run --frozen pytest -q --collect-only tests/integration/test_status_service.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_status_service.py
max_attempts: 3
---

## Goal
Write unit tests for: status of all components. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-023 implements it.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test). Use small stub classes for redis and the qdrant reader; respx for ollama.

Stub in `services/api/src/rag_api/services/status.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.config import Settings
from rag_api.qdrant_read import QdrantReader
from rag_api.s3 import ObjectStore
from rag_api.schemas.system import Status


async def get_status(
    session: AsyncSession,
    redis: Any,
    store: ObjectStore,
    qdrant: QdrantReader,
    http: httpx.AsyncClient,
    settings: Settings,
) -> Status:
    """8 components in schemas.system.COMPONENT_ORDER, each check timeout 2 s, never raises.
    worker-ingest/worker-query: redis EXISTS 'ragfun:worker:{queue}:heartbeat'. postgres: SELECT 1.
    redis: PING. qdrant: qdrant.client.get_collections(). s3: store.head_bucket(uploads).
    ollama: GET {app_settings.ollama_url}/api/tags. latency_ms = elapsed ms (int); detail = error
    text (≤500 chars) or 'heartbeat missing' for workers, None when ok."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. all healthy (stub redis with async ping/exists returning True, FakeObjectStore with bucket uploads, stub qdrant reader whose client.get_collections returns [], respx ollama 200) → 8 components in order api, worker-ingest, worker-query, postgres, redis, qdrant, s3, ollama, all ok, detail None
2. redis exists False for 'ragfun:worker:query:heartbeat' → worker-query ok False detail 'heartbeat missing'
3. store.fail = True → s3 ok False with detail text
4. ollama ConnectError → ollama ok False, others still ok
5. a check that hangs (stub awaits asyncio.sleep(10)) is reported not ok within ~2 s (assert total time < 5 s)

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
