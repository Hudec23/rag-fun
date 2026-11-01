---
id: T-api-018
kind: impl
feature: F-stage-flow
title: worker callbacks record_started + record_result
service: api
depends_on:
- T-api-018t
- T-api-015
edit:
- services/api/src/rag_api/services/results.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_results.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/results.py && uv run --frozen ruff check src/rag_api/services/results.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_results.py
max_attempts: 3
---

## Goal
Implement: worker callbacks record_started + record_result. The tests written by T-api-018t define done.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test).

Stub in `services/api/src/rag_api/services/results.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Worker callbacks (contracts/openapi/internal.yaml)."""
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.events import EventBus
from rag_api.queue import JobQueue
from rag_api.schemas.system import StageResult, StageStarted


async def record_started(session: AsyncSession, body: StageStarted) -> None:
    """404 STAGE_RUN_NOT_FOUND. Only when status == 'queued': status 'running', started_at."""
    raise NotImplementedError("not implemented")

async def record_result(
    session: AsyncSession, queue: JobQueue, events: EventBus, body: StageResult
) -> None:
    """404 STAGE_RUN_NOT_FOUND. If status already done/failed/stale: return (duplicate).
    Else set status, artifact_key, summary, error, started_at (if None), finished_at; flush.
    done -> run_all.advance_plan(run); failed -> run.run_all_plan = []. Publish run.updated
    reason 'stage_result'."""
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
