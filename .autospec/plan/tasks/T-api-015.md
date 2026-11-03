---
id: T-api-015
kind: impl
feature: F-stage-flow
title: run-all plans
service: api
depends_on:
- T-api-015t
- T-api-013
edit:
- services/api/src/rag_api/services/run_all.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_run_all.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/run_all.py && uv run --frozen ruff check src/rag_api/services/run_all.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_run_all.py
max_attempts: 3
---

## Goal
Implement: run-all plans. The tests written by T-api-015t define done.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test). Monkeypatch job_payloads.build_payload to return {} so only the plan logic is tested.

Stub in `services/api/src/rag_api/services/run_all.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Run-all plans (R-013): start stages one after another as each reports done."""
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.db.models import IngestRunRow, QueryRunRow
from rag_api.events import EventBus
from rag_api.queue import JobQueue


def first_not_done(order: list[str], latest_status: dict[str, str]) -> str | None:
    """First stage in `order` whose latest status (missing = never run) is not 'done'; None if all done."""
    raise NotImplementedError("not implemented")

async def start_run_all(
    session: AsyncSession,
    queue: JobQueue,
    events: EventBus,
    run: IngestRunRow | QueryRunRow,
    from_stage: str | None,
    params: dict[str, dict[str, Any]],
) -> bool:
    """Resolve start = from_stage or first_not_done (None -> return False, change nothing).
    plan = [{'stage': s, 'params': params[s]} for s in order from start to end].
    start_stage(first, keep_plan=True) (409s propagate), then run.run_all_plan = plan[1:]. Return True."""
    raise NotImplementedError("not implemented")

async def advance_plan(
    session: AsyncSession, queue: JobQueue, events: EventBus, run: IngestRunRow | QueryRunRow
) -> None:
    """Called after a stage of `run` reported done. Empty plan -> nothing. Else pop the first entry,
    start_stage(entry, keep_plan=True), save the rest. If start_stage raises AppError, clear the plan."""
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
