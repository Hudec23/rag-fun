from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.models import BatchRow, FileRow
from rag_api.schemas.files import BatchList, BatchOut, BatchUpdate, BatchWithFiles, FileOut


def batch_out(row: BatchRow, file_count: int) -> BatchOut:
    raise NotImplementedError("not implemented")


def file_out(row: FileRow) -> FileOut:
    raise NotImplementedError("not implemented")


async def list_batches(session: AsyncSession, limit: int, offset: int) -> BatchList:
    """Order created_at desc, id desc. file_count via count of files per batch. page.total = all batches."""
    raise NotImplementedError("not implemented")


async def get_batch(session: AsyncSession, batch_id: str) -> BatchWithFiles:
    """404 BATCH_NOT_FOUND (details.batch_id). files ordered created_at asc, id asc (= upload order)."""
    raise NotImplementedError("not implemented")


async def update_batch(session: AsyncSession, batch_id: str, body: BatchUpdate) -> BatchOut:
    """404 BATCH_NOT_FOUND. Only fields that are not None change; tags normalized (sorted, unique).
    Body with neither field -> AppError('VALIDATION_ERROR', details={'field': 'body'})."""
    raise NotImplementedError("not implemented")
