"""Stage lifecycle: started -> progress* -> done | failed (callbacks + events + artifact)."""

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import structlog

from rag_worker.callbacks import ApiClient
from rag_worker.ids import to_iso, utcnow
from rag_worker.keys import artifact_key
from rag_worker.publisher import EventPublisher
from rag_worker.store import ObjectStore

log = structlog.get_logger()


@dataclass
class StageContext:
    stage_run_id: str
    run_id: str
    stage: str
    version: int


class StageReporter:
    """Event JSON: contracts/events/stage.*.schema.json; ts = ids.to_iso(ids.utcnow())."""

    _last_progress: float | None = None

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

    def _now(self) -> float:
        return self.clock() if self.clock is not None else time.monotonic()

    def _event(self, event_type: str, ts: str) -> dict[str, Any]:
        return {
            "type": event_type,
            "run_id": self.ctx.run_id,
            "stage_run_id": self.ctx.stage_run_id,
            "stage": self.ctx.stage,
            "version": self.ctx.version,
            "ts": ts,
        }

    async def started(self) -> None:
        """Remember started_at; api.stage_started; publish stage.started."""
        ts = to_iso(utcnow())
        self.started_at = ts
        await self.api.stage_started(self.ctx.stage_run_id, ts)
        await self.events.publish(self.ctx.run_id, self._event("stage.started", ts))

    async def progress(self, done: int, total: int, message: str) -> None:
        """Publish stage.progress, at most one per 0.2 s (clock); the final one (done == total) is
        always sent. done is clamped to [0, total]; total < 1 -> nothing sent."""
        if total < 1:
            return
        now = self._now()
        clamped = min(max(0, done), total)
        last = self._last_progress
        if clamped != total and last is not None and now - last < 0.2:
            return
        self._last_progress = now
        event = self._event("stage.progress", to_iso(utcnow()))
        event["done"] = clamped
        event["total"] = total
        event["message"] = message
        await self.events.publish(self.ctx.run_id, event)

    async def done(self, artifact: dict[str, Any], summary: dict[str, Any]) -> str:
        """put_json(artifacts bucket, keys.artifact_key(...), artifact); api.stage_result(status done,
        artifact_key, summary, error None, started_at, finished_at); THEN publish stage.completed.
        Returns the artifact key."""
        key = artifact_key(self.ctx.run_id, self.ctx.stage, self.ctx.version)
        await self.store.put_json(self.artifacts_bucket, key, artifact)
        finished_at = to_iso(utcnow())
        await self.api.stage_result(
            {
                "stage_run_id": self.ctx.stage_run_id,
                "status": "done",
                "artifact_key": key,
                "summary": summary,
                "error": None,
                "started_at": self.started_at,
                "finished_at": finished_at,
            }
        )
        event = self._event("stage.completed", finished_at)
        event["artifact_key"] = key
        event["summary"] = summary
        await self.events.publish(self.ctx.run_id, event)
        return key

    async def failed(self, error_body: dict[str, Any]) -> None:
        """api.stage_result(status failed, artifact_key None, summary None, error=error_body); then
        publish stage.failed. If the callback still fails after retries, log and still publish."""
        finished_at = to_iso(utcnow())
        try:
            await self.api.stage_result(
                {
                    "stage_run_id": self.ctx.stage_run_id,
                    "status": "failed",
                    "artifact_key": None,
                    "summary": None,
                    "error": error_body,
                    "started_at": self.started_at,
                    "finished_at": finished_at,
                }
            )
        except Exception as e:  # noqa: BLE001
            log.warning(
                "stage_result callback failed",
                stage_run_id=self.ctx.stage_run_id,
                error=str(e)[:300],
            )
        event = self._event("stage.failed", finished_at)
        event["error"] = error_body
        await self.events.publish(self.ctx.run_id, event)


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
