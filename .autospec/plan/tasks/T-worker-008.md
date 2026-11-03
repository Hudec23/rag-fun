---
id: T-worker-008
kind: impl
feature: F-stage-flow
title: StageReporter lifecycle
service: worker
depends_on:
- T-worker-008t
- T-worker-005
- T-worker-006
- T-worker-007
edit:
- services/worker/src/rag_worker/report.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_reporter.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/report.py && uv run --frozen ruff check src/rag_worker/report.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_reporter.py
max_attempts: 3
---

## Goal
Implement: StageReporter lifecycle. The tests written by T-worker-008t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
