"""Batch upload (R-001, R-002, R-003)."""

import hashlib

from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.catalog import MIME_BY_EXT
from rag_api.config import Settings
from rag_api.db.models import BatchRow, FileRow
from rag_api.errors import AppError
from rag_api.ids import new_id, to_iso, utcnow
from rag_api.s3 import ObjectStore
from rag_api.schemas.files import BatchOut, BatchWithFiles, FileOut, IncomingFile
from rag_api.services.tags import normalize_tags


def detect_mime(filename: str) -> str:
    """MIME from the lowercase extension via catalog.MIME_BY_EXT.
    Unknown/missing extension -> AppError('UNSUPPORTED_FILE_TYPE', details={'filename': filename})."""
    ext = f".{filename.rsplit('.', 1)[-1].lower()}" if "." in filename else ""
    mime = MIME_BY_EXT.get(ext)
    if mime is None:
        raise AppError("UNSUPPORTED_FILE_TYPE", details={"filename": filename})
    return mime


def default_batch_name(now_iso: str) -> str:
    """'2026-11-01T18:22:05.123Z' -> 'Batch 2026-11-01 18:22'."""
    return f"Batch {now_iso[:10]} {now_iso[11:16]}"


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
    if not files:
        raise AppError("EMPTY_UPLOAD")
    if len(files) > settings.max_files_per_batch:
        raise AppError("TOO_MANY_FILES", details={"limit": settings.max_files_per_batch})
    max_bytes = settings.max_upload_mb * 1024 * 1024
    validated: list[tuple[IncomingFile, str]] = []
    for f in files:
        mime = detect_mime(f.filename)
        if len(f.data) > max_bytes:
            raise AppError(
                "FILE_TOO_LARGE",
                details={"filename": f.filename, "limit_mb": settings.max_upload_mb},
            )
        if not f.data:
            raise AppError("VALIDATION_ERROR", details={"field": "files", "filename": f.filename})
        validated.append((f, mime))
    now = utcnow()
    created_iso = to_iso(now)
    batch_id = new_id()
    batch_name = name or default_batch_name(created_iso)
    batch_tags = normalize_tags(tags)
    session.add(
        BatchRow(
            id=batch_id,
            name=batch_name,
            tags=batch_tags,
            created_at=now,
        )
    )
    out_files: list[FileOut] = []
    for f, mime in validated:
        file_id = new_id()
        key = f"{batch_id}/{file_id}/{f.filename}"
        await store.put_bytes(settings.s3_bucket_uploads, key, f.data, mime)
        digest = hashlib.sha256(f.data).hexdigest()
        session.add(
            FileRow(
                id=file_id,
                batch_id=batch_id,
                filename=f.filename,
                mime=mime,
                size_bytes=len(f.data),
                sha256=digest,
                s3_key=key,
                tags=[],
                created_at=now,
            )
        )
        out_files.append(
            FileOut(
                id=file_id,
                batch_id=batch_id,
                filename=f.filename,
                mime=mime,
                size_bytes=len(f.data),
                sha256=digest,
                tags=[],
                created_at=created_iso,
            )
        )
    await session.flush()
    return BatchWithFiles(
        batch=BatchOut(
            id=batch_id,
            name=batch_name,
            tags=batch_tags,
            file_count=len(files),
            created_at=created_iso,
        ),
        files=out_files,
    )
