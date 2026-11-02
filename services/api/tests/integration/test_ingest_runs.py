"""Integration tests for rag_api.services.ingest_runs: create_ingest_run,
ingest_run_out, list_ingest_runs, ingest_batch, load_ingest_run. Real postgres via the
`session` fixture, queue/bus via fakes, job-payload builder monkeypatched to {}.
The service is still a stub — every test here is red until T-api-016."""

from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.contracts_gen.shared.common_schema import (
    EmbedParams,
    FixedChunkParams,
    PlainTextParams,
    StoreParams,
)
from rag_api.db.models import BatchRow, FileRow, IngestRunRow, StageRunRow
from rag_api.errors import AppError
from rag_api.schemas.runs import (
    BatchIngestRequest,
    IngestParamsAll,
    IngestRunCreate,
)
from rag_api.services import ingest_runs
from tests.conftest import add_collection
from tests.fakes import FakeEventBus, FakeJobQueue

B_1 = "019a4b2c-1d00-7b00-8000-0000000000b1"
F_1 = "019a4b2c-1f00-7b00-8000-0000000000f1"
F_2 = "019a4b2c-1f00-7b00-8000-0000000000f2"
R_1 = "019a4b2c-1a00-7b00-8000-0000000000a1"
R_2 = "019a4b2c-1a00-7b00-8000-0000000000a2"
R_3 = "019a4b2c-1a00-7b00-8000-0000000000a3"
SR_1 = "019a4b2c-1c00-7b00-8000-0000000000c1"
SR_2 = "019a4b2c-1c00-7b00-8000-0000000000c2"
SR_3 = "019a4b2c-1c00-7b00-8000-0000000000c3"
SR_4 = "019a4b2c-1c00-7b00-8000-0000000000c4"
MISSING_FILE = "019a4b2c-1d00-7b00-8000-0000000000aa"
MISSING_COLLECTION = "019a4b2c-1d00-7b00-8000-0000000000ab"
MISSING_RUN = "019a4b2c-1d00-7b00-8000-0000000000ac"

T_OLD = datetime(2026, 11, 1, 18, 22, 3, 123000, tzinfo=UTC)
T_MID = datetime(2026, 11, 1, 18, 22, 4, 123000, tzinfo=UTC)
T_NEW = datetime(2026, 11, 1, 18, 22, 5, 123000, tzinfo=UTC)
ISO_OLD = "2026-11-01T18:22:03.123Z"
ISO_MID = "2026-11-01T18:22:04.123Z"
ISO_NEW = "2026-11-01T18:22:05.123Z"

DATA = b"hello file"
SHA = "0" * 64

PARSE_PARAMS: dict[str, Any] = {"strategy": "plain_text"}
CHUNK_PARAMS: dict[str, Any] = {
    "strategy": "fixed",
    "split_by": "word",
    "length": 100,
    "overlap": 10,
}
EMBED_PARAMS: dict[str, Any] = {"batch_size": 32}
STORE_PARAMS: dict[str, Any] = {}
PLAN_AFTER_PARSE = [
    {"stage": "chunk", "params": CHUNK_PARAMS},
    {"stage": "embed", "params": EMBED_PARAMS},
    {"stage": "store", "params": STORE_PARAMS},
]


async def add_batch(session: AsyncSession, batch_id: str = B_1) -> BatchRow:
    row = BatchRow(id=batch_id, name="one", tags=[], created_at=T_OLD)
    session.add(row)
    await session.flush()
    return row


async def add_file(
    session: AsyncSession, file_id: str, filename: str, created_at: datetime
) -> FileRow:
    row = FileRow(
        id=file_id,
        batch_id=B_1,
        filename=filename,
        mime="text/markdown",
        size_bytes=len(DATA),
        sha256=SHA,
        s3_key=f"{B_1}/{file_id}/{filename}",
        tags=[],
        created_at=created_at,
    )
    session.add(row)
    await session.flush()
    return row


async def add_ingest_run(
    session: AsyncSession,
    run_id: str,
    file_id: str,
    collection_id: str,
    created_at: datetime,
    run_all_plan: list[dict[str, Any]] | None = None,
) -> IngestRunRow:
    row = IngestRunRow(
        id=run_id,
        file_id=file_id,
        collection_id=collection_id,
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
        run_kind="ingest",
        stage=stage,
        version=version,
        params=params if params is not None else {},
        status=status,
        created_at=created_at,
    )
    session.add(row)
    await session.flush()
    return row


def file_out(file_id: str, filename: str, created_at: str) -> dict[str, Any]:
    return {
        "id": file_id,
        "batch_id": B_1,
        "filename": filename,
        "mime": "text/markdown",
        "size_bytes": len(DATA),
        "sha256": SHA,
        "tags": [],
        "created_at": created_at,
    }


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
        "run_kind": "ingest",
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


def run_out(
    run_id: str,
    file: dict[str, Any],
    collection_id: str,
    created_at: str,
    plan: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": run_id,
        "file": file,
        "collection_id": collection_id,
        "created_at": created_at,
        "run_all_pending": [p["stage"] for p in (plan or [])],
        "stages": {"parse": None, "chunk": None, "embed": None, "store": None},
    }


def ingest_params() -> IngestParamsAll:
    return IngestParamsAll(
        parse=PlainTextParams(strategy="plain_text"),
        chunk=FixedChunkParams(strategy="fixed", split_by="word", length=100, overlap=10),
        embed=EmbedParams(batch_size=32),
        store=StoreParams(),
    )


def patch_payload_builder(monkeypatch: pytest.MonkeyPatch) -> None:
    """job_payloads.build_payload -> {} so only the plan logic is under test."""

    async def fake_build_payload(*_: Any, **__: Any) -> dict[str, Any]:
        return {}

    monkeypatch.setattr("rag_api.services.job_payloads.build_payload", fake_build_payload)


def stage_queued_event(run_id: str) -> tuple[str, dict[str, Any]]:
    return (
        run_id,
        {
            "type": "run.updated",
            "run_id": run_id,
            "run_kind": "ingest",
            "reason": "stage_queued",
            "ts": ISO_NEW,
        },
    )


async def test_create_ingest_run_returns_run_out_with_file_and_empty_stages(
    session: AsyncSession,
    queue: FakeJobQueue,
    bus: FakeEventBus,
    frozen_now: object,
) -> None:
    col = await add_collection(session, "docs", created_at=T_OLD)
    await add_batch(session)
    await add_file(session, F_1, "a.md", T_OLD)
    body = IngestRunCreate(file_id=F_1, collection_id=col.id)

    out = await ingest_runs.create_ingest_run(session, body)

    assert out.model_dump() == {
        "id": out.id,
        "file": file_out(F_1, "a.md", ISO_OLD),
        "collection_id": col.id,
        "created_at": ISO_NEW,
        "run_all_pending": [],
        "stages": {"parse": None, "chunk": None, "embed": None, "store": None},
    }
    row = await session.get(IngestRunRow, out.id)
    assert row is not None
    assert row.file_id == F_1
    assert row.collection_id == col.id
    assert row.run_all_plan == []
    assert row.created_at == T_NEW
    assert queue.jobs == []
    assert bus.published == []


async def test_create_ingest_run_unknown_ids_raise_file_and_collection_not_found(
    session: AsyncSession,
    frozen_now: object,
) -> None:
    await add_batch(session)
    await add_file(session, F_1, "a.md", T_OLD)

    # Missing file wins over missing collection: the file is checked first.
    with pytest.raises(AppError) as exc:
        await ingest_runs.create_ingest_run(
            session, IngestRunCreate(file_id=MISSING_FILE, collection_id=MISSING_COLLECTION)
        )
    assert exc.value.code == "FILE_NOT_FOUND"
    assert exc.value.details == {"file_id": MISSING_FILE}

    with pytest.raises(AppError) as exc:
        await ingest_runs.create_ingest_run(
            session, IngestRunCreate(file_id=F_1, collection_id=MISSING_COLLECTION)
        )
    assert exc.value.code == "COLLECTION_NOT_FOUND"
    assert exc.value.details == {"collection_id": MISSING_COLLECTION}
    assert (await session.execute(select(IngestRunRow))).scalars().all() == []


async def test_ingest_run_out_shows_latest_row_per_stage_and_pending_plan(
    session: AsyncSession,
) -> None:
    col = await add_collection(session, "docs", created_at=T_OLD)
    await add_batch(session)
    await add_file(session, F_1, "a.md", T_OLD)
    await add_ingest_run(session, R_1, F_1, col.id, T_OLD, run_all_plan=PLAN_AFTER_PARSE)
    # An older failed parse is shadowed by the newer done one: only the latest row shows.
    await add_stage_run(session, SR_1, R_1, "parse", "failed", params=PARSE_PARAMS)
    await add_stage_run(
        session, SR_2, R_1, "parse", "done", version=2, params=PARSE_PARAMS, created_at=T_MID
    )
    await add_stage_run(session, SR_3, R_1, "embed", "queued", params=EMBED_PARAMS)
    await add_stage_run(session, SR_4, R_1, "store", "done", params=STORE_PARAMS)

    out = await ingest_runs.ingest_run_out(session, R_1)

    assert out.model_dump() == {
        "id": R_1,
        "file": file_out(F_1, "a.md", ISO_OLD),
        "collection_id": col.id,
        "created_at": ISO_OLD,
        "run_all_pending": [p["stage"] for p in PLAN_AFTER_PARSE],
        "stages": {
            "parse": stage_out(SR_2, R_1, "parse", "done", PARSE_PARAMS, ISO_MID, version=2),
            "chunk": None,
            "embed": stage_out(SR_3, R_1, "embed", "queued", EMBED_PARAMS, ISO_OLD),
            "store": stage_out(SR_4, R_1, "store", "done", STORE_PARAMS, ISO_OLD),
        },
    }
    assert out.run_all_pending == [p["stage"] for p in PLAN_AFTER_PARSE]


async def test_list_ingest_runs_filters_orders_and_counts_page(session: AsyncSession) -> None:
    col1 = await add_collection(session, "one", created_at=T_OLD)
    col2 = await add_collection(session, "two", created_at=T_OLD)
    await add_batch(session)
    await add_file(session, F_1, "a.md", T_OLD)
    await add_file(session, F_2, "b.md", T_OLD)
    await add_ingest_run(session, R_1, F_1, col1.id, T_OLD)
    await add_ingest_run(session, R_2, F_1, col1.id, T_NEW)
    await add_ingest_run(session, R_3, F_2, col2.id, T_NEW)
    file_a = file_out(F_1, "a.md", ISO_OLD)
    file_b = file_out(F_2, "b.md", ISO_OLD)

    by_file = await ingest_runs.list_ingest_runs(session, 10, 0, F_1, None)
    assert [item.model_dump() for item in by_file.items] == [
        run_out(R_2, file_a, col1.id, ISO_NEW),
        run_out(R_1, file_a, col1.id, ISO_OLD),
    ]
    assert by_file.page.model_dump() == {"total": 2, "limit": 10, "offset": 0}

    by_collection = await ingest_runs.list_ingest_runs(session, 10, 0, None, col1.id)
    assert [item.id for item in by_collection.items] == [R_2, R_1]
    assert by_collection.page.model_dump() == {"total": 2, "limit": 10, "offset": 0}

    combined = await ingest_runs.list_ingest_runs(session, 10, 0, F_1, col1.id)
    assert [item.id for item in combined.items] == [R_2, R_1]
    assert combined.page.model_dump() == {"total": 2, "limit": 10, "offset": 0}

    other = await ingest_runs.list_ingest_runs(session, 10, 0, None, col2.id)
    assert [item.model_dump() for item in other.items] == [
        run_out(R_3, file_b, col2.id, ISO_NEW),
    ]
    assert other.page.model_dump() == {"total": 1, "limit": 10, "offset": 0}

    # Newest first, id desc on ties: R_3 > R_2 at T_NEW, R_1 last.
    unfiltered = await ingest_runs.list_ingest_runs(session, 10, 0, None, None)
    assert [item.id for item in unfiltered.items] == [R_3, R_2, R_1]
    assert unfiltered.page.model_dump() == {"total": 3, "limit": 10, "offset": 0}

    page = await ingest_runs.list_ingest_runs(session, 1, 1, F_1, None)
    assert [item.id for item in page.items] == [R_1]
    assert page.page.model_dump() == {"total": 2, "limit": 1, "offset": 1}


async def test_ingest_batch_starts_queued_parse_per_file_in_upload_order(
    session: AsyncSession,
    queue: FakeJobQueue,
    bus: FakeEventBus,
    monkeypatch: pytest.MonkeyPatch,
    frozen_now: object,
) -> None:
    col = await add_collection(session, "docs", created_at=T_OLD)
    await add_batch(session)
    # Insert the newest file first: batch order must come from created_at, not insertion.
    await add_file(session, F_2, "b.md", T_MID)
    await add_file(session, F_1, "a.md", T_OLD)
    patch_payload_builder(monkeypatch)
    body = BatchIngestRequest(collection_id=col.id, params=ingest_params())

    result = await ingest_runs.ingest_batch(session, queue, bus, B_1, body)

    assert [item.file.model_dump() for item in result.items] == [
        file_out(F_1, "a.md", ISO_OLD),
        file_out(F_2, "b.md", ISO_MID),
    ]
    for item in result.items:
        assert item.collection_id == col.id
        assert item.created_at == ISO_NEW
        assert item.run_all_pending == ["chunk", "embed", "store"]
        assert item.stages.chunk is None
        assert item.stages.embed is None
        assert item.stages.store is None
        parse = item.stages.parse
        assert parse is not None
        assert parse.model_dump() == stage_out(
            parse.id, item.id, "parse", "queued", PARSE_PARAMS, ISO_NEW
        )
    assert queue.jobs == [("parse", {}, "ingest"), ("parse", {}, "ingest")]
    assert queue.functions() == ["parse", "parse"]
    assert bus.published == [stage_queued_event(item.id) for item in result.items]
    rows = (await session.execute(select(IngestRunRow))).scalars().all()
    assert {row.id: row.run_all_plan for row in rows} == {
        item.id: PLAN_AFTER_PARSE for item in result.items
    }
    stage_rows = (await session.execute(select(StageRunRow))).scalars().all()
    assert {row.id: (row.run_id, row.stage, row.status) for row in stage_rows} == {
        item.stages.parse.id: (item.id, "parse", "queued")
        for item in result.items  # type: ignore[union-attr]
    }


async def test_load_ingest_run_unknown_id_raises_run_not_found(session: AsyncSession) -> None:
    with pytest.raises(AppError) as exc:
        await ingest_runs.load_ingest_run(session, MISSING_RUN)
    assert exc.value.code == "RUN_NOT_FOUND"
    assert exc.value.details == {"run_id": MISSING_RUN}
