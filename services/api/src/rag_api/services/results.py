"""Worker callbacks (contracts/openapi/internal.yaml)."""

from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.models import IngestRunRow, QueryRunRow, StageRunRow
from rag_api.errors import AppError
from rag_api.events import EventBus, run_updated_event
from rag_api.ids import to_iso, utcnow
from rag_api.queue import JobQueue
from rag_api.schemas.system import StageResult, StageStarted
from rag_api.services import run_all


async def _load_stage_run(session: AsyncSession, stage_run_id: str) -> StageRunRow:
    """404 STAGE_RUN_NOT_FOUND (details.stage_run_id)."""
    row = await session.get(StageRunRow, stage_run_id)
    if row is None:
        raise AppError("STAGE_RUN_NOT_FOUND", details={"stage_run_id": stage_run_id})
    return row


async def _load_run(session: AsyncSession, row: StageRunRow) -> IngestRunRow | QueryRunRow:
    """The run of a stage row (table chosen by row.run_kind); 404 RUN_NOT_FOUND."""
    run: IngestRunRow | QueryRunRow | None
    if row.run_kind == "ingest":
        run = await session.get(IngestRunRow, row.run_id)
    else:
        run = await session.get(QueryRunRow, row.run_id)
    if run is None:
        raise AppError("RUN_NOT_FOUND", details={"run_id": row.run_id})
    return run


async def record_started(session: AsyncSession, body: StageStarted) -> None:
    """404 STAGE_RUN_NOT_FOUND. Only when status == 'queued': status 'running', started_at."""
    row = await _load_stage_run(session, body.stage_run_id)
    if row.status != "queued":
        return
    row.status = "running"
    row.started_at = utcnow()
    await session.flush()


async def record_result(
    session: AsyncSession, queue: JobQueue, events: EventBus, body: StageResult
) -> None:
    """404 STAGE_RUN_NOT_FOUND. If status already done/failed/stale: return (duplicate).
    Else set status, artifact_key, summary, error, started_at (if None), finished_at; flush.
    done -> run_all.advance_plan(run); failed -> run.run_all_plan = []. Publish run.updated
    reason 'stage_result'."""
    row = await _load_stage_run(session, body.stage_run_id)
    if row.status in ("done", "failed", "stale"):
        return
    row.status = body.status
    row.artifact_key = body.artifact_key
    row.summary = body.summary.model_dump(mode="json") if body.summary is not None else None
    row.error = body.error.model_dump(mode="json") if body.error is not None else None
    if row.started_at is None:
        row.started_at = utcnow()
    row.finished_at = utcnow()
    await session.flush()
    run = await _load_run(session, row)
    if body.status == "done":
        await run_all.advance_plan(session, queue, events, run)
    else:
        run.run_all_plan = []
        await session.flush()
    kind = "ingest" if isinstance(run, IngestRunRow) else "query"
    await events.publish(run.id, run_updated_event(run.id, kind, "stage_result", to_iso(utcnow())))
