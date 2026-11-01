---
id: T-api-010t
kind: test
feature: F-upload
title: 'Write tests: files list/get/update/delete/content'
service: api
depends_on: []
edit:
- services/api/tests/integration/test_files.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_files.py && uv run --frozen ruff check tests/integration/test_files.py && uv run --frozen pytest -q --collect-only tests/integration/test_files.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_files.py
max_attempts: 3
---

## Goal
Write unit tests for: files list/get/update/delete/content. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-010 implements it.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test).

Stub in `services/api/src/rag_api/services/files.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.config import Settings
from rag_api.queue import JobQueue
from rag_api.s3 import ObjectStore
from rag_api.schemas.files import FileList, FileOut, FileUpdate


async def list_files(
    session: AsyncSession,
    limit: int,
    offset: int,
    batch_id: str | None,
    tag: str | None,
    mime: str | None,
) -> FileList:
    """Filters AND-ed (tag: files.tags contains tag). Order created_at desc, filename asc.
    page.total counts filtered rows."""
    raise NotImplementedError("not implemented")

async def get_file(session: AsyncSession, file_id: str) -> FileOut:
    """404 FILE_NOT_FOUND (details.file_id)."""
    raise NotImplementedError("not implemented")

async def update_file(session: AsyncSession, file_id: str, body: FileUpdate) -> FileOut:
    """Replace tags (normalized). 404 FILE_NOT_FOUND."""
    raise NotImplementedError("not implemented")

async def delete_file(
    session: AsyncSession, store: ObjectStore, queue: JobQueue, settings: Settings, file_id: str
) -> None:
    """404 FILE_NOT_FOUND. For each distinct collection of the file's ingest runs that has a store
    stage run with status done: enqueue('delete_points', {'qdrant_name', 'file_id'}, 'query').
    Delete stage_runs of the file's ingest runs, delete the file row (ingest runs cascade),
    flush, then store.delete(uploads bucket, s3_key)."""
    raise NotImplementedError("not implemented")

async def get_file_content(
    session: AsyncSession, store: ObjectStore, settings: Settings, file_id: str
) -> tuple[bytes, str, str]:
    """(bytes, mime, filename). 404 FILE_NOT_FOUND."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. list_files filters: batch_id only, tag 'tax' (files.tags contains), mime 'text/plain', and all three AND-ed; page.total counts filtered rows
2. list_files order: created_at desc then filename asc (two files with the same created_at sorted by name)
3. get_file unknown → FILE_NOT_FOUND details {'file_id'}
4. update_file(tags ['z','a','z']) → tags ['a','z']
5. delete_file: file with a done store stage run in collection C → queue.jobs == [('delete_points', {'qdrant_name': C.qdrant_name, 'file_id': id}, 'query')], file row and its ingest + stage rows gone, upload object removed from store
6. delete_file of a file never stored → no jobs enqueued
7. get_file_content returns (bytes, mime, filename) from the store

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
