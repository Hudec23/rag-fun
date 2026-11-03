---
id: T-api-013
kind: impl
feature: F-stage-flow
title: stage state machine (latest/active/downstream/check/stale/start_stage)
service: api
depends_on:
- T-api-013t
- T-api-004
- T-api-005
edit:
- services/api/src/rag_api/services/stages.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_stages.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/stages.py && uv run --frozen ruff check src/rag_api/services/stages.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_stages.py
max_attempts: 3
---

## Goal
Implement: stage state machine (latest/active/downstream/check/stale/start_stage). The tests written by T-api-013t define done.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test). Create runs by inserting FileRow/BatchRow/IngestRunRow/QueryRunRow/StageRunRow directly.

Stub in `services/api/src/rag_api/services/stages.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Stage state machine (R-013). Rules: contracts/openapi/api.yaml info.description 'Stage rules'."""
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.db.models import IngestRunRow, QueryRunRow, StageRunRow
from rag_api.events import EventBus
from rag_api.queue import JobQueue
from rag_api.schemas.runs import StageRunOut
Run = IngestRunRow | QueryRunRow


def run_kind_of(run: Run) -> str:
    return "ingest" if isinstance(run, IngestRunRow) else "query"

def stage_run_out(row: StageRunRow) -> StageRunOut:
    """Row -> DTO; timestamps via ids.to_iso (None stays None)."""
    raise NotImplementedError("not implemented")

async def latest_rows(session: AsyncSession, run_id: str) -> dict[str, StageRunRow]:
    """{stage: row with the highest version} for every stage that has at least one row."""
    raise NotImplementedError("not implemented")

def active_row(latest: dict[str, StageRunRow], stage: str) -> StageRunRow | None:
    """latest[stage] if its status is 'done', else None."""
    raise NotImplementedError("not implemented")

def downstream_of(stage: str) -> list[str]:
    """Stages after `stage` in its pipeline order (catalog.INGEST_STAGES / QUERY_STAGES).
    'chunk' -> ['embed', 'store']; 'generate' -> []; 'transform' -> ['retrieve', 'rerank', 'generate']."""
    raise NotImplementedError("not implemented")

def check_can_start(latest: dict[str, StageRunRow], stage: str) -> None:
    """latest[stage].status in (queued, running) -> AppError('STAGE_ALREADY_RUNNING', details={'stage'}).
    Required upstream (catalog.REQUIRED_UPSTREAM) without active row ->
    AppError('STAGE_PREREQUISITE_MISSING', details={'stage': stage, 'missing': upstream})."""
    raise NotImplementedError("not implemented")

def mark_stale(latest: dict[str, StageRunRow], stage: str) -> list[str]:
    """Set status 'stale' on latest rows of downstream stages whose status is done or failed.
    Returns the stages changed, in pipeline order."""
    raise NotImplementedError("not implemented")

async def start_stage(
    session: AsyncSession,
    queue: JobQueue,
    events: EventBus,
    run: Run,
    stage: str,
    params: dict[str, Any],
    *,
    keep_plan: bool = False,
) -> StageRunRow:
    """1. latest = latest_rows; check_can_start. 2. Insert row: id new_id, version latest+1 (or 1),
    status queued, params, created_at utcnow. 3. mark_stale. 4. Unless keep_plan: run.run_all_plan = [].
    5. Flush. 6. payload = await job_payloads.build_payload(session, run, row, latest) — call it
    through the module (`from rag_api.services import job_payloads` at the top, then
    `job_payloads.build_payload(...)`) so tests can monkeypatch it;
    queue.enqueue(stage, payload, catalog.QUEUE_OF[stage]). 7. Publish run.updated reason
    'stage_queued' (and a second one with 'stages_stale' if mark_stale changed anything)."""
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
