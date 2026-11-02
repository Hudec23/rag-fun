"""Stage state machine (R-013). Rules: contracts/openapi/api.yaml info.description 'Stage rules'."""

from typing import Any, Literal, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.catalog import INGEST_STAGES, QUERY_STAGES, QUEUE_OF, REQUIRED_UPSTREAM
from rag_api.db.models import IngestRunRow, QueryRunRow, StageRunRow
from rag_api.errors import AppError
from rag_api.events import EventBus, run_updated_event
from rag_api.ids import new_id, to_iso, utcnow
from rag_api.queue import JobQueue
from rag_api.schemas.runs import Stage, StageRunOut, StageStatus
from rag_api.services import job_payloads

Run = IngestRunRow | QueryRunRow


def run_kind_of(run: Run) -> str:
    return "ingest" if isinstance(run, IngestRunRow) else "query"


def stage_run_out(row: StageRunRow) -> StageRunOut:
    """Row -> DTO; timestamps via ids.to_iso (None stays None)."""
    return StageRunOut(
        id=row.id,
        run_id=row.run_id,
        run_kind=cast(Literal["ingest", "query"], row.run_kind),
        stage=cast(Stage, row.stage),
        version=row.version,
        params=row.params,
        status=cast(StageStatus, row.status),
        artifact_key=row.artifact_key,
        summary=row.summary,
        error=row.error,
        created_at=to_iso(row.created_at),
        started_at=to_iso(row.started_at) if row.started_at is not None else None,
        finished_at=to_iso(row.finished_at) if row.finished_at is not None else None,
    )


async def latest_rows(session: AsyncSession, run_id: str) -> dict[str, StageRunRow]:
    """{stage: row with the highest version} for every stage that has at least one row."""
    rows = (await session.scalars(select(StageRunRow).where(StageRunRow.run_id == run_id))).all()
    latest: dict[str, StageRunRow] = {}
    for row in rows:
        current = latest.get(row.stage)
        if current is None or row.version > current.version:
            latest[row.stage] = row
    return latest


def active_row(latest: dict[str, StageRunRow], stage: str) -> StageRunRow | None:
    """latest[stage] if its status is 'done', else None."""
    row = latest.get(stage)
    if row is not None and row.status == "done":
        return row
    return None


def downstream_of(stage: str) -> list[str]:
    """Stages after `stage` in its pipeline order (catalog.INGEST_STAGES / catalog.QUERY_STAGES).
    'chunk' -> ['embed', 'store']; 'generate' -> []; 'transform' -> ['retrieve', 'rerank', 'generate']."""
    order = INGEST_STAGES if stage in INGEST_STAGES else QUERY_STAGES
    return order[order.index(stage) + 1 :]


def check_can_start(latest: dict[str, StageRunRow], stage: str) -> None:
    """latest[stage].status in (queued, running) -> AppError('STAGE_ALREADY_RUNNING', details={'stage'}).
    Required upstream (catalog.REQUIRED_UPSTREAM) without active row ->
    AppError('STAGE_PREREQUISITE_MISSING', details={'stage': stage, 'missing': upstream})."""
    current = latest.get(stage)
    if current is not None and current.status in ("queued", "running"):
        raise AppError("STAGE_ALREADY_RUNNING", details={"stage": stage})
    upstream = REQUIRED_UPSTREAM[stage]
    if upstream is not None and active_row(latest, upstream) is None:
        raise AppError("STAGE_PREREQUISITE_MISSING", details={"stage": stage, "missing": upstream})


def mark_stale(latest: dict[str, StageRunRow], stage: str) -> list[str]:
    """Set status 'stale' on latest rows of downstream stages whose status is done or failed.
    Returns the stages changed, in pipeline order."""
    changed: list[str] = []
    for downstream in downstream_of(stage):
        row = latest.get(downstream)
        if row is not None and row.status in ("done", "failed"):
            row.status = "stale"
            changed.append(downstream)
    return changed


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
    latest = await latest_rows(session, run.id)
    check_can_start(latest, stage)
    prior = latest.get(stage)
    row = StageRunRow(
        id=new_id(),
        run_id=run.id,
        run_kind=run_kind_of(run),
        stage=stage,
        version=prior.version + 1 if prior is not None else 1,
        params=params,
        status="queued",
        created_at=utcnow(),
    )
    session.add(row)
    stale = mark_stale(latest, stage)
    if not keep_plan:
        run.run_all_plan = []
    await session.flush()
    payload = await job_payloads.build_payload(session, run, row, latest)
    await queue.enqueue(stage, payload, QUEUE_OF[stage])
    kind = run_kind_of(run)
    ts = to_iso(utcnow())
    await events.publish(run.id, run_updated_event(run.id, kind, "stage_queued", ts))
    if stale:
        await events.publish(run.id, run_updated_event(run.id, kind, "stages_stale", ts))
    return row
