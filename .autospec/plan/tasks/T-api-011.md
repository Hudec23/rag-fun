---
id: T-api-011
kind: impl
feature: F-collections
title: create_collection + delete_collection
service: api
depends_on:
- T-api-011t
edit:
- services/api/src/rag_api/services/collections.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_collections_write.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/collections.py && uv run --frozen ruff check src/rag_api/services/collections.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_collections_write.py
max_attempts: 3
---

## Goal
Implement: create_collection + delete_collection. The tests written by T-api-011t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or .autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
