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
