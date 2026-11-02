"""Integration tests for rag_api.services.query_runs: create_query_run, query_run_out,
list_query_runs, load_query_run. Real postgres via the `session` fixture, service
functions called directly. The service is still a stub — every test here is red until
T-api-017."""

from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.models import BatchRow, FileRow, IngestRunRow, QueryRunRow, StageRunRow
from rag_api.errors import AppError
from rag_api.schemas.runs import QueryRunCreate
from rag_api.services import query_runs
from tests.conftest import add_collection

Q_1 = "019a4b2c-1b00-7b00-8000-0000000000b1"
Q_2 = "019a4b2c-1b00-7b00-8000-0000000000b2"
Q_3 = "019a4b2c-1b00-7b00-8000-0000000000b3"
Q_4 = "019a4b2c-1b00-7b00-8000-0000000000b4"
SR_1 = "019a4b2c-2c00-7b00-8000-0000000000c1"
SR_2 = "019a4b2c-2c00-7b00-8000-0000000000c2"
SR_3 = "019a4b2c-2c00-7b00-8000-0000000000c3"
SR_4 = "019a4b2c-2c00-7b00-8000-0000000000c4"
B_1 = "019a4b2c-2e00-7b00-8000-0000000000b1"
F_1 = "019a4b2c-2f00-7b00-8000-0000000000f1"
IR_1 = "019a4b2c-2a00-7b00-8000-0000000000a1"
MISSING_COLLECTION = "019a4b2c-1d00-7b00-8000-0000000000ab"

T_OLD = datetime(2026, 11, 1, 18, 22, 3, 123000, tzinfo=UTC)
T_MID = datetime(2026, 11, 1, 18, 22, 4, 123000, tzinfo=UTC)
T_NEW = datetime(2026, 11, 1, 18, 22, 5, 123000, tzinfo=UTC)
ISO_OLD = "2026-11-01T18:22:03.123Z"
ISO_MID = "2026-11-01T18:22:04.123Z"
ISO_NEW = "2026-11-01T18:22:05.123Z"

SHA = "0" * 64

TRANSFORM_PARAMS: dict[str, Any] = {"queries": ["what is rag"]}
RETRIEVE_PARAMS: dict[str, Any] = {"top_k": 20}
GENERATE_PARAMS: dict[str, Any] = {"max_tokens": 100}


async def add_query_run(
    session: AsyncSession,
    run_id: str,
    collection_id: str,
    question: str,
    created_at: datetime,
    run_all_plan: list[dict[str, Any]] | None = None,
) -> QueryRunRow:
    row = QueryRunRow(
        id=run_id,
        collection_id=collection_id,
        question=question,
        run_all_plan=run_all_plan if run_all_plan is not None else [],
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
    *,
    version: int = 1,
    params: dict[str, Any] | None = None,
    created_at: datetime = T_OLD,
) -> StageRunRow:
    row = StageRunRow(
        id=stage_run_id,
        run_id=run_id,
        run_kind="query",
        stage=stage,
        version=version,
        params=params if params is not None else {},
        status=status,
        created_at=created_at,
    )
    session.add(row)
    await session.flush()
    return row


async def add_ingest_run(session: AsyncSession, collection_id: str) -> IngestRunRow:
    """Batch + file + ingest run rows, so the ingest run id is a known id."""
    session.add(BatchRow(id=B_1, name="one", tags=[], created_at=T_OLD))
    await session.flush()
    session.add(
        FileRow(
            id=F_1,
            batch_id=B_1,
            filename="a.md",
            mime="text/markdown",
            size_bytes=10,
            sha256=SHA,
            s3_key=f"{B_1}/{F_1}/a.md",
            tags=[],
            created_at=T_OLD,
        )
    )
    await session.flush()
    row = IngestRunRow(id=IR_1, file_id=F_1, collection_id=collection_id, created_at=T_OLD)
    session.add(row)
    await session.flush()
    return row


def stage_out(
    stage_run_id: str,
    run_id: str,
    stage: str,
    status: str,
    params: dict[str, Any],
    created_at: str,
    version: int = 1,
) -> dict[str, Any]:
    return {
        "id": stage_run_id,
        "run_id": run_id,
        "run_kind": "query",
        "stage": stage,
        "version": version,
        "params": params,
        "status": status,
        "artifact_key": None,
        "summary": None,
        "error": None,
        "created_at": created_at,
        "started_at": None,
        "finished_at": None,
    }


def run_out(run_id: str, collection_id: str, question: str, created_at: str) -> dict[str, Any]:
    return {
        "id": run_id,
        "collection_id": collection_id,
        "question": question,
        "created_at": created_at,
        "run_all_pending": [],
        "stages": {"transform": None, "retrieve": None, "rerank": None, "generate": None},
    }


async def test_create_query_run_strips_question_and_stores_empty_run(
    session: AsyncSession,
    frozen_now: object,
) -> None:
    col = await add_collection(session, "docs", created_at=T_OLD)

    out = await query_runs.create_query_run(
        session, QueryRunCreate(collection_id=col.id, question="  How?  ")
    )

    assert out.model_dump() == {
        "id": out.id,
        "collection_id": col.id,
        "question": "How?",
        "created_at": ISO_NEW,
        "run_all_pending": [],
        "stages": {"transform": None, "retrieve": None, "rerank": None, "generate": None},
    }
    row = await session.get(QueryRunRow, out.id)
    assert row is not None
    assert row.question == "How?"
    assert row.run_all_plan == []
    assert row.created_at == T_NEW


async def test_create_query_run_blank_question_is_validation_error(
    session: AsyncSession,
) -> None:
    col = await add_collection(session, "docs", created_at=T_OLD)

    with pytest.raises(AppError) as exc:
        await query_runs.create_query_run(
            session, QueryRunCreate(collection_id=col.id, question="   ")
        )
    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.details == {"field": "question"}
    assert (await session.execute(select(QueryRunRow))).scalars().all() == []


async def test_create_query_run_unknown_collection_is_collection_not_found(
    session: AsyncSession,
) -> None:
    with pytest.raises(AppError) as exc:
        await query_runs.create_query_run(
            session, QueryRunCreate(collection_id=MISSING_COLLECTION, question="How?")
        )
    assert exc.value.code == "COLLECTION_NOT_FOUND"
    assert exc.value.details == {"collection_id": MISSING_COLLECTION}
    assert (await session.execute(select(QueryRunRow))).scalars().all() == []


async def test_query_run_out_shows_latest_row_per_query_stage(session: AsyncSession) -> None:
    col = await add_collection(session, "docs", created_at=T_OLD)
    await add_query_run(session, Q_1, col.id, "What is RAG?", T_OLD)
    # An older failed transform is shadowed by the newer done one: only the latest row shows.
    await add_stage_run(session, SR_1, Q_1, "transform", "failed", params=TRANSFORM_PARAMS)
    await add_stage_run(
        session,
        SR_2,
        Q_1,
        "transform",
        "done",
        version=2,
        params=TRANSFORM_PARAMS,
        created_at=T_MID,
    )
    await add_stage_run(session, SR_3, Q_1, "retrieve", "queued", params=RETRIEVE_PARAMS)
    await add_stage_run(session, SR_4, Q_1, "generate", "done", params=GENERATE_PARAMS)

    out = await query_runs.query_run_out(session, Q_1)

    assert out.model_dump() == {
        "id": Q_1,
        "collection_id": col.id,
        "question": "What is RAG?",
        "created_at": ISO_OLD,
        "run_all_pending": [],
        "stages": {
            "transform": stage_out(
                SR_2, Q_1, "transform", "done", TRANSFORM_PARAMS, ISO_MID, version=2
            ),
            "retrieve": stage_out(SR_3, Q_1, "retrieve", "queued", RETRIEVE_PARAMS, ISO_OLD),
            "rerank": None,
            "generate": stage_out(SR_4, Q_1, "generate", "done", GENERATE_PARAMS, ISO_OLD),
        },
    }


async def test_list_query_runs_by_collection_newest_first(session: AsyncSession) -> None:
    col1 = await add_collection(session, "one", created_at=T_OLD)
    col2 = await add_collection(session, "two", created_at=T_OLD)
    await add_query_run(session, Q_1, col1.id, "a?", T_OLD)
    await add_query_run(session, Q_2, col1.id, "b?", T_NEW)
    await add_query_run(session, Q_3, col2.id, "c?", T_NEW)
    await add_query_run(session, Q_4, col2.id, "d?", T_MID)

    by_one = await query_runs.list_query_runs(session, 10, 0, col1.id)
    assert [item.model_dump() for item in by_one.items] == [
        run_out(Q_2, col1.id, "b?", ISO_NEW),
        run_out(Q_1, col1.id, "a?", ISO_OLD),
    ]
    assert by_one.page.model_dump() == {"total": 2, "limit": 10, "offset": 0}

    by_two = await query_runs.list_query_runs(session, 10, 0, col2.id)
    assert [item.id for item in by_two.items] == [Q_3, Q_4]
    assert by_two.page.model_dump() == {"total": 2, "limit": 10, "offset": 0}

    # Newest first, id desc on ties: Q_3 > Q_2 at T_NEW, Q_4 at T_MID, Q_1 last.
    unfiltered = await query_runs.list_query_runs(session, 10, 0, None)
    assert [item.id for item in unfiltered.items] == [Q_3, Q_2, Q_4, Q_1]
    assert unfiltered.page.model_dump() == {"total": 4, "limit": 10, "offset": 0}

    page = await query_runs.list_query_runs(session, 1, 1, None)
    assert [item.id for item in page.items] == [Q_2]
    assert page.page.model_dump() == {"total": 4, "limit": 1, "offset": 1}


async def test_load_query_run_ingest_run_id_raises_run_not_found(
    session: AsyncSession,
) -> None:
    col = await add_collection(session, "docs", created_at=T_OLD)
    await add_ingest_run(session, col.id)

    with pytest.raises(AppError) as exc:
        await query_runs.load_query_run(session, IR_1)
    assert exc.value.code == "RUN_NOT_FOUND"
    assert exc.value.details == {"run_id": IR_1}
    # The id exists as an ingest run: this is not just an unknown id.
    assert (await session.get(IngestRunRow, IR_1)) is not None
    assert (await session.get(QueryRunRow, IR_1)) is None
