"""Integration tests for rag_api.services.run_all: first_not_done, start_run_all,
advance_plan. The pure helper is tested directly; the run-level functions use the
`session` fixture (postgres-test) with the queue/bus fakes and a monkeypatched
job-payload builder. The service is still a stub — every test here is red until
T-api-015."""

from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.models import BatchRow, FileRow, IngestRunRow, StageRunRow
from rag_api.services import run_all
from tests.conftest import add_collection
from tests.fakes import FakeEventBus, FakeJobQueue

B_1 = "019a4b2c-1d00-7b00-8000-0000000000b1"
F_1 = "019a4b2c-1f00-7b00-8000-0000000000f1"
R_1 = "019a4b2c-1a00-7b00-8000-0000000000a1"
SR_1 = "019a4b2c-1c00-7b00-8000-0000000000c1"
SR_2 = "019a4b2c-1c00-7b00-8000-0000000000c2"
SR_3 = "019a4b2c-1c00-7b00-8000-0000000000c3"
SR_4 = "019a4b2c-1c00-7b00-8000-0000000000c4"

T_OLD = datetime(2026, 11, 1, 18, 22, 3, 123000, tzinfo=UTC)
ISO_NEW = "2026-11-01T18:22:05.123Z"

DATA = b"hello file"
SHA = "0" * 64

INGEST_ORDER = ["parse", "chunk", "embed", "store"]
PARAMS: dict[str, dict[str, Any]] = {
    "parse": {"strategy": "auto"},
    "chunk": {"strategy": "auto"},
    "embed": {"model": "dense"},
    "store": {},
}
PLAN_AFTER_PARSE = [
    {"stage": "chunk", "params": {"strategy": "auto"}},
    {"stage": "embed", "params": {"model": "dense"}},
    {"stage": "store", "params": {}},
]


async def add_batch(session: AsyncSession, batch_id: str) -> BatchRow:
    row = BatchRow(id=batch_id, name="one", tags=[], created_at=T_OLD)
    session.add(row)
    await session.flush()
    return row


async def add_file(session: AsyncSession, file_id: str, batch_id: str) -> FileRow:
    row = FileRow(
        id=file_id,
        batch_id=batch_id,
        filename="a.md",
        mime="text/markdown",
        size_bytes=len(DATA),
        sha256=SHA,
        s3_key=f"{batch_id}/{file_id}/a.md",
        tags=[],
        created_at=T_OLD,
    )
    session.add(row)
    await session.flush()
    return row


async def add_ingest_run(
    session: AsyncSession,
    run_id: str,
    file_id: str,
    collection_id: str,
    run_all_plan: list[dict[str, Any]] | None = None,
) -> IngestRunRow:
    row = IngestRunRow(
        id=run_id,
        file_id=file_id,
        collection_id=collection_id,
        run_all_plan=run_all_plan if run_all_plan is not None else [],
        created_at=T_OLD,
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
) -> StageRunRow:
    row = StageRunRow(
        id=stage_run_id,
        run_id=run_id,
        run_kind="ingest",
        stage=stage,
        version=version,
        params={},
        status=status,
        created_at=T_OLD,
    )
    session.add(row)
    await session.flush()
    return row


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


def test_first_not_done_returns_first_stage_not_done_and_none_if_all_done() -> None:
    assert run_all.first_not_done(INGEST_ORDER, {}) == "parse"
    assert run_all.first_not_done(INGEST_ORDER, {"parse": "done", "chunk": "failed"}) == "chunk"
    assert (
        run_all.first_not_done(
            INGEST_ORDER, {"parse": "done", "chunk": "done", "embed": "done", "store": "done"}
        )
        is None
    )


async def test_start_run_all_fresh_run_starts_parse_and_keeps_rest_of_plan(
    session: AsyncSession,
    queue: FakeJobQueue,
    bus: FakeEventBus,
    monkeypatch: pytest.MonkeyPatch,
    frozen_now: object,
) -> None:
    col = await add_collection(session, "docs")
    await add_batch(session, B_1)
    await add_file(session, F_1, B_1)
    run = await add_ingest_run(session, R_1, F_1, col.id)
    patch_payload_builder(monkeypatch)

    started = await run_all.start_run_all(session, queue, bus, run, None, PARAMS)

    assert started is True
    assert queue.jobs == [("parse", {}, "ingest")]
    assert run.run_all_plan == PLAN_AFTER_PARSE
    assert bus.published == [stage_queued_event(R_1)]


async def test_start_run_all_from_stage_starts_that_stage_and_keeps_stages_after(
    session: AsyncSession,
    queue: FakeJobQueue,
    bus: FakeEventBus,
    monkeypatch: pytest.MonkeyPatch,
    frozen_now: object,
) -> None:
    col = await add_collection(session, "docs")
    await add_batch(session, B_1)
    await add_file(session, F_1, B_1)
    run = await add_ingest_run(session, R_1, F_1, col.id)
    await add_stage_run(session, SR_1, R_1, "chunk", "done")
    patch_payload_builder(monkeypatch)

    started = await run_all.start_run_all(session, queue, bus, run, "embed", PARAMS)

    assert started is True
    assert queue.jobs == [("embed", {}, "ingest")]
    assert run.run_all_plan == [{"stage": "store", "params": {}}]
    assert bus.published == [stage_queued_event(R_1)]


async def test_start_run_all_with_every_stage_done_returns_false_and_changes_nothing(
    session: AsyncSession,
    queue: FakeJobQueue,
    bus: FakeEventBus,
    monkeypatch: pytest.MonkeyPatch,
    frozen_now: object,
) -> None:
    col = await add_collection(session, "docs")
    await add_batch(session, B_1)
    await add_file(session, F_1, B_1)
    leftover = [{"stage": "store", "params": {}}]
    run = await add_ingest_run(session, R_1, F_1, col.id, run_all_plan=leftover)
    await add_stage_run(session, SR_1, R_1, "parse", "done")
    await add_stage_run(session, SR_2, R_1, "chunk", "done")
    await add_stage_run(session, SR_3, R_1, "embed", "done")
    await add_stage_run(session, SR_4, R_1, "store", "done")
    patch_payload_builder(monkeypatch)

    started = await run_all.start_run_all(session, queue, bus, run, None, PARAMS)

    assert started is False
    assert queue.jobs == []
    assert bus.published == []
    assert run.run_all_plan == leftover


async def test_advance_plan_starts_first_entry_and_shrinks_plan_by_one(
    session: AsyncSession,
    queue: FakeJobQueue,
    bus: FakeEventBus,
    monkeypatch: pytest.MonkeyPatch,
    frozen_now: object,
) -> None:
    col = await add_collection(session, "docs")
    await add_batch(session, B_1)
    await add_file(session, F_1, B_1)
    run = await add_ingest_run(
        session,
        R_1,
        F_1,
        col.id,
        run_all_plan=PLAN_AFTER_PARSE,
    )
    await add_stage_run(session, SR_1, R_1, "parse", "done")
    patch_payload_builder(monkeypatch)

    await run_all.advance_plan(session, queue, bus, run)

    assert queue.jobs == [("chunk", {}, "ingest")]
    assert run.run_all_plan == PLAN_AFTER_PARSE[1:]
    assert bus.published == [stage_queued_event(R_1)]


async def test_advance_plan_with_empty_plan_does_nothing(
    session: AsyncSession,
    queue: FakeJobQueue,
    bus: FakeEventBus,
    monkeypatch: pytest.MonkeyPatch,
    frozen_now: object,
) -> None:
    col = await add_collection(session, "docs")
    await add_batch(session, B_1)
    await add_file(session, F_1, B_1)
    run = await add_ingest_run(session, R_1, F_1, col.id)
    patch_payload_builder(monkeypatch)

    await run_all.advance_plan(session, queue, bus, run)

    assert queue.jobs == []
    assert bus.published == []
    assert run.run_all_plan == []


async def test_advance_plan_clears_plan_when_next_stage_cannot_start(
    session: AsyncSession,
    queue: FakeJobQueue,
    bus: FakeEventBus,
    monkeypatch: pytest.MonkeyPatch,
    frozen_now: object,
) -> None:
    col = await add_collection(session, "docs")
    await add_batch(session, B_1)
    await add_file(session, F_1, B_1)
    run = await add_ingest_run(
        session,
        R_1,
        F_1,
        col.id,
        run_all_plan=PLAN_AFTER_PARSE[:2],
    )
    # No stage runs at all: 'chunk' requires a done 'parse', so it cannot start.
    patch_payload_builder(monkeypatch)

    await run_all.advance_plan(session, queue, bus, run)

    assert run.run_all_plan == []
    assert queue.jobs == []
    assert bus.published == []
