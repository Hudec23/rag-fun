"""Batch upload (R-001, R-002, R-003)."""

from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.config import Settings
from rag_api.s3 import ObjectStore
from rag_api.schemas.files import BatchWithFiles, IncomingFile


def detect_mime(filename: str) -> str:
    """MIME from the lowercase extension via catalog.MIME_BY_EXT.
    Unknown/missing extension -> AppError('UNSUPPORTED_FILE_TYPE', details={'filename': filename})."""
    raise NotImplementedError("not implemented")


def default_batch_name(now_iso: str) -> str:
    """'2026-11-01T18:22:05.123Z' -> 'Batch 2026-11-01 18:22'."""
    raise NotImplementedError("not implemented")


async def upload_batch(
    session: AsyncSession,
    store: ObjectStore,
    settings: Settings,
    files: list[IncomingFile],
    name: str | None,
    tags: list[str],
) -> BatchWithFiles:
    """Validate ALL files first, in this order, before storing anything:
    0 files -> EMPTY_UPLOAD; len > settings.max_files_per_batch -> TOO_MANY_FILES (details.limit);
    for each file in order: detect_mime (UNSUPPORTED_FILE_TYPE); len(data) > max_upload_mb*1024*1024
    -> FILE_TOO_LARGE (details.filename, details.limit_mb); len(data) == 0 -> VALIDATION_ERROR
    (details.field='files', details.filename).
    Then: insert batch (name or default_batch_name, tags normalized), for each file: id=new_id(),
    key f'{batch_id}/{file_id}/{filename}', store.put_bytes(settings.s3_bucket_uploads, key, data, mime),
    sha256 hex of data, insert files row (tags []). Flush. Return BatchWithFiles (files in upload order,
    batch.file_count = len(files))."""
    raise NotImplementedError("not implemented")
