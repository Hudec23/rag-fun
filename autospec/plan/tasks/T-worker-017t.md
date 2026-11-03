---
id: T-worker-017t
kind: test
feature: F-parse
title: 'Write tests: parse job'
service: worker
depends_on: []
edit:
- services/worker/tests/integration/test_parse_job.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_parse_job.py && uv run --frozen ruff check tests/integration/test_parse_job.py && uv run --frozen pytest -q --collect-only tests/integration/test_parse_job.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/integration/test_parse_job.py
max_attempts: 3
---

## Goal
Write unit tests for: parse job. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-017 implements it.

## Context
Always: run Haystack pipelines and other CPU work with `await asyncio.to_thread(...)`; read inputs with `ctx['store'].get_json(ctx['settings'].s3_bucket_artifacts, key)` / `get_bytes(ctx['settings'].s3_bucket_uploads, key)`; never call ctx['api'] or ctx['events'] directly except via `rep` (StageReporter); raise WorkerError for expected failures; return (artifact dict, summary dict). Recipe: data = get_bytes(uploads, job.file.s3_key); pipe = pipelines.parse.build_parse_pipeline(job.params.strategy, job.params.model_dump()); res = run_parse(pipe, strategy, data, mime, filename) (to_thread); elements, full_text = components.text_layout.assign_spans(res['elements']); for each page_no, png in res['page_images']: put_bytes(artifacts, keys.page_image_key(job.run_id, job.version, n), png, 'image/png') + rep.progress(i, n, f'page {i}/{n}'); docling_json → put_bytes(artifacts, keys.docling_json_key(...), utf-8, 'application/json'); build the parse artifact (schema_version 1, stage parse, strategy, file_id, mime, ocr_used, pages with image_key or None, elements, full_text, docling_json_key or None); summary pages/elements/tables/pictures (type picture)/chars/ocr_used. Use `ctx` (FakeObjectStore) and call `await parse(ctx, payload)` from rag_worker.jobs.parse.

Stub in `services/worker/src/rag_worker/jobs/parse.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from rag_worker.contracts_gen.jobs.parse_schema import JobPayloadParse
from rag_worker.report import StageReporter, run_stage


async def parse_body(
    job: JobPayloadParse, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/parse.schema.json and the parse summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. ctx store has uploads/<key> = handbook.md bytes; parse({payload from FIXTURES/jobs__parse.json with mime text/markdown, strategy plain_text}) → api.results[0].status done; stored artifact validates artifacts/parse.schema.json; summary {'stage': 'parse', pages 0, elements > 0, tables 0, pictures 0, chars == len(full_text), ocr_used False}
2. docling_layout on q3-report.pdf → page PNGs stored at keys.page_image_key(run_id, version, n) and artifact pages[].image_key equal to them; docling.json stored at keys.docling_json_key and artifact docling_json_key set
3. full_text/char spans from assign_spans: every element with spans satisfies full_text[s:e] == text
4. missing upload object → failed result FILE_NOT_FOUND
5. plain_text on PNG → failed UNSUPPORTED_FOR_STRATEGY
6. reporter.progress called at least once (FakePublisher has a stage.progress event)

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
