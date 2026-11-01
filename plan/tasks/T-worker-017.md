---
id: T-worker-017
kind: impl
feature: F-parse
title: parse job
service: worker
depends_on:
- T-worker-017t
- T-worker-009
- T-worker-016
edit:
- services/worker/src/rag_worker/jobs/parse.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/integration/test_parse_job.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/jobs/parse.py && uv run --frozen ruff check src/rag_worker/jobs/parse.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/integration/test_parse_job.py
max_attempts: 3
---

## Goal
Implement: parse job. The tests written by T-worker-017t define done.

## Context
Use `ctx` (FakeObjectStore) and call `await parse(ctx, payload)` from rag_worker.jobs.parse.

Stub in `services/worker/src/rag_worker/jobs/parse.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from rag_worker.contracts_gen.jobs.parse_schema import JobPayloadParse
from rag_worker.report import StageReporter, run_stage


async def parse_body(
    job: JobPayloadParse, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/parse.schema.json and the parse summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
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
