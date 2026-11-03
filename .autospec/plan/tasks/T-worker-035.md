---
id: T-worker-035
kind: impl
feature: F-rerank
title: rerank job
service: worker
depends_on:
- T-worker-035t
- T-worker-009
- T-worker-034
edit:
- services/worker/src/rag_worker/jobs/rerank.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_rerank_job.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/jobs/rerank.py && uv run --frozen ruff check src/rag_worker/jobs/rerank.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_rerank_job.py
max_attempts: 3
---

## Goal
Implement: rerank job. The tests written by T-worker-035t define done.

## Context
Always: run Haystack pipelines and other CPU work with `await asyncio.to_thread(...)`; read inputs with `ctx['store'].get_json(ctx['settings'].s3_bucket_artifacts, key)` / `get_bytes(ctx['settings'].s3_bucket_uploads, key)`; never call ctx['api'] or ctx['events'] directly except via `rep` (StageReporter); raise WorkerError for expected failures; return (artifact dict, summary dict). Recipe: ret = get_json(retrieve_artifact_key); before = [f['hit'] for f in ret['fused']]; enabled → pipe = build_rerank_pipeline(job.model, top_n, ctx['models']); docs = pipe.run({'ranker': {'query': job.question, 'documents': [hit_to_document(h) for h in before]}})['ranker']['documents'] in to_thread; art = rerank_artifact(enabled, model or None, top_n, question, before, docs or None).

Stub in `services/worker/src/rag_worker/jobs/rerank.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from rag_worker.contracts_gen.jobs.rerank_schema import JobPayloadRerank
from rag_worker.report import StageReporter, run_stage


async def rerank_body(
    job: JobPayloadRerank, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/rerank.schema.json and the rerank summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
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
