---
id: T-worker-025t
kind: test
feature: F-embed
title: 'Write tests: embed job'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_embed_job.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_embed_job.py && uv run --frozen ruff check tests/unit/test_embed_job.py && uv run --frozen pytest -q --collect-only tests/unit/test_embed_job.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_embed_job.py
max_attempts: 3
---

## Goal
Write unit tests for: embed job. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-025 implements it.

## Context
Always: run Haystack pipelines and other CPU work with `await asyncio.to_thread(...)`; read inputs with `ctx['store'].get_json(ctx['settings'].s3_bucket_artifacts, key)` / `get_bytes(ctx['settings'].s3_bucket_uploads, key)`; never call ctx['api'] or ctx['events'] directly except via `rep` (StageReporter); raise WorkerError for expected failures; return (artifact dict, summary dict). Recipe: chunk = get_json(artifacts, job.chunk_artifact_key); docs = [Document(id=c['doc_id'], content=c['text']) ...]; run the embed pipeline in batches of job.params.batch_size (one pipe.run per batch inside to_thread) calling rep.progress(done_so_far, n, f'embedding {done}/{n}') after each batch; art = pipelines.embed.embed_artifact(all docs, job.collection, repo, max_tokens) with repo/max_tokens from models.registry.TOKENIZERS[job.collection.dense.model]; summary {stage embed, chunks, dense_dims, mean_tokens (round 2), over_limit count, mean_sparse_nnz (round 2)} (0 values for 0 chunks).

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

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. chunk artifact FIXTURES/artifact_chunk.json stored; embed(ctx, jobs__embed payload with collection dense all-minilm 384) → done, artifact validates, len(chunks) == 4, doc_ids match the chunk artifact
2. summary {'stage': 'embed', 'chunks': 4, 'dense_dims': 384, 'mean_tokens' > 0, 'over_limit': 0, 'mean_sparse_nnz' > 0}
3. progress events emitted per batch (batch_size 2 → done values 2 and 4)
4. empty chunk list → done with chunks [] and similarity []

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
