from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.models import BatchRow, FileRow
from rag_api.errors import AppError
from rag_api.ids import to_iso
from rag_api.schemas.base import PageInfo
from rag_api.schemas.files import BatchList, BatchOut, BatchUpdate, BatchWithFiles, FileOut
from rag_api.services.tags import normalize_tags


def batch_out(row: BatchRow, file_count: int) -> BatchOut:
    return BatchOut(
        id=row.id,
        name=row.name,
        tags=row.tags,
        file_count=file_count,
        created_at=to_iso(row.created_at),
    )


def file_out(row: FileRow) -> FileOut:
    return FileOut(
        id=row.id,
        batch_id=row.batch_id,
        filename=row.filename,
        mime=row.mime,
        size_bytes=row.size_bytes,
        sha256=row.sha256,
        tags=row.tags,
        created_at=to_iso(row.created_at),
    )


async def file_count_for(session: AsyncSession, batch_id: str) -> int:
    count = await session.scalar(
        select(func.count()).select_from(FileRow).where(FileRow.batch_id == batch_id)
    )
    return int(count or 0)


async def file_counts_for(session: AsyncSession, batch_ids: list[str]) -> dict[str, int]:
    if not batch_ids:
        return {}
    rows = (
        await session.execute(
            select(FileRow.batch_id, func.count(FileRow.id))
            .where(FileRow.batch_id.in_(batch_ids))
            .group_by(FileRow.batch_id)
        )
    ).all()
    return {batch_id: count for batch_id, count in rows}


async def list_batches(session: AsyncSession, limit: int, offset: int) -> BatchList:
    """Order created_at desc, id desc. file_count via count of files per batch. page.total = all batches."""
    total = await session.scalar(select(func.count()).select_from(BatchRow))
    rows = (
        await session.scalars(
            select(BatchRow)
            .order_by(BatchRow.created_at.desc(), BatchRow.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    counts = await file_counts_for(session, [row.id for row in rows])
    return BatchList(
        items=[batch_out(row, counts.get(row.id, 0)) for row in rows],
        page=PageInfo(total=int(total or 0), limit=limit, offset=offset),
    )


async def get_batch(session: AsyncSession, batch_id: str) -> BatchWithFiles:
    """404 BATCH_NOT_FOUND (details.batch_id). files ordered created_at asc, id asc (= upload order)."""
    row = await session.get(BatchRow, batch_id)
    if row is None:
        raise AppError("BATCH_NOT_FOUND", details={"batch_id": batch_id})
    files = (
        await session.scalars(
            select(FileRow)
            .where(FileRow.batch_id == batch_id)
            .order_by(FileRow.created_at.asc(), FileRow.id.asc())
        )
    ).all()
    return BatchWithFiles(batch=batch_out(row, len(files)), files=[file_out(f) for f in files])


async def update_batch(session: AsyncSession, batch_id: str, body: BatchUpdate) -> BatchOut:
    """404 BATCH_NOT_FOUND. Only fields that are not None change; tags normalized (sorted, unique).
    Body with neither field -> AppError('VALIDATION_ERROR', details={'field': 'body'})."""
    row = await session.get(BatchRow, batch_id)
    if row is None:
        raise AppError("BATCH_NOT_FOUND", details={"batch_id": batch_id})
    if body.name is None and body.tags is None:
        raise AppError("VALIDATION_ERROR", details={"field": "body"})
    if body.name is not None:
        row.name = body.name
    if body.tags is not None:
        row.tags = normalize_tags(body.tags)
    await session.flush()
    return batch_out(row, await file_count_for(session, batch_id))
