"""Worker callbacks (contracts/openapi/internal.yaml)."""

from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.events import EventBus
from rag_api.queue import JobQueue
from rag_api.schemas.system import StageResult, StageStarted


async def record_started(session: AsyncSession, body: StageStarted) -> None:
    """404 STAGE_RUN_NOT_FOUND. Only when status == 'queued': status 'running', started_at."""
    raise NotImplementedError("not implemented")


async def record_result(
    session: AsyncSession, queue: JobQueue, events: EventBus, body: StageResult
) -> None:
    """404 STAGE_RUN_NOT_FOUND. If status already done/failed/stale: return (duplicate).
    Else set status, artifact_key, summary, error, started_at (if None), finished_at; flush.
    done -> run_all.advance_plan(run); failed -> run.run_all_plan = []. Publish run.updated
    reason 'stage_result'."""
    raise NotImplementedError("not implemented")
