---
id: T-api-013t
kind: test
feature: F-stage-flow
title: 'Write tests: stage state machine (latest/active/downstream/check/stale/start_stage)'
service: api
depends_on: []
edit:
- services/api/tests/integration/test_stages.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_stages.py && uv run --frozen ruff check tests/integration/test_stages.py && uv run --frozen pytest -q --collect-only tests/integration/test_stages.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_stages.py
max_attempts: 3
---

## Goal
Write unit tests for: stage state machine (latest/active/downstream/check/stale/start_stage). Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-013 implements it.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test). Create runs by inserting FileRow/BatchRow/IngestRunRow/QueryRunRow/StageRunRow directly.

Stub in `services/api/src/rag_api/services/stages.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Stage state machine (R-013). Rules: contracts/openapi/api.yaml info.description 'Stage rules'."""
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.db.models import IngestRunRow, QueryRunRow, StageRunRow
from rag_api.events import EventBus
from rag_api.queue import JobQueue
from rag_api.schemas.runs import StageRunOut
Run = IngestRunRow | QueryRunRow


def run_kind_of(run: Run) -> str:
    return "ingest" if isinstance(run, IngestRunRow) else "query"

def stage_run_out(row: StageRunRow) -> StageRunOut:
    """Row -> DTO; timestamps via ids.to_iso (None stays None)."""
    raise NotImplementedError("not implemented")

async def latest_rows(session: AsyncSession, run_id: str) -> dict[str, StageRunRow]:
    """{stage: row with the highest version} for every stage that has at least one row."""
    raise NotImplementedError("not implemented")

def active_row(latest: dict[str, StageRunRow], stage: str) -> StageRunRow | None:
    """latest[stage] if its status is 'done', else None."""
    raise NotImplementedError("not implemented")

def downstream_of(stage: str) -> list[str]:
    """Stages after `stage` in its pipeline order (catalog.INGEST_STAGES / QUERY_STAGES).
    'chunk' -> ['embed', 'store']; 'generate' -> []; 'transform' -> ['retrieve', 'rerank', 'generate']."""
    raise NotImplementedError("not implemented")

def check_can_start(latest: dict[str, StageRunRow], stage: str) -> None:
    """latest[stage].status in (queued, running) -> AppError('STAGE_ALREADY_RUNNING', details={'stage'}).
    Required upstream (catalog.REQUIRED_UPSTREAM) without active row ->
    AppError('STAGE_PREREQUISITE_MISSING', details={'stage': stage, 'missing': upstream})."""
    raise NotImplementedError("not implemented")

def mark_stale(latest: dict[str, StageRunRow], stage: str) -> list[str]:
    """Set status 'stale' on latest rows of downstream stages whose status is done or failed.
    Returns the stages changed, in pipeline order."""
    raise NotImplementedError("not implemented")

async def start_stage(
    session: AsyncSession,
    queue: JobQueue,
    events: EventBus,
    run: Run,
    stage: str,
    params: dict[str, Any],
    *,
    keep_plan: bool = False,
) -> StageRunRow:
    """1. latest = latest_rows; check_can_start. 2. Insert row: id new_id, version latest+1 (or 1),
    status queued, params, created_at utcnow. 3. mark_stale. 4. Unless keep_plan: run.run_all_plan = [].
    5. Flush. 6. payload = await job_payloads.build_payload(session, run, row, latest) — call it
    through the module (`from rag_api.services import job_payloads` at the top, then
    `job_payloads.build_payload(...)`) so tests can monkeypatch it;
    queue.enqueue(stage, payload, catalog.QUEUE_OF[stage]). 7. Publish run.updated reason
    'stage_queued' (and a second one with 'stages_stale' if mark_stale changed anything)."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. downstream_of('chunk') == ['embed', 'store']; downstream_of('store') == []; downstream_of('transform') == ['retrieve', 'rerank', 'generate']
2. latest_rows returns the highest version per stage (rows v1 done, v2 failed for parse → v2)
3. active_row: latest done → that row; latest failed/stale/queued → None
4. check_can_start('chunk') with no parse → AppError STAGE_PREREQUISITE_MISSING details {'stage': 'chunk', 'missing': 'parse'}; parse latest running → still missing
5. check_can_start('parse') when parse latest is queued → STAGE_ALREADY_RUNNING details {'stage': 'parse'}
6. check_can_start('retrieve') with nothing run → ok; 'generate' without retrieve → missing 'retrieve'
7. mark_stale('parse') with chunk done, embed failed, store queued → chunk + embed set stale, returns ['chunk', 'embed'], store untouched
8. start_stage (monkeypatch.setattr('rag_api.services.job_payloads.build_payload', fake async fn returning {'p': 1})) on an ingest run → row version 1 status queued; queue.jobs == [('parse', {'p': 1}, 'ingest')]; bus published run.updated reason 'stage_queued' with run_kind 'ingest'
9. start_stage parse again after v1 done with chunk done → version 2, chunk latest stale, bus reasons ['stage_queued', 'stages_stale']
10. start_stage clears run.run_all_plan unless keep_plan=True
11. stage_run_out formats timestamps with to_iso and keeps None

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
