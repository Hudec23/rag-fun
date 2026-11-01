from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.models import IngestRunRow
from rag_api.events import EventBus
from rag_api.queue import JobQueue
from rag_api.schemas.runs import (
    BatchIngestRequest,
    IngestRunCreate,
    IngestRunList,
    IngestRunOut,
    IngestRunPage,
)


async def load_ingest_run(session: AsyncSession, run_id: str) -> IngestRunRow:
    """404 RUN_NOT_FOUND (details.run_id)."""
    raise NotImplementedError("not implemented")


async def ingest_run_out(session: AsyncSession, run_id: str) -> IngestRunOut:
    """Run + its file + latest row per stage (None if never run) + run_all_pending = plan stages."""
    raise NotImplementedError("not implemented")


async def create_ingest_run(session: AsyncSession, body: IngestRunCreate) -> IngestRunOut:
    """404 FILE_NOT_FOUND / COLLECTION_NOT_FOUND (file checked first). Insert, flush, return out."""
    raise NotImplementedError("not implemented")


async def list_ingest_runs(
    session: AsyncSession, limit: int, offset: int, file_id: str | None, collection_id: str | None
) -> IngestRunPage:
    """Order created_at desc, id desc."""
    raise NotImplementedError("not implemented")


async def ingest_batch(
    session: AsyncSession,
    queue: JobQueue,
    events: EventBus,
    batch_id: str,
    body: BatchIngestRequest,
) -> IngestRunList:
    """404 BATCH_NOT_FOUND then COLLECTION_NOT_FOUND. For each file of the batch (upload order):
    create run, run_all.start_run_all(run, from_stage='parse', params=body.params dumped)."""
    raise NotImplementedError("not implemented")
