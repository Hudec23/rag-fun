"""Run-all plans (R-013): start stages one after another as each reports done."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.catalog import INGEST_STAGES, QUERY_STAGES
from rag_api.db.models import IngestRunRow, QueryRunRow
from rag_api.errors import AppError
from rag_api.events import EventBus
from rag_api.queue import JobQueue
from rag_api.services import stages


def first_not_done(order: list[str], latest_status: dict[str, str]) -> str | None:
    """First stage in `order` whose latest status (missing = never run) is not 'done'; None if all done."""
    for stage in order:
        if latest_status.get(stage) != "done":
            return stage
    return None


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
    order = INGEST_STAGES if isinstance(run, IngestRunRow) else QUERY_STAGES
    latest = await stages.latest_rows(session, run.id)
    latest_status = {stage: row.status for stage, row in latest.items()}
    start = from_stage if from_stage is not None else first_not_done(order, latest_status)
    if start is None:
        return False
    plan: list[dict[str, Any]] = [
        {"stage": s, "params": params[s]} for s in order[order.index(start) :]
    ]
    first = plan[0]
    await stages.start_stage(
        session, queue, events, run, first["stage"], first["params"], keep_plan=True
    )
    run.run_all_plan = plan[1:]
    await session.flush()
    return True


async def advance_plan(
    session: AsyncSession, queue: JobQueue, events: EventBus, run: IngestRunRow | QueryRunRow
) -> None:
    """Called after a stage of `run` reported done. Empty plan -> nothing. Else pop the first entry,
    start_stage(entry, keep_plan=True), save the rest. If start_stage raises AppError, clear the plan."""
    plan = run.run_all_plan
    if not plan:
        return
    entry, rest = plan[0], plan[1:]
    try:
        await stages.start_stage(
            session, queue, events, run, entry["stage"], entry["params"], keep_plan=True
        )
    except AppError:
        run.run_all_plan = []
        await session.flush()
        return
    run.run_all_plan = rest
    await session.flush()
