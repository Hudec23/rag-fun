---
id: T-api-008
kind: impl
feature: F-upload
title: upload_batch + detect_mime + default_batch_name
service: api
depends_on:
- T-api-008t
- T-api-001
- T-api-003
edit:
- services/api/src/rag_api/services/uploads.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_uploads.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/uploads.py && uv run --frozen ruff check src/rag_api/services/uploads.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_uploads.py
max_attempts: 3
---

## Goal
Implement: upload_batch + detect_mime + default_batch_name. The tests written by T-api-008t define done.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test).

Stub in `services/api/src/rag_api/services/uploads.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Batch upload (R-001, R-002, R-003)."""
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.config import Settings
from rag_api.s3 import ObjectStore
from rag_api.schemas.files import BatchWithFiles, IncomingFile


def detect_mime(filename: str) -> str:
    """MIME from the lowercase extension via catalog.MIME_BY_EXT.
    Unknown/missing extension -> AppError('UNSUPPORTED_FILE_TYPE', details={'filename': filename})."""
    raise NotImplementedError("not implemented")

def default_batch_name(now_iso: str) -> str:
    """'2026-11-01T18:22:05.123Z' -> 'Batch 2026-11-01 18:22'."""
    raise NotImplementedError("not implemented")

async def upload_batch(
    session: AsyncSession,
    store: ObjectStore,
    settings: Settings,
    files: list[IncomingFile],
    name: str | None,
    tags: list[str],
) -> BatchWithFiles:
    """Validate ALL files first, in this order, before storing anything:
    0 files -> EMPTY_UPLOAD; len > settings.max_files_per_batch -> TOO_MANY_FILES (details.limit);
    for each file in order: detect_mime (UNSUPPORTED_FILE_TYPE); len(data) > max_upload_mb*1024*1024
    -> FILE_TOO_LARGE (details.filename, details.limit_mb); len(data) == 0 -> VALIDATION_ERROR
    (details.field='files', details.filename).
    Then: insert batch (name or default_batch_name, tags normalized), for each file: id=new_id(),
    key f'{batch_id}/{file_id}/{filename}', store.put_bytes(settings.s3_bucket_uploads, key, data, mime),
    sha256 hex of data, insert files row (tags []). Flush. Return BatchWithFiles (files in upload order,
    batch.file_count = len(files))."""
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
