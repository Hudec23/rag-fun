---
id: T-worker-009
kind: impl
feature: F-stage-flow
title: run_stage generic job wrapper
service: worker
depends_on:
- T-worker-009t
- T-worker-008
edit:
- services/worker/src/rag_worker/report.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_run_stage.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/report.py && uv run --frozen ruff check src/rag_worker/report.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_run_stage.py
max_attempts: 3
---

## Goal
Implement: run_stage generic job wrapper. The tests written by T-worker-009t define done.

## Context
Use the `ctx` fixture and JobPayloadChunk from rag_worker.contracts_gen.jobs.chunk_schema.

Stub in `services/worker/src/rag_worker/report.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Stage lifecycle: started -> progress* -> done | failed (callbacks + events + artifact)."""
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any
from rag_worker.callbacks import ApiClient
from rag_worker.publisher import EventPublisher
from rag_worker.store import ObjectStore
StageBody = Callable[
    [Any, StageReporter, dict[str, Any]], Awaitable[tuple[dict[str, Any], dict[str, Any]]]
]


async def run_stage(
    ctx: dict[str, Any], payload: dict[str, Any], model: type, body: StageBody
) -> dict[str, Any]:
    """Generic job wrapper used by every jobs/<stage>.py:
    1. job = model.model_validate(payload); invalid payload -> log error, return {'status': 'invalid'}.
    2. reporter = StageReporter(StageContext(job.stage_run_id, job.run_id, job.stage, job.version),
       ctx['api'], ctx['events'], ctx['store'], ctx['settings'].s3_bucket_artifacts).
    3. await reporter.started(); ctx['running'] += 1 (decrement in finally).
    4. artifact, summary = await body(job, reporter, ctx); await reporter.done(artifact, summary);
       return {'status': 'done', 'summary': summary}.
    5. WorkerError e -> reporter.failed(e.error_body()); any other Exception -> failed with
       WorkerError('INTERNAL_ERROR', details={'exception': type(e).__name__}).error_body();
       return {'status': 'failed', 'code': code}. Never raises."""
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
