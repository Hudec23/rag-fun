---
id: T-worker-005
kind: impl
feature: F-stage-flow
title: S3ObjectStore for artifacts
service: worker
depends_on:
- T-worker-005t
edit:
- services/worker/src/rag_worker/store.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/integration/test_store_s3.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/store.py && uv run --frozen ruff check src/rag_worker/store.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/integration/test_store_s3.py
max_attempts: 3
---

## Goal
Implement: S3ObjectStore for artifacts. The tests written by T-worker-005t define done.

## Context
Integration test against s3-test (S3_* env). Create buckets 'uploads' and 'artifacts' at test start with aioboto3 if missing.

Stub in `services/worker/src/rag_worker/store.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""S3 access: read uploads (originals) and artifacts, write artifacts only."""
from typing import Any, Protocol
from rag_worker.config import Settings


class ObjectStore(Protocol):
    async def get_bytes(self, bucket: str, key: str) -> bytes: ...
    async def put_bytes(self, bucket: str, key: str, data: bytes, content_type: str) -> None: ...
    async def get_json(self, bucket: str, key: str) -> Any: ...
    async def put_json(self, bucket: str, key: str, obj: Any) -> None: ...

class S3ObjectStore:
    """aioboto3. Missing key -> WorkerError('ARTIFACT_NOT_FOUND' for bucket artifacts,
    'FILE_NOT_FOUND' for bucket uploads, details={'key': key}); any other failure ->
    WorkerError('S3_ERROR', details={'key': key}). put_json: UTF-8, separators (',', ':'),
    content type application/json; ensure_ascii False."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def get_bytes(self, bucket: str, key: str) -> bytes:
        raise NotImplementedError("not implemented")

    async def put_bytes(self, bucket: str, key: str, data: bytes, content_type: str) -> None:
        raise NotImplementedError("not implemented")

    async def get_json(self, bucket: str, key: str) -> Any:
        raise NotImplementedError("not implemented")

    async def put_json(self, bucket: str, key: str, obj: Any) -> None:
        raise NotImplementedError("not implemented")
```

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
