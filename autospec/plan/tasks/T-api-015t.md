---
id: T-api-015t
kind: test
feature: F-stage-flow
title: 'Write tests: run-all plans'
service: api
depends_on: []
edit:
- services/api/tests/integration/test_run_all.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_run_all.py && uv run --frozen ruff check tests/integration/test_run_all.py && uv run --frozen pytest -q --collect-only tests/integration/test_run_all.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_run_all.py
max_attempts: 3
---

## Goal
Write unit tests for: run-all plans. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-015 implements it.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test). Monkeypatch job_payloads.build_payload to return {} so only the plan logic is tested.

Stub in `services/api/src/rag_api/services/run_all.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Run-all plans (R-013): start stages one after another as each reports done."""
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.db.models import IngestRunRow, QueryRunRow
from rag_api.events import EventBus
from rag_api.queue import JobQueue


def first_not_done(order: list[str], latest_status: dict[str, str]) -> str | None:
    """First stage in `order` whose latest status (missing = never run) is not 'done'; None if all done."""
    raise NotImplementedError("not implemented")

async def start_run_all(
    session: AsyncSession,
    queue: JobQueue,
    events: EventBus,
    run: IngestRunRow | QueryRunRow,
    from_stage: str | None,
    params: dict[str, dict[str, Any]],
) -> bool:
    """Resolve start = from_stage or first_not_done (None -> return False, change nothing).
    plan = [{'stage': s, 'params': params[s]} for s in order from start to end].
    start_stage(first, keep_plan=True) (409s propagate), then run.run_all_plan = plan[1:]. Return True."""
    raise NotImplementedError("not implemented")

async def advance_plan(
    session: AsyncSession, queue: JobQueue, events: EventBus, run: IngestRunRow | QueryRunRow
) -> None:
    """Called after a stage of `run` reported done. Empty plan -> nothing. Else pop the first entry,
    start_stage(entry, keep_plan=True), save the rest. If start_stage raises AppError, clear the plan."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. first_not_done(['parse','chunk','embed','store'], {}) == 'parse'; {'parse': 'done', 'chunk': 'failed'} → 'chunk'; all done → None
2. start_run_all(ingest run, None, params) with nothing run → returns True, queue.jobs[0][0] == 'parse', run.run_all_plan == [{'stage': 'chunk', 'params': …}, {'stage': 'embed', …}, {'stage': 'store', …}]
3. start_run_all with from_stage 'embed' (chunk done) → starts embed, plan == [store]
4. start_run_all with every stage done and from_stage None → returns False, no jobs
5. advance_plan pops the first entry and starts it (queue gets 'chunk'), plan shrinks by one
6. advance_plan with an empty plan does nothing
7. advance_plan when the next stage cannot start (prerequisite missing) → plan cleared, no exception

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
