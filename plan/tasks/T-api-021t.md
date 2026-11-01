---
id: T-api-021t
kind: test
feature: F-qdrant-browser
title: 'Write tests: qdrant browser service'
service: api
depends_on: []
edit:
- services/api/tests/integration/test_qdrant_browser_service.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_qdrant_browser_service.py && uv run --frozen ruff check tests/integration/test_qdrant_browser_service.py && uv run --frozen pytest -q --collect-only tests/integration/test_qdrant_browser_service.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_qdrant_browser_service.py
max_attempts: 3
---

## Goal
Write unit tests for: qdrant browser service. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-021 implements it.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test). Use a small stub class in the test implementing QdrantReader's methods (no real Qdrant).

Stub in `services/api/src/rag_api/services/qdrant_browser.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Qdrant browser endpoints: resolve the collection row (404 COLLECTION_NOT_FOUND), then delegate to
QdrantReader with row.qdrant_name. Reader errors other than 'collection missing' -> 503 QDRANT_ERROR."""
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.qdrant_read import QdrantReader
from rag_api.schemas.qdrant import (
    CountRequest,
    CountResponse,
    FacetResponse,
    QdrantInfo,
    QdrantPoint,
    ScrollRequest,
    ScrollResponse,
)


async def info(session: AsyncSession, q: QdrantReader, collection_id: str) -> QdrantInfo:
    raise NotImplementedError("not implemented")

async def scroll(
    session: AsyncSession, q: QdrantReader, collection_id: str, body: ScrollRequest
) -> ScrollResponse:
    raise NotImplementedError("not implemented")

async def count(
    session: AsyncSession, q: QdrantReader, collection_id: str, body: CountRequest
) -> CountResponse:
    raise NotImplementedError("not implemented")

async def facet(
    session: AsyncSession, q: QdrantReader, collection_id: str, key: str
) -> FacetResponse:
    raise NotImplementedError("not implemented")

async def get_point(
    session: AsyncSession, q: QdrantReader, collection_id: str, point_id: str
) -> QdrantPoint:
    raise NotImplementedError("not implemented")
```

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. info(unknown collection id) → COLLECTION_NOT_FOUND
2. info delegates to reader.info(row.qdrant_name) (use a stub reader class recording calls)
3. scroll passes filter, limit, offset, with_vectors through and returns the reader's ScrollResponse
4. count returns CountResponse(count=reader result)
5. reader raising a generic Exception → AppError QDRANT_ERROR; reader raising AppError POINT_NOT_FOUND → propagated unchanged

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
