---
id: T-api-009
kind: impl
feature: F-upload
title: batches list/get/update
service: api
depends_on:
- T-api-009t
- T-api-001
edit:
- services/api/src/rag_api/services/batches.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_batches.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/batches.py && uv run --frozen ruff check src/rag_api/services/batches.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_batches.py
max_attempts: 3
---

## Goal
Implement: batches list/get/update. The tests written by T-api-009t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or .autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
