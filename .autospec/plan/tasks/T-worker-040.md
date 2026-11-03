---
id: T-worker-040
kind: impl
feature: F-collections
title: maintenance jobs drop_collection + delete_points
service: worker
depends_on:
- T-worker-040t
- T-worker-011
edit:
- services/worker/src/rag_worker/jobs/maintenance.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/integration/test_maintenance_jobs.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/jobs/maintenance.py && uv run --frozen ruff check src/rag_worker/jobs/maintenance.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/integration/test_maintenance_jobs.py
max_attempts: 3
---

## Goal
Implement: maintenance jobs drop_collection + delete_points. The tests written by T-worker-040t define done.

## Context
Integration test against qdrant-test (QDRANT_URL); use collection 'rf_' + uuid4().hex and delete it afterwards.

Stub in `services/worker/src/rag_worker/jobs/maintenance.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Utility jobs without callbacks or events (contracts/jobs/drop_collection, delete_points)."""
from typing import Any


async def drop_collection(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Validate JobPayloadDropCollection; asyncio.to_thread(qdrant_admin.drop_collection,
    QdrantClient(url=ctx['qdrant_url']), name) -> {'status': 'done'}. Errors -> log, {'status': 'failed'}."""
    raise NotImplementedError("not implemented")

async def delete_points(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Validate JobPayloadDeletePoints; qdrant_admin.delete_file_points -> {'status': 'done',
    'deleted': n}. Errors -> log, {'status': 'failed'}."""
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
