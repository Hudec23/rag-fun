"""Ingest runs (R-013): create runs per file/collection, batch ingest, stage progress."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.models import BatchRow, FileRow, IngestRunRow, StageRunRow
from rag_api.errors import AppError
from rag_api.events import EventBus
from rag_api.ids import new_id, to_iso, utcnow
from rag_api.queue import JobQueue
from rag_api.schemas.base import PageInfo
from rag_api.schemas.runs import (
    BatchIngestRequest,
    IngestRunCreate,
    IngestRunList,
    IngestRunOut,
    IngestRunPage,
    IngestStages,
    StageRunOut,
)
from rag_api.services import collections, files, run_all, stages
from rag_api.services.batches import file_out


def _stage_out(row: StageRunRow | None) -> StageRunOut | None:
    """A stage's latest row -> DTO; None if the stage never ran."""
    if row is None:
        return None
    return stages.stage_run_out(row)


async def run_out_for(session: AsyncSession, row: IngestRunRow) -> IngestRunOut:
    """Run + its file + latest row per stage (None if never run) + run_all_pending = plan stages."""
    file = await files.load_file(session, row.file_id)
    latest = await stages.latest_rows(session, row.id)
    return IngestRunOut(
        id=row.id,
        file=file_out(file),
        collection_id=row.collection_id,
        created_at=to_iso(row.created_at),
        run_all_pending=[entry["stage"] for entry in row.run_all_plan],
        stages=IngestStages(
            parse=_stage_out(latest.get("parse")),
            chunk=_stage_out(latest.get("chunk")),
            embed=_stage_out(latest.get("embed")),
            store=_stage_out(latest.get("store")),
        ),
    )


async def load_ingest_run(session: AsyncSession, run_id: str) -> IngestRunRow:
    """404 RUN_NOT_FOUND (details.run_id)."""
    row = await session.get(IngestRunRow, run_id)
    if row is None:
        raise AppError("RUN_NOT_FOUND", details={"run_id": run_id})
    return row


async def ingest_run_out(session: AsyncSession, run_id: str) -> IngestRunOut:
    """Run + its file + latest row per stage (None if never run) + run_all_pending = plan stages."""
    return await run_out_for(session, await load_ingest_run(session, run_id))


async def create_ingest_run(session: AsyncSession, body: IngestRunCreate) -> IngestRunOut:
    """404 FILE_NOT_FOUND / COLLECTION_NOT_FOUND (file checked first). Insert, flush, return out."""
    await files.load_file(session, body.file_id)
    await collections.load_collection(session, body.collection_id)
    row = IngestRunRow(
        id=new_id(),
        file_id=body.file_id,
        collection_id=body.collection_id,
        run_all_plan=[],
        created_at=utcnow(),
    )
    session.add(row)
    await session.flush()
    return await run_out_for(session, row)


async def list_ingest_runs(
    session: AsyncSession, limit: int, offset: int, file_id: str | None, collection_id: str | None
) -> IngestRunPage:
    """Order created_at desc, id desc."""
    stmt = select(IngestRunRow)
    count_stmt = select(func.count()).select_from(IngestRunRow)
    if file_id is not None:
        stmt = stmt.where(IngestRunRow.file_id == file_id)
        count_stmt = count_stmt.where(IngestRunRow.file_id == file_id)
    if collection_id is not None:
        stmt = stmt.where(IngestRunRow.collection_id == collection_id)
        count_stmt = count_stmt.where(IngestRunRow.collection_id == collection_id)
    total = await session.scalar(count_stmt)
    rows = (
        await session.scalars(
            stmt.order_by(IngestRunRow.created_at.desc(), IngestRunRow.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    items = [await run_out_for(session, row) for row in rows]
    return IngestRunPage(
        items=items,
        page=PageInfo(total=int(total or 0), limit=limit, offset=offset),
    )


async def ingest_batch(
    session: AsyncSession,
    queue: JobQueue,
    events: EventBus,
    batch_id: str,
    body: BatchIngestRequest,
) -> IngestRunList:
    """404 BATCH_NOT_FOUND then COLLECTION_NOT_FOUND. For each file of the batch (upload order):
    create run, run_all.start_run_all(run, from_stage='parse', params=body.params dumped)."""
    row = await session.get(BatchRow, batch_id)
    if row is None:
        raise AppError("BATCH_NOT_FOUND", details={"batch_id": batch_id})
    await collections.load_collection(session, body.collection_id)
    file_rows = (
        await session.scalars(
            select(FileRow)
            .where(FileRow.batch_id == batch_id)
            .order_by(FileRow.created_at.asc(), FileRow.id.asc())
        )
    ).all()
    params = body.params.model_dump(mode="json")
    items: list[IngestRunOut] = []
    for file in file_rows:
        run = IngestRunRow(
            id=new_id(),
            file_id=file.id,
            collection_id=body.collection_id,
            run_all_plan=[],
            created_at=utcnow(),
        )
        session.add(run)
        await session.flush()
        await run_all.start_run_all(session, queue, events, run, "parse", params)
        items.append(await run_out_for(session, run))
    return IngestRunList(items=items)
