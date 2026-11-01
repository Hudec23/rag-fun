---
id: T-api-018t
kind: test
feature: F-stage-flow
title: 'Write tests: worker callbacks record_started + record_result'
service: api
depends_on: []
edit:
- services/api/tests/integration/test_results.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_results.py && uv run --frozen ruff check tests/integration/test_results.py && uv run --frozen pytest -q --collect-only tests/integration/test_results.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_results.py
max_attempts: 3
---

## Goal
Write unit tests for: worker callbacks record_started + record_result. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-018 implements it.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test).

Stub in `services/api/src/rag_api/services/results.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Worker callbacks (contracts/openapi/internal.yaml)."""
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.events import EventBus
from rag_api.queue import JobQueue
from rag_api.schemas.system import StageResult, StageStarted


async def record_started(session: AsyncSession, body: StageStarted) -> None:
    """404 STAGE_RUN_NOT_FOUND. Only when status == 'queued': status 'running', started_at."""
    raise NotImplementedError("not implemented")

async def record_result(
    session: AsyncSession, queue: JobQueue, events: EventBus, body: StageResult
) -> None:
    """404 STAGE_RUN_NOT_FOUND. If status already done/failed/stale: return (duplicate).
    Else set status, artifact_key, summary, error, started_at (if None), finished_at; flush.
    done -> run_all.advance_plan(run); failed -> run.run_all_plan = []. Publish run.updated
    reason 'stage_result'."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. record_started on a queued row → status running, started_at set; on a done row → unchanged
2. record_result done → status done, artifact_key, summary, finished_at stored; bus run.updated reason 'stage_result'
3. record_result failed → status failed, error stored, run.run_all_plan cleared
4. record_result for a row already done → ignored (summary unchanged, no event)
5. record_result done with a run-all plan [chunk] → chunk queued (monkeypatch job_payloads.build_payload → {}), plan []
6. unknown stage_run_id → STAGE_RUN_NOT_FOUND
7. HTTP: POST /internal/v1/stage-results without X-Internal-Token → 401 UNAUTHORIZED; with token and the contract example (tests.conftest.FIXTURES / … build from contracts/openapi/internal.yaml example) → 204

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
