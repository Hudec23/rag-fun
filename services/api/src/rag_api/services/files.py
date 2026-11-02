from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.config import Settings
from rag_api.db.models import CollectionRow, FileRow, IngestRunRow, StageRunRow
from rag_api.errors import AppError
from rag_api.queue import JobQueue
from rag_api.s3 import ObjectStore
from rag_api.schemas.base import PageInfo
from rag_api.schemas.files import FileList, FileOut, FileUpdate
from rag_api.services.batches import file_out
from rag_api.services.tags import normalize_tags


async def load_file(session: AsyncSession, file_id: str) -> FileRow:
    """404 FILE_NOT_FOUND (details.file_id)."""
    row = await session.get(FileRow, file_id)
    if row is None:
        raise AppError("FILE_NOT_FOUND", details={"file_id": file_id})
    return row


async def list_files(
    session: AsyncSession,
    limit: int,
    offset: int,
    batch_id: str | None,
    tag: str | None,
    mime: str | None,
) -> FileList:
    """Filters AND-ed (tag: files.tags contains tag). Order created_at desc, filename asc.
    page.total counts filtered rows."""
    stmt = select(FileRow)
    count_stmt = select(func.count()).select_from(FileRow)
    if batch_id is not None:
        stmt = stmt.where(FileRow.batch_id == batch_id)
        count_stmt = count_stmt.where(FileRow.batch_id == batch_id)
    if tag is not None:
        stmt = stmt.where(FileRow.tags.contains([tag]))
        count_stmt = count_stmt.where(FileRow.tags.contains([tag]))
    if mime is not None:
        stmt = stmt.where(FileRow.mime == mime)
        count_stmt = count_stmt.where(FileRow.mime == mime)
    total = await session.scalar(count_stmt)
    rows = (
        await session.scalars(
            stmt.order_by(FileRow.created_at.desc(), FileRow.filename.asc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return FileList(
        items=[file_out(row) for row in rows],
        page=PageInfo(total=int(total or 0), limit=limit, offset=offset),
    )


async def get_file(session: AsyncSession, file_id: str) -> FileOut:
    """404 FILE_NOT_FOUND (details.file_id)."""
    return file_out(await load_file(session, file_id))


async def update_file(session: AsyncSession, file_id: str, body: FileUpdate) -> FileOut:
    """Replace tags (normalized). 404 FILE_NOT_FOUND."""
    row = await load_file(session, file_id)
    row.tags = normalize_tags(body.tags)
    await session.flush()
    return file_out(row)


async def delete_file(
    session: AsyncSession, store: ObjectStore, queue: JobQueue, settings: Settings, file_id: str
) -> None:
    """404 FILE_NOT_FOUND. For each distinct collection of the file's ingest runs that has a store
    stage run with status done: enqueue('delete_points', {'qdrant_name', 'file_id'}, 'query').
    Delete stage_runs of the file's ingest runs, delete the file row (ingest runs cascade),
    flush, then store.delete(uploads bucket, s3_key)."""
    row = await load_file(session, file_id)
    runs = (
        await session.scalars(select(IngestRunRow).where(IngestRunRow.file_id == file_id))
    ).all()
    run_ids = [run.id for run in runs]
    stored_in = (
        await session.execute(
            select(IngestRunRow.collection_id, CollectionRow.qdrant_name)
            .join(CollectionRow, CollectionRow.id == IngestRunRow.collection_id)
            .join(StageRunRow, StageRunRow.run_id == IngestRunRow.id)
            .where(
                IngestRunRow.file_id == file_id,
                StageRunRow.stage == "store",
                StageRunRow.status == "done",
            )
            .order_by(IngestRunRow.collection_id)
            .distinct()
        )
    ).all()
    for _, qdrant_name in stored_in:
        await queue.enqueue(
            "delete_points", {"qdrant_name": qdrant_name, "file_id": file_id}, "query"
        )
    s3_key = row.s3_key
    if run_ids:
        await session.execute(delete(StageRunRow).where(StageRunRow.run_id.in_(run_ids)))
    await session.delete(row)
    await session.flush()
    await store.delete(settings.s3_bucket_uploads, s3_key)


async def get_file_content(
    session: AsyncSession, store: ObjectStore, settings: Settings, file_id: str
) -> tuple[bytes, str, str]:
    """(bytes, mime, filename). 404 FILE_NOT_FOUND."""
    row = await load_file(session, file_id)
    data = await store.get_bytes(settings.s3_bucket_uploads, row.s3_key)
    return data, row.mime, row.filename
