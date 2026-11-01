---
id: T-api-011t
kind: test
feature: F-collections
title: 'Write tests: create_collection + delete_collection'
service: api
depends_on: []
edit:
- services/api/tests/integration/test_collections_write.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_collections_write.py && uv run --frozen ruff check tests/integration/test_collections_write.py && uv run --frozen pytest -q --collect-only tests/integration/test_collections_write.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_collections_write.py
max_attempts: 3
---

## Goal
Write unit tests for: create_collection + delete_collection. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-011 implements it.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test).

Stub in `services/api/src/rag_api/services/collections.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Collections (R-012). Example module for the house style: get_collection is implemented."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.catalog import DENSE_MODELS
from rag_api.db.models import CollectionRow
from rag_api.errors import AppError
from rag_api.ids import to_iso
from rag_api.queue import JobQueue
from rag_api.schemas.collections import CollectionCreate, CollectionList, CollectionOut


async def create_collection(session: AsyncSession, body: CollectionCreate) -> CollectionOut:
    """Insert a row: id = new_id(), qdrant_name = qdrant_name_for(id), dense_dims from
    catalog.DENSE_MODELS[body.dense_model][0], created_at = utcnow(). Name already used ->
    AppError('COLLECTION_NAME_TAKEN', details={'name': name}). Flush (no commit) and return to_out."""
    _ = DENSE_MODELS
    raise NotImplementedError("not implemented")

async def delete_collection(session: AsyncSession, queue: JobQueue, collection_id: str) -> None:
    """Load (404 COLLECTION_NOT_FOUND), delete stage_runs of its ingest + query runs, delete the row
    (runs cascade), flush, then enqueue('drop_collection', {'qdrant_name': ...}, 'query')."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. create_collection(name 'exp', dense 'nomic-embed-text', sparse 'Qdrant/bm25') with frozen_now → dense_dims 768, qdrant_name 'rf_' + id without dashes, created_at '2026-11-01T18:22:05.123Z'
2. dense 'all-minilm' → dims 384; 'mxbai-embed-large' → 1024
3. same name twice → AppError COLLECTION_NAME_TAKEN details {'name': 'exp'}
4. delete_collection: row removed, its ingest runs + query runs + their stage runs removed, queue.jobs == [('drop_collection', {'qdrant_name': …}, 'query')]
5. delete_collection(unknown) → COLLECTION_NOT_FOUND, no job enqueued

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
