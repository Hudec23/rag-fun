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
