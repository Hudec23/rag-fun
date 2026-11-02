---
id: T-worker-022
kind: impl
feature: F-chunk
title: chunk job
service: worker
depends_on:
- T-worker-022t
- T-worker-001
- T-worker-009
- T-worker-021
edit:
- services/worker/src/rag_worker/jobs/chunk.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_chunk_job.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/jobs/chunk.py && uv run --frozen ruff check src/rag_worker/jobs/chunk.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_chunk_job.py
max_attempts: 3
---

## Goal
Implement: chunk job. The tests written by T-worker-022t define done.

## Context
Always: run Haystack pipelines and other CPU work with `await asyncio.to_thread(...)`; read inputs with `ctx['store'].get_json(ctx['settings'].s3_bucket_artifacts, key)` / `get_bytes(ctx['settings'].s3_bucket_uploads, key)`; never call ctx['api'] or ctx['events'] directly except via `rep` (StageReporter); raise WorkerError for expected failures; return (artifact dict, summary dict). Recipe: parse = get_json(artifacts, job.parse_artifact_key); docling_json = get_bytes(artifacts, parse['docling_json_key']).decode() when the key is set else None; pipe = pipelines.chunk.build_chunk_pipeline(strategy, job.params.model_dump(), ctx['models'], job.dense); out = run_chunk(pipe, strategy, parse, docling_json, job.file.file_id) (to_thread); stats = viz.stats.chunk_stats([c['char_count'] for c in chunks]); artifact {schema_version 1, stage chunk, strategy, params (model_dump), parse_strategy = parse['strategy'], source_text = parse['full_text'], chunks, stats, semantic = out['semantic']}; summary {stage, chunks, min_chars, max_chars, mean_chars} from stats. Use `ctx` and put fixtures into ctx['store'] with put_json.

Stub in `services/worker/src/rag_worker/jobs/chunk.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from rag_worker.contracts_gen.jobs.chunk_schema import JobPayloadChunk
from rag_worker.report import StageReporter, run_stage


async def chunk_body(
    job: JobPayloadChunk, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/chunk.schema.json and the chunk summary of
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
