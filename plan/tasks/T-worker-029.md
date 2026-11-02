---
id: T-worker-029
kind: impl
feature: F-transform
title: transform job
service: worker
depends_on:
- T-worker-029t
- T-worker-009
- T-worker-028
edit:
- services/worker/src/rag_worker/jobs/transform.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_transform_job.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/jobs/transform.py && uv run --frozen ruff check src/rag_worker/jobs/transform.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_transform_job.py
max_attempts: 3
---

## Goal
Implement: transform job. The tests written by T-worker-029t define done.

## Context
Always: run Haystack pipelines and other CPU work with `await asyncio.to_thread(...)`; read inputs with `ctx['store'].get_json(ctx['settings'].s3_bucket_artifacts, key)` / `get_bytes(ctx['settings'].s3_bucket_uploads, key)`; never call ctx['api'] or ctx['events'] directly except via `rep` (StageReporter); raise WorkerError for expected failures; return (artifact dict, summary dict). Recipe: strategy none → transform_artifact('none', question, None, [], None, n) without building a pipeline; else pipe = build_transform_pipeline(strategy, job.chat, ctx['models']); res = pipe.run({'prompt': {'question': q, 'n': num_queries}}, include_outputs_from={'prompt'}) in to_thread; reply = res['llm']['replies'][0].text; messages = [{'role': m.role.value, 'content': m.text} for m in res['prompt']['prompt']]; any exception from the run → WorkerError('LLM_ERROR', details={'reason': str(e)[:300]}).

Stub in `services/worker/src/rag_worker/jobs/transform.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from rag_worker.contracts_gen.jobs.transform_schema import JobPayloadTransform
from rag_worker.report import StageReporter, run_stage


async def transform_body(
    job: JobPayloadTransform, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/transform.schema.json and the transform summary of
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
