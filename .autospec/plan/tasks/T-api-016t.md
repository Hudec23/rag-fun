---
id: T-api-016t
kind: test
feature: F-stage-flow
title: 'Write tests: ingest runs create/get/list/batch ingest'
service: api
depends_on: []
edit:
- services/api/tests/integration/test_ingest_runs.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_ingest_runs.py && uv run --frozen ruff check tests/integration/test_ingest_runs.py && uv run --frozen pytest -q --collect-only tests/integration/test_ingest_runs.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_ingest_runs.py
max_attempts: 3
---

## Goal
Write unit tests for: ingest runs create/get/list/batch ingest. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-016 implements it.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test). Monkeypatch job_payloads.build_payload to return {}.

Stub in `services/api/src/rag_api/services/ingest_runs.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.db.models import IngestRunRow
from rag_api.events import EventBus
from rag_api.queue import JobQueue
from rag_api.schemas.runs import (
    BatchIngestRequest,
    IngestRunCreate,
    IngestRunList,
    IngestRunOut,
    IngestRunPage,
)


async def load_ingest_run(session: AsyncSession, run_id: str) -> IngestRunRow:
    """404 RUN_NOT_FOUND (details.run_id)."""
    raise NotImplementedError("not implemented")

async def ingest_run_out(session: AsyncSession, run_id: str) -> IngestRunOut:
    """Run + its file + latest row per stage (None if never run) + run_all_pending = plan stages."""
    raise NotImplementedError("not implemented")

async def create_ingest_run(session: AsyncSession, body: IngestRunCreate) -> IngestRunOut:
    """404 FILE_NOT_FOUND / COLLECTION_NOT_FOUND (file checked first). Insert, flush, return out."""
    raise NotImplementedError("not implemented")

async def list_ingest_runs(
    session: AsyncSession, limit: int, offset: int, file_id: str | None, collection_id: str | None
) -> IngestRunPage:
    """Order created_at desc, id desc."""
    raise NotImplementedError("not implemented")

async def ingest_batch(
    session: AsyncSession,
    queue: JobQueue,
    events: EventBus,
    batch_id: str,
    body: BatchIngestRequest,
) -> IngestRunList:
    """404 BATCH_NOT_FOUND then COLLECTION_NOT_FOUND. For each file of the batch (upload order):
    create run, run_all.start_run_all(run, from_stage='parse', params=body.params dumped)."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. create_ingest_run → IngestRunOut with file (FileOut), stages all None, run_all_pending []
2. create with unknown file → FILE_NOT_FOUND; known file + unknown collection → COLLECTION_NOT_FOUND
3. ingest_run_out shows latest row per stage and run_all_pending == [p['stage'] for p in plan]
4. list_ingest_runs filters by file_id and collection_id, newest first, page total
5. ingest_batch with 2 files → 2 runs, each has a queued parse stage, queue.jobs functions == ['parse', 'parse']
6. load_ingest_run(unknown) → RUN_NOT_FOUND details {'run_id'}

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
