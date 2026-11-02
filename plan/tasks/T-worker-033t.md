---
id: T-worker-033t
kind: test
feature: F-retrieve
title: 'Write tests: retrieve job'
service: worker
depends_on: []
edit:
- services/worker/tests/integration/test_retrieve_job.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_retrieve_job.py && uv run --frozen ruff check tests/integration/test_retrieve_job.py && uv run --frozen pytest -q --collect-only tests/integration/test_retrieve_job.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/integration/test_retrieve_job.py
max_attempts: 3
---

## Goal
Write unit tests for: retrieve job. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-033 implements it.

## Context
Always: run Haystack pipelines and other CPU work with `await asyncio.to_thread(...)`; read inputs with `ctx['store'].get_json(ctx['settings'].s3_bucket_artifacts, key)` / `get_bytes(ctx['settings'].s3_bucket_uploads, key)`; never call ctx['api'] or ctx['events'] directly except via `rep` (StageReporter); raise WorkerError for expected failures; return (artifact dict, summary dict). Recipe: queries = transform artifact['queries'] if job.transform_artifact_key else [job.question]; ds = qdrant_admin.document_store(qdrant_url, qdrant_name, dims); pipe = build_retrieve_pipeline(mode, collection, ds, top_k, ctx['models']); per = run_retrieve(pipe, mode, queries, to_haystack_filters(job.params.filters)) in to_thread; per_query entries convert Documents with components.hits.to_hit(doc, rank); lists for RRF = [(qi, 'dense', docs), (qi, 'sparse', docs)] for every non-None list; fused = rrf_fuse(lists, rrf_k, top_k) → [{'hit': to_hit(doc, rank i+1, score), 'source_ranks'}]; for mode dense/sparse with ONE query fused = that list re-ranked 1..n keeping the original scores (source_ranks from that list). Integration test against qdrant-test (QDRANT_URL); use collection 'rf_' + uuid4().hex and delete it afterwards.

Stub in `services/worker/src/rag_worker/jobs/retrieve.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from rag_worker.contracts_gen.jobs.retrieve_schema import JobPayloadRetrieve
from rag_worker.report import StageReporter, run_stage


async def retrieve_body(
    job: JobPayloadRetrieve, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/retrieve.schema.json and the retrieve summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. with a seeded collection and transform_artifact_key None → per_query has 1 entry with query == question; artifact validates artifacts/retrieve.schema.json
2. with a transform artifact (multi_query, 3 queries) → per_query length 3; fused deduplicated by doc_id
3. fused hits ranks 1..n and source_ranks set; summary {'stage': 'retrieve', 'queries': n, 'hits': len(fused)}
4. mode dense → fused == dense list re-ranked, sparse None
5. collection never stored (document_store creates it empty) → status done, per_query[0].dense == [] and fused == []

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
