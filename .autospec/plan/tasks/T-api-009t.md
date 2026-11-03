---
id: T-api-009t
kind: test
feature: F-upload
title: 'Write tests: batches list/get/update'
service: api
depends_on: []
edit:
- services/api/tests/integration/test_batches.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_batches.py && uv run --frozen ruff check tests/integration/test_batches.py && uv run --frozen pytest -q --collect-only tests/integration/test_batches.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_batches.py
max_attempts: 3
---

## Goal
Write unit tests for: batches list/get/update. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-009 implements it.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test).

Stub in `services/api/src/rag_api/services/batches.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.db.models import BatchRow, FileRow
from rag_api.schemas.files import BatchList, BatchOut, BatchUpdate, BatchWithFiles, FileOut


def batch_out(row: BatchRow, file_count: int) -> BatchOut:
    raise NotImplementedError("not implemented")

def file_out(row: FileRow) -> FileOut:
    raise NotImplementedError("not implemented")

async def list_batches(session: AsyncSession, limit: int, offset: int) -> BatchList:
    """Order created_at desc, id desc. file_count via count of files per batch. page.total = all batches."""
    raise NotImplementedError("not implemented")

async def get_batch(session: AsyncSession, batch_id: str) -> BatchWithFiles:
    """404 BATCH_NOT_FOUND (details.batch_id). files ordered created_at asc, id asc (= upload order)."""
    raise NotImplementedError("not implemented")

async def update_batch(session: AsyncSession, batch_id: str, body: BatchUpdate) -> BatchOut:
    """404 BATCH_NOT_FOUND. Only fields that are not None change; tags normalized (sorted, unique).
    Body with neither field -> AppError('VALIDATION_ERROR', details={'field': 'body'})."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. list_batches with 3 batches created at t1<t2<t3 (insert BatchRow/FileRow directly) → items newest first, file_count per batch correct, page {total 3, limit 2, offset 0} when limit=2
2. list_batches offset beyond total → items [] and total unchanged
3. get_batch → files ordered by created_at asc; timestamps formatted '2026-11-01T18:22:05.123Z'
4. get_batch(unknown id) → AppError BATCH_NOT_FOUND details {'batch_id': id}
5. update_batch(tags ['b','a','a']) → tags ['a','b']; name unchanged
6. update_batch(BatchUpdate()) → VALIDATION_ERROR details {'field': 'body'}

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
