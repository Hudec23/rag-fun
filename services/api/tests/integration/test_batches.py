"""Integration tests for rag_api.services.batches: list_batches, get_batch, update_batch.
Real postgres via the `session` fixture; BatchRow/FileRow rows are inserted directly so the
tests do not depend on the upload flow.
The service is still a stub — every test here is red until T-api-009."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.models import BatchRow, FileRow
from rag_api.errors import AppError
from rag_api.schemas.files import BatchUpdate
from rag_api.services import batches

B_OLDEST = "019a4b2c-1d00-7b00-8000-0000000000b1"
B_MIDDLE = "019a4b2c-1d00-7b00-8000-0000000000b2"
B_NEWEST = "019a4b2c-1d00-7b00-8000-0000000000b3"
F_1 = "019a4b2c-1e00-7b00-8000-0000000000f1"
F_2 = "019a4b2c-1e00-7b00-8000-0000000000f2"
F_3 = "019a4b2c-1e00-7b00-8000-0000000000f3"
MISSING_ID = "019a4b2c-1d00-7b00-8000-0000000000aa"

T_OLDEST = datetime(2026, 11, 1, 18, 22, 3, 123000, tzinfo=UTC)
T_MIDDLE = datetime(2026, 11, 1, 18, 22, 4, 123000, tzinfo=UTC)
T_NEWEST = datetime(2026, 11, 1, 18, 22, 5, 123000, tzinfo=UTC)


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
    created_at: datetime,
) -> FileRow:
    row = FileRow(
        id=file_id,
        batch_id=batch_id,
        filename=filename,
        mime="text/markdown",
        size_bytes=4,
        sha256="0" * 64,
        s3_key=f"{batch_id}/{file_id}/{filename}",
        tags=[],
        created_at=created_at,
    )
    session.add(row)
    await session.flush()
    return row


async def test_list_batches_orders_newest_first_counts_files_and_reports_page(
    session: AsyncSession,
) -> None:
    oldest = await add_batch(session, B_OLDEST, "oldest", T_OLDEST)
    middle = await add_batch(session, B_MIDDLE, "middle", T_MIDDLE)
    await add_batch(session, B_NEWEST, "newest", T_NEWEST)
    await add_file(session, F_1, oldest.id, "a.md", T_OLDEST)
    await add_file(session, F_2, oldest.id, "b.md", T_OLDEST)
    await add_file(session, F_3, middle.id, "c.md", T_MIDDLE)

    result = await batches.list_batches(session, 2, 0)

    assert [b.model_dump() for b in result.items] == [
        {
            "id": B_NEWEST,
            "name": "newest",
            "tags": [],
            "file_count": 0,
            "created_at": "2026-11-01T18:22:05.123Z",
        },
        {
            "id": B_MIDDLE,
            "name": "middle",
            "tags": [],
            "file_count": 1,
            "created_at": "2026-11-01T18:22:04.123Z",
        },
    ]
    assert result.page.model_dump() == {"total": 3, "limit": 2, "offset": 0}


async def test_list_batches_offset_beyond_total_returns_empty_items_with_unchanged_total(
    session: AsyncSession,
) -> None:
    batch = await add_batch(session, B_OLDEST, "only", T_OLDEST)
    await add_file(session, F_1, batch.id, "a.md", T_OLDEST)

    result = await batches.list_batches(session, 5, 10)

    assert result.items == []
    assert result.page.model_dump() == {"total": 1, "limit": 5, "offset": 10}


async def test_get_batch_orders_files_by_created_at_ascending(session: AsyncSession) -> None:
    batch = await add_batch(session, B_MIDDLE, "my batch", T_NEWEST)
    # Insert the newest file first: the order must come from created_at, not from insertion order.
    await add_file(session, F_3, batch.id, "newer.md", T_NEWEST)
    await add_file(session, F_1, batch.id, "older.md", T_MIDDLE)

    result = await batches.get_batch(session, batch.id)

    assert result.batch.model_dump() == {
        "id": B_MIDDLE,
        "name": "my batch",
        "tags": [],
        "file_count": 2,
        "created_at": "2026-11-01T18:22:05.123Z",
    }
    assert [f.model_dump() for f in result.files] == [
        {
            "id": F_1,
            "batch_id": B_MIDDLE,
            "filename": "older.md",
            "mime": "text/markdown",
            "size_bytes": 4,
            "sha256": "0" * 64,
            "tags": [],
            "created_at": "2026-11-01T18:22:04.123Z",
        },
        {
            "id": F_3,
            "batch_id": B_MIDDLE,
            "filename": "newer.md",
            "mime": "text/markdown",
            "size_bytes": 4,
            "sha256": "0" * 64,
            "tags": [],
            "created_at": "2026-11-01T18:22:05.123Z",
        },
    ]


async def test_get_batch_unknown_id_raises_batch_not_found(session: AsyncSession) -> None:
    with pytest.raises(AppError) as exc:
        await batches.get_batch(session, MISSING_ID)
    assert exc.value.code == "BATCH_NOT_FOUND"
    assert exc.value.details == {"batch_id": MISSING_ID}


async def test_update_batch_normalizes_tags_and_keeps_name(session: AsyncSession) -> None:
    batch = await add_batch(session, B_MIDDLE, "my batch", T_MIDDLE)

    result = await batches.update_batch(session, batch.id, BatchUpdate(tags=["b", "a", "a"]))

    assert result.model_dump() == {
        "id": B_MIDDLE,
        "name": "my batch",
        "tags": ["a", "b"],
        "file_count": 0,
        "created_at": "2026-11-01T18:22:04.123Z",
    }
    await session.refresh(batch)
    assert batch.name == "my batch"
    assert batch.tags == ["a", "b"]


async def test_update_batch_empty_body_raises_validation_error(session: AsyncSession) -> None:
    batch = await add_batch(session, B_OLDEST, "my batch", T_OLDEST)

    with pytest.raises(AppError) as exc:
        await batches.update_batch(session, batch.id, BatchUpdate())
    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.details == {"field": "body"}

    await session.refresh(batch)
    assert batch.name == "my batch"
    assert batch.tags == []
