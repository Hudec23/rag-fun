---
id: T-api-025
kind: impl
feature: F-pipeline-graph
title: pipeline graph store
service: api
depends_on:
- T-api-025t
edit:
- services/api/src/rag_api/services/pipeline_graphs.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_pipeline_graphs_service.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/pipeline_graphs.py && uv run --frozen ruff check src/rag_api/services/pipeline_graphs.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_pipeline_graphs_service.py
max_attempts: 3
---

## Goal
Implement: pipeline graph store. The tests written by T-api-025t define done.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test). Graph fixture: tests.conftest.FIXTURES / 'shared__pipeline-graph.json' (stage chunk, variant fixed); copy and change stage/variant for others.

Stub in `services/api/src/rag_api/services/pipeline_graphs.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.schemas.system import PipelineGraphList


async def put_graph(session: AsyncSession, stage: str, variant: str, graph: dict[str, Any]) -> None:
    """graph['stage'] != stage or graph['variant'] != variant -> VALIDATION_ERROR
    (details.field='stage' or 'variant'). Upsert row, updated_at utcnow."""
    raise NotImplementedError("not implemented")

async def list_graphs(session: AsyncSession) -> PipelineGraphList:
    """Order: stage pipeline order (parse, chunk, embed, store, transform, retrieve, rerank,
    generate), then variant ascending."""
    raise NotImplementedError("not implemented")

async def get_graph(session: AsyncSession, stage: str, variant: str) -> dict[str, Any]:
    """404 PIPELINE_GRAPH_NOT_FOUND (details.stage, details.variant)."""
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
