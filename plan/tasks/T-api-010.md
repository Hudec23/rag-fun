---
id: T-api-010
kind: impl
feature: F-upload
title: files list/get/update/delete/content
service: api
depends_on:
- T-api-010t
- T-api-001
- T-api-009
edit:
- services/api/src/rag_api/services/files.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_files.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/files.py && uv run --frozen ruff check src/rag_api/services/files.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_files.py
max_attempts: 3
---

## Goal
Implement: files list/get/update/delete/content. The tests written by T-api-010t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
