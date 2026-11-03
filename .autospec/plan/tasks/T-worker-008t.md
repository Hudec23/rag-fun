---
id: T-worker-008t
kind: test
feature: F-stage-flow
title: 'Write tests: StageReporter lifecycle'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_reporter.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_reporter.py && uv run --frozen ruff check tests/unit/test_reporter.py && uv run --frozen pytest -q --collect-only tests/unit/test_reporter.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_reporter.py
max_attempts: 3
---

## Goal
Write unit tests for: StageReporter lifecycle. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-008 implements it.

## Context
Use the `ctx` fixture's FakeApi/FakePublisher/FakeObjectStore and a fake clock `lambda: t[0]`.

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


@dataclass
class StageContext:
    stage_run_id: str
    run_id: str
    stage: str
    version: int

class StageReporter:
    """Event JSON: contracts/events/stage.*.schema.json; ts = ids.to_iso(ids.utcnow())."""

    def __init__(
        self,
        ctx: StageContext,
        api: ApiClient,
        events: EventPublisher,
        store: ObjectStore,
        artifacts_bucket: str,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.ctx = ctx
        self.api = api
        self.events = events
        self.store = store
        self.artifacts_bucket = artifacts_bucket
        self.clock = clock  # monotonic seconds; None -> time.monotonic
        self.started_at: str | None = None

    async def started(self) -> None:
        """Remember started_at; api.stage_started; publish stage.started."""
        raise NotImplementedError("not implemented")

    async def progress(self, done: int, total: int, message: str) -> None:
        """Publish stage.progress, at most one per 0.2 s (clock); the final one (done == total) is
        always sent. done is clamped to [0, total]; total < 1 -> nothing sent."""
        raise NotImplementedError("not implemented")

    async def done(self, artifact: dict[str, Any], summary: dict[str, Any]) -> str:
        """put_json(artifacts bucket, keys.artifact_key(...), artifact); api.stage_result(status done,
        artifact_key, summary, error None, started_at, finished_at); THEN publish stage.completed.
        Returns the artifact key."""
        raise NotImplementedError("not implemented")

    async def failed(self, error_body: dict[str, Any]) -> None:
        """api.stage_result(status failed, artifact_key None, summary None, error=error_body); then
        publish stage.failed. If the callback still fails after retries, log and still publish."""
        raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. started() → api.started == [(stage_run_id, '2026-11-01T18:22:05.123Z')] (frozen_now) and one stage.started event that validates against contracts events/stage.started.schema.json
2. progress(1, 4, 'm') then progress(2, 4, 'm') within 0.1 s (fake clock) → only the first published; progress(4, 4, 'm') always published
3. progress(9, 4, 'm') → done clamped to 4; progress(0, 0, 'm') → nothing published
4. done(artifact, summary) → artifact stored at '<run_id>/<stage>/v<version>.json' in the artifacts bucket, api.results[0] == {stage_run_id, 'status': 'done', artifact_key, summary, 'error': None, started_at, finished_at}, returns the key
5. ordering: api.calls ends with ['result', 'stage.completed'] (callback before event)
6. failed(error_body) → result status failed with error, artifact_key None, summary None; then stage.failed event with the same error
7. failed when api.fail_results is True → no exception, stage.failed still published

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
