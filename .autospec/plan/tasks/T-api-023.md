---
id: T-api-023
kind: impl
feature: F-status
title: status of all components
service: api
depends_on:
- T-api-023t
- T-api-012
edit:
- services/api/src/rag_api/services/status.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_status_service.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/status.py && uv run --frozen ruff check src/rag_api/services/status.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_status_service.py
max_attempts: 3
---

## Goal
Implement: status of all components. The tests written by T-api-023t define done.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test). Use small stub classes for redis and the qdrant reader; respx for ollama.

Stub in `services/api/src/rag_api/services/status.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.config import Settings
from rag_api.qdrant_read import QdrantReader
from rag_api.s3 import ObjectStore
from rag_api.schemas.system import Status


async def get_status(
    session: AsyncSession,
    redis: Any,
    store: ObjectStore,
    qdrant: QdrantReader,
    http: httpx.AsyncClient,
    settings: Settings,
) -> Status:
    """8 components in schemas.system.COMPONENT_ORDER, each check timeout 2 s, never raises.
    worker-ingest/worker-query: redis EXISTS 'ragfun:worker:{queue}:heartbeat'. postgres: SELECT 1.
    redis: PING. qdrant: qdrant.client.get_collections(). s3: store.head_bucket(uploads).
    ollama: GET {app_settings.ollama_url}/api/tags. latency_ms = elapsed ms (int); detail = error
    text (≤500 chars) or 'heartbeat missing' for workers, None when ok."""
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
