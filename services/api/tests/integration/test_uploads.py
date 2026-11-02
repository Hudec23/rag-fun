"""Integration tests for rag_api.services.uploads: upload_batch + detect_mime +
default_batch_name. Real postgres via the `session` fixture, S3 via FakeObjectStore.
The service is still a stub — every test here is red until T-api-008."""

import hashlib

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.config import Settings
from rag_api.db.models import BatchRow
from rag_api.errors import AppError
from rag_api.schemas.files import IncomingFile
from rag_api.services.uploads import default_batch_name, detect_mime, upload_batch
from tests.fakes import FakeObjectStore

MD_DATA = b"# Report\n"
PDF_DATA = b"%PDF-1.4"


def test_detect_mime_uses_lowercase_extension() -> None:
    assert detect_mime("Report.PDF") == "application/pdf"
    assert detect_mime("a.jpeg") == "image/jpeg"
    assert detect_mime("x.tif") == "image/tiff"


def test_detect_mime_unknown_extension_raises_unsupported_file_type() -> None:
    with pytest.raises(AppError) as exc:
        detect_mime("notes.rtf")
    assert exc.value.code == "UNSUPPORTED_FILE_TYPE"
    assert exc.value.details == {"filename": "notes.rtf"}


def test_detect_mime_no_extension_raises_unsupported_file_type() -> None:
    with pytest.raises(AppError) as exc:
        detect_mime("README")
    assert exc.value.code == "UNSUPPORTED_FILE_TYPE"
    assert exc.value.details == {"filename": "README"}


def test_default_batch_name_formats_iso_datetime() -> None:
    assert default_batch_name("2026-11-01T18:22:05.123Z") == "Batch 2026-11-01 18:22"


async def test_upload_batch_two_files_uses_default_name_and_stores_every_file(
    session: AsyncSession, store: FakeObjectStore, settings: Settings, frozen_now: object
) -> None:
    result = await upload_batch(
        session,
        store,
        settings,
        [
            IncomingFile(filename="a.md", data=MD_DATA),
            IncomingFile(filename="b.pdf", data=PDF_DATA),
        ],
        None,
        ["x"],
    )
    assert result.batch.name == "Batch 2026-11-01 18:22"
    assert result.batch.tags == ["x"]
    assert result.batch.file_count == 2
    assert result.batch.created_at == "2026-11-01T18:22:05.123Z"
    assert [f.filename for f in result.files] == ["a.md", "b.pdf"]
    assert [f.mime for f in result.files] == ["text/markdown", "application/pdf"]
    assert [f.size_bytes for f in result.files] == [len(MD_DATA), len(PDF_DATA)]
    assert [f.sha256 for f in result.files] == [
        hashlib.sha256(MD_DATA).hexdigest(),
        hashlib.sha256(PDF_DATA).hexdigest(),
    ]
    assert [f.batch_id for f in result.files] == [result.batch.id, result.batch.id]
    assert [f.tags for f in result.files] == [[], []]
    assert [f.created_at for f in result.files] == [
        "2026-11-01T18:22:05.123Z",
        "2026-11-01T18:22:05.123Z",
    ]
    assert store.objects == {
        (settings.s3_bucket_uploads, f"{result.batch.id}/{result.files[0].id}/a.md"): (
            MD_DATA,
            "text/markdown",
        ),
        (settings.s3_bucket_uploads, f"{result.batch.id}/{result.files[1].id}/b.pdf"): (
            PDF_DATA,
            "application/pdf",
        ),
    }


async def test_upload_batch_no_files_raises_empty_upload(
    session: AsyncSession, store: FakeObjectStore, settings: Settings
) -> None:
    with pytest.raises(AppError) as exc:
        await upload_batch(session, store, settings, [], None, [])
    assert exc.value.code == "EMPTY_UPLOAD"
    assert exc.value.details == {}
    assert store.objects == {}


async def test_upload_batch_too_many_files_raises_too_many_files(
    session: AsyncSession, store: FakeObjectStore, settings: Settings
) -> None:
    files = [IncomingFile(filename=f"f{i:02d}.md", data=b"# hi") for i in range(21)]
    with pytest.raises(AppError) as exc:
        await upload_batch(session, store, settings, files, None, [])
    assert exc.value.code == "TOO_MANY_FILES"
    assert exc.value.details == {"limit": 20}
    assert store.objects == {}


async def test_upload_batch_file_too_large_raises_file_too_large(
    session: AsyncSession,
    store: FakeObjectStore,
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "max_upload_mb", 0)
    files = [IncomingFile(filename="b.pdf", data=b"%P")]
    with pytest.raises(AppError) as exc:
        await upload_batch(session, store, settings, files, None, [])
    assert exc.value.code == "FILE_TOO_LARGE"
    assert exc.value.details == {"filename": "b.pdf", "limit_mb": 0}
    assert store.objects == {}
    assert (await session.execute(select(BatchRow))).scalars().all() == []


async def test_upload_batch_unsupported_extension_stores_nothing(
    session: AsyncSession, store: FakeObjectStore, settings: Settings
) -> None:
    files = [
        IncomingFile(filename="a.md", data=MD_DATA),
        IncomingFile(filename="notes.rtf", data=b"{\\rtf1}"),
    ]
    with pytest.raises(AppError) as exc:
        await upload_batch(session, store, settings, files, None, [])
    assert exc.value.code == "UNSUPPORTED_FILE_TYPE"
    assert exc.value.details == {"filename": "notes.rtf"}
    assert store.objects == {}
    assert (await session.execute(select(BatchRow))).scalars().all() == []


async def test_upload_batch_empty_file_raises_validation_error(
    session: AsyncSession, store: FakeObjectStore, settings: Settings
) -> None:
    files = [IncomingFile(filename="a.md", data=b"")]
    with pytest.raises(AppError) as exc:
        await upload_batch(session, store, settings, files, None, [])
    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.details == {"field": "files", "filename": "a.md"}
    assert store.objects == {}
