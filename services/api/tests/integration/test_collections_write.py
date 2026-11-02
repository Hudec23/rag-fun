"""Integration tests for rag_api.services.collections: create_collection, delete_collection.
Real postgres via the `session` fixture, queue via FakeJobQueue; rows are inserted directly so
the tests do not depend on the upload or run flows.
The services are still stubs — every test here is red until T-api-011."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.models import (
    BatchRow,
    CollectionRow,
    FileRow,
    IngestRunRow,
    QueryRunRow,
    StageRunRow,
)
from rag_api.errors import AppError
from rag_api.schemas.collections import CollectionCreate
from rag_api.services import collections
from tests.conftest import add_collection
from tests.fakes import FakeJobQueue

B_1 = "019a4b2c-1d00-7b00-8000-0000000000b1"
B_2 = "019a4b2c-1d00-7b00-8000-0000000000b2"
F_1 = "019a4b2c-1f00-7b00-8000-0000000000f1"
F_2 = "019a4b2c-1f00-7b00-8000-0000000000f2"
R_1 = "019a4b2c-1a00-7b00-8000-0000000000a1"
R_2 = "019a4b2c-1a00-7b00-8000-0000000000a2"
QR_1 = "019a4b2c-1e00-7b00-8000-0000000000e1"
SR_1 = "019a4b2c-1c00-7b00-8000-0000000000c1"
SR_2 = "019a4b2c-1c00-7b00-8000-0000000000c2"
SR_3 = "019a4b2c-1c00-7b00-8000-0000000000c3"
MISSING_ID = "019a4b2c-1d00-7b00-8000-0000000000aa"

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
        tags=[],
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


async def add_query_run(
    session: AsyncSession, run_id: str, collection_id: str, question: str, created_at: datetime
) -> QueryRunRow:
    row = QueryRunRow(
        id=run_id,
        collection_id=collection_id,
        question=question,
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
    run_kind: str,
    stage: str,
    status: str,
    created_at: datetime,
) -> StageRunRow:
    row = StageRunRow(
        id=stage_run_id,
        run_id=run_id,
        run_kind=run_kind,
        stage=stage,
        version=1,
        params={},
        status=status,
        created_at=created_at,
    )
    session.add(row)
    await session.flush()
    return row


async def test_create_collection_inserts_row_with_qdrant_name_dims_and_frozen_created_at(
    session: AsyncSession, frozen_now: object
) -> None:
    body = CollectionCreate(name="exp", dense_model="nomic-embed-text", sparse_model="Qdrant/bm25")

    out = await collections.create_collection(session, body)

    assert out.model_dump() == {
        "id": out.id,
        "name": "exp",
        "qdrant_name": "rf_" + out.id.replace("-", ""),
        "dense_model": "nomic-embed-text",
        "dense_dims": 768,
        "sparse_model": "Qdrant/bm25",
        "created_at": "2026-11-01T18:22:05.123Z",
    }
    rows = (await session.execute(select(CollectionRow))).scalars().all()
    assert [r.id for r in rows] == [out.id]
    assert rows[0].qdrant_name == "rf_" + out.id.replace("-", "")


async def test_create_collection_maps_dense_model_to_its_dims(
    session: AsyncSession, frozen_now: object
) -> None:
    mini = await collections.create_collection(
        session,
        CollectionCreate(name="mini", dense_model="all-minilm", sparse_model="Qdrant/bm25"),
    )
    assert mini.dense_dims == 384
    assert mini.dense_model == "all-minilm"

    large = await collections.create_collection(
        session,
        CollectionCreate(name="large", dense_model="mxbai-embed-large", sparse_model="Qdrant/bm25"),
    )
    assert large.dense_dims == 1024
    assert large.dense_model == "mxbai-embed-large"


async def test_create_collection_duplicate_name_raises_collection_name_taken(
    session: AsyncSession, frozen_now: object
) -> None:
    body = CollectionCreate(name="exp", dense_model="nomic-embed-text", sparse_model="Qdrant/bm25")
    first = await collections.create_collection(session, body)

    with pytest.raises(AppError) as exc:
        await collections.create_collection(session, body)

    assert first.name == "exp"
    assert exc.value.code == "COLLECTION_NAME_TAKEN"
    assert exc.value.details == {"name": "exp"}
    rows = (await session.execute(select(CollectionRow))).scalars().all()
    assert [r.name for r in rows] == ["exp"]


async def test_delete_collection_removes_only_its_runs_and_enqueues_drop_collection(
    session: AsyncSession, queue: FakeJobQueue, frozen_now: object
) -> None:
    col = await add_collection(session, "docs")
    other = await add_collection(session, "other")
    await add_batch(session, B_1, "one", T_OLD)
    await add_file(session, F_1, B_1, "a.md", "text/markdown", T_OLD)
    await add_ingest_run(session, R_1, F_1, col.id, T_OLD)
    await add_stage_run(session, SR_1, R_1, "ingest", "chunk", "done", T_OLD)
    await add_query_run(session, QR_1, col.id, "who won?", T_OLD)
    await add_stage_run(session, SR_2, QR_1, "query", "retrieve", "done", T_OLD)
    await add_batch(session, B_2, "two", T_OLD)
    await add_file(session, F_2, B_2, "b.md", "text/markdown", T_OLD)
    await add_ingest_run(session, R_2, F_2, other.id, T_OLD)
    await add_stage_run(session, SR_3, R_2, "ingest", "chunk", "done", T_OLD)

    await collections.delete_collection(session, queue, col.id)

    assert queue.jobs == [("drop_collection", {"qdrant_name": col.qdrant_name}, "query")]
    assert [c.id for c in (await session.execute(select(CollectionRow))).scalars().all()] == [
        other.id
    ]
    assert [r.id for r in (await session.execute(select(IngestRunRow))).scalars().all()] == [R_2]
    assert (await session.execute(select(QueryRunRow))).scalars().all() == []
    assert [r.id for r in (await session.execute(select(StageRunRow))).scalars().all()] == [SR_3]


async def test_delete_collection_unknown_raises_collection_not_found_and_enqueues_nothing(
    session: AsyncSession, queue: FakeJobQueue
) -> None:
    with pytest.raises(AppError) as exc:
        await collections.delete_collection(session, queue, MISSING_ID)

    assert exc.value.code == "COLLECTION_NOT_FOUND"
    assert exc.value.details == {"collection_id": MISSING_ID}
    assert queue.jobs == []
