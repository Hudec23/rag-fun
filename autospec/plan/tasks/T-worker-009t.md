---
id: T-worker-009t
kind: test
feature: F-stage-flow
title: 'Write tests: run_stage generic job wrapper'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_run_stage.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_run_stage.py && uv run --frozen ruff check tests/unit/test_run_stage.py && uv run --frozen pytest -q --collect-only tests/unit/test_run_stage.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_run_stage.py
max_attempts: 3
---

## Goal
Write unit tests for: run_stage generic job wrapper. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-009 implements it.

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

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. valid payload (FIXTURES/jobs__chunk.json) + body returning ({'a': 1}, {'stage': 'chunk', ...}) → returns {'status': 'done', 'summary': …}; api.results[0].status 'done'; ctx['running'] back to 0
2. body raising WorkerError('PARSE_FAILED') → {'status': 'failed', 'code': 'PARSE_FAILED'}, failed result with that code
3. body raising ValueError → failed with code INTERNAL_ERROR and details {'exception': 'ValueError'}
4. invalid payload (missing stage_run_id) → {'status': 'invalid'}, no api calls
5. ctx['running'] is 1 while the body runs (body asserts it)

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
