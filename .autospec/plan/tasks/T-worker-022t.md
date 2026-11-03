---
id: T-worker-022t
kind: test
feature: F-chunk
title: 'Write tests: chunk job'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_chunk_job.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_chunk_job.py && uv run --frozen ruff check tests/unit/test_chunk_job.py && uv run --frozen pytest -q --collect-only tests/unit/test_chunk_job.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_chunk_job.py
max_attempts: 3
---

## Goal
Write unit tests for: chunk job. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-022 implements it.

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

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. parse artifact FIXTURES/artifact_parse.json stored at the payload's parse_artifact_key; chunk(ctx, FIXTURES/jobs__chunk.json payload) → done; artifact validates artifacts/chunk.schema.json; artifact.source_text == parse full_text; parse_strategy copied
2. summary == {'stage': 'chunk', 'chunks': n, 'min_chars', 'max_chars', 'mean_chars'} consistent with artifact.stats
3. doc_ids '<file_id>:00000'…; stats from viz.stats.chunk_stats
4. structure strategy: docling JSON read from the parse artifact's docling_json_key
5. missing parse artifact → failed ARTIFACT_NOT_FOUND

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
