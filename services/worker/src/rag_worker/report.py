"""Stage lifecycle: started -> progress* -> done | failed (callbacks + events + artifact)."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from rag_worker.callbacks import ApiClient
from rag_worker.publisher import EventPublisher
from rag_worker.store import ObjectStore


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
