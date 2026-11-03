---
id: T-api-021
kind: impl
feature: F-qdrant-browser
title: qdrant browser service
service: api
depends_on:
- T-api-021t
- T-api-007
edit:
- services/api/src/rag_api/services/qdrant_browser.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_qdrant_browser_service.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/qdrant_browser.py && uv run --frozen ruff check src/rag_api/services/qdrant_browser.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_qdrant_browser_service.py
max_attempts: 3
---

## Goal
Implement: qdrant browser service. The tests written by T-api-021t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or .autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
