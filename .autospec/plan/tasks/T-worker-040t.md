---
id: T-worker-040t
kind: test
feature: F-collections
title: 'Write tests: maintenance jobs drop_collection + delete_points'
service: worker
depends_on: []
edit:
- services/worker/tests/integration/test_maintenance_jobs.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_maintenance_jobs.py && uv run --frozen ruff check tests/integration/test_maintenance_jobs.py && uv run --frozen pytest -q --collect-only tests/integration/test_maintenance_jobs.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/integration/test_maintenance_jobs.py
max_attempts: 3
---

## Goal
Write unit tests for: maintenance jobs drop_collection + delete_points. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-040 implements it.

## Context
Integration test against qdrant-test (QDRANT_URL); use collection 'rf_' + uuid4().hex and delete it afterwards.

Stub in `services/worker/src/rag_worker/jobs/maintenance.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Utility jobs without callbacks or events (contracts/jobs/drop_collection, delete_points)."""
from typing import Any


async def drop_collection(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Validate JobPayloadDropCollection; asyncio.to_thread(qdrant_admin.drop_collection,
    QdrantClient(url=ctx['qdrant_url']), name) -> {'status': 'done'}. Errors -> log, {'status': 'failed'}."""
    raise NotImplementedError("not implemented")

async def delete_points(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Validate JobPayloadDeletePoints; qdrant_admin.delete_file_points -> {'status': 'done',
    'deleted': n}. Errors -> log, {'status': 'failed'}."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. delete_points(ctx, {'qdrant_name': n, 'file_id': f}) on a seeded collection → {'status': 'done', 'deleted': k}; no api/events calls
2. drop_collection(ctx, {'qdrant_name': n}) → collection gone, {'status': 'done'}
3. invalid payload → {'status': 'failed'} without raising
4. Qdrant unreachable → {'status': 'failed'}

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
