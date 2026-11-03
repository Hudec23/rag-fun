---
id: T-worker-027t
kind: test
feature: F-store
title: 'Write tests: store job'
service: worker
depends_on: []
edit:
- services/worker/tests/integration/test_store_job.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_store_job.py && uv run --frozen ruff check tests/integration/test_store_job.py && uv run --frozen pytest -q --collect-only tests/integration/test_store_job.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/integration/test_store_job.py
max_attempts: 3
---

## Goal
Write unit tests for: store job. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-027 implements it.

## Context
Always: run Haystack pipelines and other CPU work with `await asyncio.to_thread(...)`; read inputs with `ctx['store'].get_json(ctx['settings'].s3_bucket_artifacts, key)` / `get_bytes(ctx['settings'].s3_bucket_uploads, key)`; never call ctx['api'] or ctx['events'] directly except via `rep` (StageReporter); raise WorkerError for expected failures; return (artifact dict, summary dict). Recipe: chunk = get_json(chunk_artifact_key); emb = get_json(embed_artifact_key); client = QdrantClient(url=ctx['qdrant_url']); deleted = to_thread(qdrant_admin.delete_file_points, client, qdrant_name, file_id) BEFORE writing; ds = qdrant_admin.document_store(ctx['qdrant_url'], qdrant_name, dims) (creates the collection + indexes); docs = pipelines.store.documents_for_store(chunk, emb, meta_base, ids.to_iso(ids.utcnow())) with meta_base from job.file (file_id, batch_id, batch_name, filename, mime, tags) + ingest_run_id = job.run_id, dense_model, sparse_model, parse_strategy, chunk_strategy; run build_store_pipeline(ds) in to_thread; artifact point_ids = [convert_id(d.id) for d in docs] (from haystack_integrations.document_stores.qdrant.converters import convert_id); payload_sample = the payload of chunk 0 as written (= docs[0].to_dict(flatten=False) without embedding/sparse_embedding); vector_config dense_name 'text-dense', dense_size dims, distance 'Cosine', sparse_name 'text-sparse', sparse_modifier 'idf'. Any qdrant_client / connection exception → WorkerError('QDRANT_ERROR'). Integration test against qdrant-test (QDRANT_URL); use collection 'rf_' + uuid4().hex and delete it afterwards. Use the embed fixture (384 dims) and a collection ref with dims 384.

Stub in `services/worker/src/rag_worker/jobs/store.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from rag_worker.contracts_gen.jobs.store_schema import JobPayloadStore
from rag_worker.report import StageReporter, run_stage


async def store_body(
    job: JobPayloadStore, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/store.schema.json and the store summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. store(ctx, payload) with chunk + embed fixtures → done; Qdrant collection payload.qdrant_name exists with 4 points; artifact validates artifacts/store.schema.json; points_deleted 0
2. point_ids == [qdrant convert_id(doc_id)] in chunk order; payload_sample validates qdrant/payload.schema.json and meta.tags == payload file tags
3. running store twice → second artifact points_deleted 4, collection still 4 points
4. summary {'stage': 'store', 'points_written': 4, 'points_deleted': 0, 'qdrant_collection': name}
5. Qdrant unreachable (ctx['qdrant_url'] = 'http://127.0.0.1:1') → failed QDRANT_ERROR

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
