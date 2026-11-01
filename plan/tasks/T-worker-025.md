---
id: T-worker-025
kind: impl
feature: F-embed
title: embed job
service: worker
depends_on:
- T-worker-025t
- T-worker-009
- T-worker-024
edit:
- services/worker/src/rag_worker/jobs/embed.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_embed_job.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/jobs/embed.py && uv run --frozen ruff check src/rag_worker/jobs/embed.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_embed_job.py
max_attempts: 3
---

## Goal
Implement: embed job. The tests written by T-worker-025t define done.

## Context
Stub in `services/worker/src/rag_worker/jobs/embed.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from rag_worker.contracts_gen.jobs.embed_schema import JobPayloadEmbed
from rag_worker.report import StageReporter, run_stage


async def embed_body(
    job: JobPayloadEmbed, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/embed.schema.json and the embed summary of
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
