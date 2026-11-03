---
id: T-api-019
kind: impl
feature: F-stage-flow
title: stage runs + artifact proxy + page images
service: api
depends_on:
- T-api-019t
edit:
- services/api/src/rag_api/services/artifacts.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_artifacts.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/artifacts.py && uv run --frozen ruff check src/rag_api/services/artifacts.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_artifacts.py
max_attempts: 3
---

## Goal
Implement: stage runs + artifact proxy + page images. The tests written by T-api-019t define done.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test).

Stub in `services/api/src/rag_api/services/artifacts.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.config import Settings
from rag_api.s3 import ObjectStore
from rag_api.schemas.runs import StageRunList, StageRunOut


async def get_stage_run(session: AsyncSession, stage_run_id: str) -> StageRunOut:
    """404 STAGE_RUN_NOT_FOUND (details.stage_run_id)."""
    raise NotImplementedError("not implemented")

async def list_stage_runs(session: AsyncSession, run_id: str, stage: str) -> StageRunList:
    """All versions, version desc. Unknown run -> empty list."""
    raise NotImplementedError("not implemented")

async def get_artifact(
    session: AsyncSession, store: ObjectStore, settings: Settings, stage_run_id: str
) -> bytes:
    """Raw JSON bytes from bucket artifacts. 404 STAGE_RUN_NOT_FOUND; artifact_key None or object
    missing (ObjectNotFound) -> 404 ARTIFACT_NOT_FOUND (details.stage_run_id)."""
    raise NotImplementedError("not implemented")

async def get_page_image(
    session: AsyncSession, store: ObjectStore, settings: Settings, stage_run_id: str, page_no: int
) -> bytes:
    """PNG bytes. 404 STAGE_RUN_NOT_FOUND. Not a parse run, no artifact, page_no not in pages, or
    image_key None/missing -> 404 PAGE_NOT_FOUND (details.page_no). Reads the parse artifact JSON
    to find pages[].image_key."""
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
