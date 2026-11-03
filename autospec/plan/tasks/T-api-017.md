---
id: T-api-017
kind: impl
feature: F-transform
title: query runs create/get/list
service: api
depends_on:
- T-api-017t
- T-api-013
edit:
- services/api/src/rag_api/services/query_runs.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_query_runs.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/query_runs.py && uv run --frozen ruff check src/rag_api/services/query_runs.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_query_runs.py
max_attempts: 3
---

## Goal
Implement: query runs create/get/list. The tests written by T-api-017t define done.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test).

Stub in `services/api/src/rag_api/services/query_runs.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.db.models import QueryRunRow
from rag_api.schemas.runs import QueryRunCreate, QueryRunOut, QueryRunPage


async def load_query_run(session: AsyncSession, run_id: str) -> QueryRunRow:
    """404 RUN_NOT_FOUND (details.run_id)."""
    raise NotImplementedError("not implemented")

async def query_run_out(session: AsyncSession, run_id: str) -> QueryRunOut:
    raise NotImplementedError("not implemented")

async def create_query_run(session: AsyncSession, body: QueryRunCreate) -> QueryRunOut:
    """404 COLLECTION_NOT_FOUND. Question stored stripped; empty after strip -> VALIDATION_ERROR
    (details.field='question')."""
    raise NotImplementedError("not implemented")

async def list_query_runs(
    session: AsyncSession, limit: int, offset: int, collection_id: str | None
) -> QueryRunPage:
    """Order created_at desc, id desc."""
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
