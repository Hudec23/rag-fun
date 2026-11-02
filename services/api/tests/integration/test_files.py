"""Integration tests for rag_api.services.files: list_files, get_file, update_file,
delete_file, get_file_content. Real postgres via the `session` fixture, S3 via
FakeObjectStore, queue via FakeJobQueue; rows are inserted directly so the tests do not
depend on the upload flow.
The service is still a stub — every test here is red until T-api-010."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.config import Settings
from rag_api.db.models import BatchRow, FileRow, IngestRunRow, StageRunRow
from rag_api.errors import AppError
from rag_api.schemas.files import FileUpdate
from rag_api.services import files
from tests.conftest import add_collection
from tests.fakes import FakeJobQueue, FakeObjectStore

B_1 = "019a4b2c-1d00-7b00-8000-0000000000b1"
B_2 = "019a4b2c-1d00-7b00-8000-0000000000b2"
F_1 = "019a4b2c-1f00-7b00-8000-0000000000f1"
F_2 = "019a4b2c-1f00-7b00-8000-0000000000f2"
F_3 = "019a4b2c-1f00-7b00-8000-0000000000f3"
F_4 = "019a4b2c-1f00-7b00-8000-0000000000f4"
R_1 = "019a4b2c-1a00-7b00-8000-0000000000a1"
SR_1 = "019a4b2c-1c00-7b00-8000-0000000000c1"
MISSING_ID = "019a4b2c-1d00-7b00-8000-0000000000aa"

T_NEW = datetime(2026, 11, 1, 18, 22, 5, 123000, tzinfo=UTC)
T_OLD = datetime(2026, 11, 1, 18, 22, 3, 123000, tzinfo=UTC)

DATA = b"hello file"
SHA = "0" * 64


async def add_batch(
    session: AsyncSession, batch_id: str, name: str, created_at: datetime
) -> BatchRow:
    row = BatchRow(id=batch_id, name=name, tags=[], created_at=created_at)
    session.add(row)
    await session.flush()
    return row


async def add_file(
    session: AsyncSession,
    file_id: str,
    batch_id: str,
    filename: str,
    mime: str,
    tags: list[str],
    created_at: datetime,
) -> FileRow:
    row = FileRow(
        id=file_id,
        batch_id=batch_id,
        filename=filename,
        mime=mime,
        size_bytes=len(DATA),
        sha256=SHA,
        s3_key=f"{batch_id}/{file_id}/{filename}",
        tags=tags,
        created_at=created_at,
    )
    session.add(row)
    await session.flush()
    return row


async def add_ingest_run(
    session: AsyncSession, run_id: str, file_id: str, collection_id: str, created_at: datetime
) -> IngestRunRow:
    row = IngestRunRow(
        id=run_id,
        file_id=file_id,
        collection_id=collection_id,
        run_all_plan=[],
        created_at=created_at,
    )
    session.add(row)
    await session.flush()
    return row


async def add_stage_run(
    session: AsyncSession,
    stage_run_id: str,
    run_id: str,
    stage: str,
    status: str,
    created_at: datetime,
) -> StageRunRow:
    row = StageRunRow(
        id=stage_run_id,
        run_id=run_id,
        run_kind="ingest",
        stage=stage,
        version=1,
        params={},
        status=status,
        created_at=created_at,
    )
    session.add(row)
    await session.flush()
    return row


async def test_list_files_filters_by_batch_tag_and_mime_and_counts_filtered_rows(
    session: AsyncSession,
) -> None:
    await add_batch(session, B_1, "one", T_OLD)
    await add_batch(session, B_2, "two", T_OLD)
    await add_file(session, F_1, B_1, "a.md", "text/plain", ["tax"], T_NEW)
    await add_file(session, F_2, B_1, "b.md", "text/markdown", ["tax", "x"], T_NEW)
    await add_file(session, F_3, B_2, "c.md", "text/plain", ["tax"], T_OLD)
    await add_file(session, F_4, B_1, "d.md", "text/plain", [], T_OLD)

    by_batch = await files.list_files(session, 10, 0, B_1, None, None)
    assert [f.id for f in by_batch.items] == [F_1, F_2, F_4]
    assert by_batch.page.model_dump() == {"total": 3, "limit": 10, "offset": 0}

    by_tag = await files.list_files(session, 10, 0, None, "tax", None)
    assert [f.id for f in by_tag.items] == [F_1, F_2, F_3]
    assert by_tag.page.model_dump() == {"total": 3, "limit": 10, "offset": 0}

    by_mime = await files.list_files(session, 10, 0, None, None, "text/plain")
    assert [f.id for f in by_mime.items] == [F_1, F_3, F_4]
    assert by_mime.page.model_dump() == {"total": 3, "limit": 10, "offset": 0}

    combined = await files.list_files(session, 10, 0, B_1, "tax", "text/plain")
    assert [f.id for f in combined.items] == [F_1]
    assert combined.page.model_dump() == {"total": 1, "limit": 10, "offset": 0}


async def test_list_files_orders_by_created_at_desc_then_filename_asc(
    session: AsyncSession,
) -> None:
    await add_batch(session, B_1, "one", T_OLD)
    # Insert the newest files first and the oldest last: the expected order matches neither
    # insertion order nor filename order, so it must come from the two sort keys.
    await add_file(session, F_2, B_1, "b.md", "text/markdown", [], T_NEW)
    await add_file(session, F_1, B_1, "a.md", "text/markdown", [], T_NEW)
    await add_file(session, F_3, B_1, "a0.md", "text/markdown", [], T_OLD)

    result = await files.list_files(session, 10, 0, None, None, None)

    assert [f.model_dump() for f in result.items] == [
        {
            "id": F_1,
            "batch_id": B_1,
            "filename": "a.md",
            "mime": "text/markdown",
            "size_bytes": len(DATA),
            "sha256": SHA,
            "tags": [],
            "created_at": "2026-11-01T18:22:05.123Z",
        },
        {
            "id": F_2,
            "batch_id": B_1,
            "filename": "b.md",
            "mime": "text/markdown",
            "size_bytes": len(DATA),
            "sha256": SHA,
            "tags": [],
            "created_at": "2026-11-01T18:22:05.123Z",
        },
        {
            "id": F_3,
            "batch_id": B_1,
            "filename": "a0.md",
            "mime": "text/markdown",
            "size_bytes": len(DATA),
            "sha256": SHA,
            "tags": [],
            "created_at": "2026-11-01T18:22:03.123Z",
        },
    ]
    assert result.page.model_dump() == {"total": 3, "limit": 10, "offset": 0}


async def test_get_file_unknown_id_raises_file_not_found(session: AsyncSession) -> None:
    with pytest.raises(AppError) as exc:
        await files.get_file(session, MISSING_ID)
    assert exc.value.code == "FILE_NOT_FOUND"
    assert exc.value.details == {"file_id": MISSING_ID}


async def test_update_file_replaces_tags_normalized(session: AsyncSession) -> None:
    await add_batch(session, B_1, "one", T_OLD)
    row = await add_file(session, F_1, B_1, "a.md", "text/plain", ["x"], T_OLD)

    result = await files.update_file(session, F_1, FileUpdate(tags=["z", "a", "z"]))

    assert result.model_dump() == {
        "id": F_1,
        "batch_id": B_1,
        "filename": "a.md",
        "mime": "text/plain",
        "size_bytes": len(DATA),
        "sha256": SHA,
        "tags": ["a", "z"],
        "created_at": "2026-11-01T18:22:03.123Z",
    }
    await session.refresh(row)
    assert row.tags == ["a", "z"]


async def test_delete_file_enqueues_delete_points_for_done_store_stage_runs(
    session: AsyncSession,
    store: FakeObjectStore,
    queue: FakeJobQueue,
    settings: Settings,
    frozen_now: object,
) -> None:
    col = await add_collection(session, "docs")
    await add_batch(session, B_1, "one", T_OLD)
    row = await add_file(session, F_1, B_1, "a.md", "text/plain", [], T_OLD)
    await store.put_bytes(settings.s3_bucket_uploads, row.s3_key, DATA, "text/plain")
    await add_ingest_run(session, R_1, F_1, col.id, T_OLD)
    await add_stage_run(session, SR_1, R_1, "store", "done", T_OLD)

    await files.delete_file(session, store, queue, settings, F_1)

    assert queue.jobs == [
        ("delete_points", {"qdrant_name": col.qdrant_name, "file_id": F_1}, "query")
    ]
    assert (await session.execute(select(FileRow))).scalars().all() == []
    assert (await session.execute(select(IngestRunRow))).scalars().all() == []
    assert (await session.execute(select(StageRunRow))).scalars().all() == []
    assert store.objects == {}


async def test_delete_file_never_stored_enqueues_no_jobs(
    session: AsyncSession,
    store: FakeObjectStore,
    queue: FakeJobQueue,
    settings: Settings,
    frozen_now: object,
) -> None:
    col = await add_collection(session, "docs")
    await add_batch(session, B_1, "one", T_OLD)
    row = await add_file(session, F_1, B_1, "a.md", "text/plain", [], T_OLD)
    await store.put_bytes(settings.s3_bucket_uploads, row.s3_key, DATA, "text/plain")
    await add_ingest_run(session, R_1, F_1, col.id, T_OLD)
    # The store stage run exists but never finished: the file was never stored in qdrant.
    await add_stage_run(session, SR_1, R_1, "store", "queued", T_OLD)

    await files.delete_file(session, store, queue, settings, F_1)

    assert queue.jobs == []
    assert (await session.execute(select(FileRow))).scalars().all() == []
    assert (await session.execute(select(IngestRunRow))).scalars().all() == []
    assert (await session.execute(select(StageRunRow))).scalars().all() == []
    assert store.objects == {}


async def test_get_file_content_returns_bytes_mime_and_filename(
    session: AsyncSession, store: FakeObjectStore, settings: Settings
) -> None:
    await add_batch(session, B_1, "one", T_OLD)
    row = await add_file(session, F_1, B_1, "a.md", "text/plain", [], T_OLD)
    await store.put_bytes(settings.s3_bucket_uploads, row.s3_key, DATA, "text/plain")

    result = await files.get_file_content(session, store, settings, F_1)

    assert result == (DATA, "text/plain", "a.md")
