---
id: T-api-016
kind: impl
feature: F-stage-flow
title: ingest runs create/get/list/batch ingest
service: api
depends_on:
- T-api-016t
- T-api-010
- T-api-015
edit:
- services/api/src/rag_api/services/ingest_runs.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_ingest_runs.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/ingest_runs.py && uv run --frozen ruff check src/rag_api/services/ingest_runs.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_ingest_runs.py
max_attempts: 3
---

## Goal
Implement: ingest runs create/get/list/batch ingest. The tests written by T-api-016t define done.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test). Monkeypatch job_payloads.build_payload to return {}.

Stub in `services/api/src/rag_api/services/ingest_runs.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.db.models import IngestRunRow
from rag_api.events import EventBus
from rag_api.queue import JobQueue
from rag_api.schemas.runs import (
    BatchIngestRequest,
    IngestRunCreate,
    IngestRunList,
    IngestRunOut,
    IngestRunPage,
)


async def load_ingest_run(session: AsyncSession, run_id: str) -> IngestRunRow:
    """404 RUN_NOT_FOUND (details.run_id)."""
    raise NotImplementedError("not implemented")

async def ingest_run_out(session: AsyncSession, run_id: str) -> IngestRunOut:
    """Run + its file + latest row per stage (None if never run) + run_all_pending = plan stages."""
    raise NotImplementedError("not implemented")

async def create_ingest_run(session: AsyncSession, body: IngestRunCreate) -> IngestRunOut:
    """404 FILE_NOT_FOUND / COLLECTION_NOT_FOUND (file checked first). Insert, flush, return out."""
    raise NotImplementedError("not implemented")

async def list_ingest_runs(
    session: AsyncSession, limit: int, offset: int, file_id: str | None, collection_id: str | None
) -> IngestRunPage:
    """Order created_at desc, id desc."""
    raise NotImplementedError("not implemented")

async def ingest_batch(
    session: AsyncSession,
    queue: JobQueue,
    events: EventBus,
    batch_id: str,
    body: BatchIngestRequest,
) -> IngestRunList:
    """404 BATCH_NOT_FOUND then COLLECTION_NOT_FOUND. For each file of the batch (upload order):
    create run, run_all.start_run_all(run, from_stage='parse', params=body.params dumped)."""
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
