from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.config import Settings
from rag_api.queue import JobQueue
from rag_api.s3 import ObjectStore
from rag_api.schemas.files import FileList, FileOut, FileUpdate


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
    raise NotImplementedError("not implemented")


async def get_file(session: AsyncSession, file_id: str) -> FileOut:
    """404 FILE_NOT_FOUND (details.file_id)."""
    raise NotImplementedError("not implemented")


async def update_file(session: AsyncSession, file_id: str, body: FileUpdate) -> FileOut:
    """Replace tags (normalized). 404 FILE_NOT_FOUND."""
    raise NotImplementedError("not implemented")


async def delete_file(
    session: AsyncSession, store: ObjectStore, queue: JobQueue, settings: Settings, file_id: str
) -> None:
    """404 FILE_NOT_FOUND. For each distinct collection of the file's ingest runs that has a store
    stage run with status done: enqueue('delete_points', {'qdrant_name', 'file_id'}, 'query').
    Delete stage_runs of the file's ingest runs, delete the file row (ingest runs cascade),
    flush, then store.delete(uploads bucket, s3_key)."""
    raise NotImplementedError("not implemented")


async def get_file_content(
    session: AsyncSession, store: ObjectStore, settings: Settings, file_id: str
) -> tuple[bytes, str, str]:
    """(bytes, mime, filename). 404 FILE_NOT_FOUND."""
    raise NotImplementedError("not implemented")
