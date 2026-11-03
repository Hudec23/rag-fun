---
id: T-worker-038
kind: impl
feature: F-generate
title: generate job with streaming
service: worker
depends_on:
- T-worker-038t
- T-worker-009
- T-worker-037
edit:
- services/worker/src/rag_worker/jobs/generate.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_generate_job.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/jobs/generate.py && uv run --frozen ruff check src/rag_worker/jobs/generate.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_generate_job.py
max_attempts: 3
---

## Goal
Implement: generate job with streaming. The tests written by T-worker-038t define done.

## Context
Always: run Haystack pipelines and other CPU work with `await asyncio.to_thread(...)`; read inputs with `ctx['store'].get_json(ctx['settings'].s3_bucket_artifacts, key)` / `get_bytes(ctx['settings'].s3_bucket_uploads, key)`; never call ctx['api'] or ctx['events'] directly except via `rep` (StageReporter); raise WorkerError for expected failures; return (artifact dict, summary dict). Recipe: src = get_json(job.context_artifact_key); hits = [a['hit'] for a in src['after']] if context_source == 'rerank' else [f['hit'] for f in src['fused']]; tok = ctx['models'].tokenizer('bge-m3'); counts = [len(tok.encode(h['content'], add_special_tokens=False).ids)]; system/question tokens likewise for prompts.ANSWER_SYSTEM and the question; included, used, dropped = select_context(hits, counts, max_context_tokens); loop = asyncio.get_running_loop(); callback(chunk) → asyncio.run_coroutine_threadsafe(ctx['events'].publish(job.run_id, generate.token event with contiguous index), loop); pipe = build_generate_pipeline(job.chat, temperature, max_answer_tokens, ctx['models'], callback); res = pipe.run({'prompt': {'context': [{'n': c['n'], 'text': c['hit']['content']} ...], 'question': q}}, include_outputs_from={'prompt'}) in to_thread; usage from replies[0].meta['usage'] (prompt_tokens/completion_tokens, None when missing); LLM exception → WorkerError('LLM_ERROR'). Streaming callbacks run in a worker thread (pipeline.run inside asyncio.to_thread): publish tokens via asyncio.run_coroutine_threadsafe(events.publish(...), loop) captured before to_thread.

Stub in `services/worker/src/rag_worker/jobs/generate.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from rag_worker.contracts_gen.jobs.generate_schema import JobPayloadGenerate
from rag_worker.report import StageReporter, run_stage


async def generate_body(
    job: JobPayloadGenerate, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/generate.schema.json and the generate summary of
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
