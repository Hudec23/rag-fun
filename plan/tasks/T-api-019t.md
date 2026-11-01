---
id: T-api-019t
kind: test
feature: F-stage-flow
title: 'Write tests: stage runs + artifact proxy + page images'
service: api
depends_on: []
edit:
- services/api/tests/integration/test_artifacts.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_artifacts.py && uv run --frozen ruff check tests/integration/test_artifacts.py && uv run --frozen pytest -q --collect-only tests/integration/test_artifacts.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_artifacts.py
max_attempts: 3
---

## Goal
Write unit tests for: stage runs + artifact proxy + page images. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-019 implements it.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test).

Stub in `services/api/src/rag_api/services/artifacts.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.config import Settings
from rag_api.s3 import ObjectStore
from rag_api.schemas.runs import StageRunList, StageRunOut


async def get_stage_run(session: AsyncSession, stage_run_id: str) -> StageRunOut:
    """404 STAGE_RUN_NOT_FOUND (details.stage_run_id)."""
    raise NotImplementedError("not implemented")

async def list_stage_runs(session: AsyncSession, run_id: str, stage: str) -> StageRunList:
    """All versions, version desc. Unknown run -> empty list."""
    raise NotImplementedError("not implemented")

async def get_artifact(
    session: AsyncSession, store: ObjectStore, settings: Settings, stage_run_id: str
) -> bytes:
    """Raw JSON bytes from bucket artifacts. 404 STAGE_RUN_NOT_FOUND; artifact_key None or object
    missing (ObjectNotFound) -> 404 ARTIFACT_NOT_FOUND (details.stage_run_id)."""
    raise NotImplementedError("not implemented")

async def get_page_image(
    session: AsyncSession, store: ObjectStore, settings: Settings, stage_run_id: str, page_no: int
) -> bytes:
    """PNG bytes. 404 STAGE_RUN_NOT_FOUND. Not a parse run, no artifact, page_no not in pages, or
    image_key None/missing -> 404 PAGE_NOT_FOUND (details.page_no). Reads the parse artifact JSON
    to find pages[].image_key."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. get_stage_run unknown → STAGE_RUN_NOT_FOUND
2. list_stage_runs returns versions desc; unknown run → empty items
3. get_artifact returns the stored bytes unchanged (store.objects[('artifacts', key)])
4. get_artifact with artifact_key None → ARTIFACT_NOT_FOUND; key set but object missing → ARTIFACT_NOT_FOUND
5. get_page_image: parse artifact (FIXTURES/artifact_parse.json) stored under the row key and b'\x89PNG' at its page 1 image_key → returns the PNG bytes
6. get_page_image page 9 / non-parse stage / image_key None → PAGE_NOT_FOUND details {'page_no': n}

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
