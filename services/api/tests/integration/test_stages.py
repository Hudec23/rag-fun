"""Integration tests for rag_api.services.stages: downstream_of, latest_rows, active_row,
check_can_start, mark_stale, stage_run_out, start_stage. The pure helpers are tested on
in-memory StageRunRow objects; latest_rows and start_stage use the `session` fixture
(postgres-test) with the queue/bus fakes and a monkeypatched job-payload builder.
The service is still a stub — every test here is red until T-api-013."""

import re
from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.models import BatchRow, FileRow, IngestRunRow, StageRunRow
from rag_api.errors import AppError
from rag_api.services import stages
from tests.conftest import add_collection
from tests.fakes import FakeEventBus, FakeJobQueue

B_1 = "019a4b2c-1d00-7b00-8000-0000000000b1"
F_1 = "019a4b2c-1f00-7b00-8000-0000000000f1"
R_1 = "019a4b2c-1a00-7b00-8000-0000000000a1"
R_2 = "019a4b2c-1a00-7b00-8000-0000000000a2"
SR_1 = "019a4b2c-1c00-7b00-8000-0000000000c1"
SR_2 = "019a4b2c-1c00-7b00-8000-0000000000c2"
SR_3 = "019a4b2c-1c00-7b00-8000-0000000000c3"

T_NEW = datetime(2026, 11, 1, 18, 22, 5, 123000, tzinfo=UTC)
T_OLD = datetime(2026, 11, 1, 18, 22, 3, 123000, tzinfo=UTC)
ISO_NEW = "2026-11-01T18:22:05.123Z"
ISO_OLD = "2026-11-01T18:22:03.123Z"

DATA = b"hello file"
SHA = "0" * 64
UUID7_RE = r"[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"


def make_stage_run(stage: str, status: str, *, stage_run_id: str = SR_1) -> StageRunRow:
    """In-memory row for the pure helpers (no session)."""
    return StageRunRow(
        id=stage_run_id,
        run_id=R_1,
        run_kind="ingest",
        stage=stage,
        version=1,
        params={},
        status=status,
        created_at=T_OLD,
    )


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


def test_downstream_of_returns_stages_after_in_pipeline_order() -> None:
    assert stages.downstream_of("chunk") == ["embed", "store"]
    assert stages.downstream_of("store") == []
    assert stages.downstream_of("transform") == ["retrieve", "rerank", "generate"]


async def test_latest_rows_returns_highest_version_per_stage(session: AsyncSession) -> None:
    await add_stage_run(session, SR_1, R_1, "parse", "done")
    await add_stage_run(session, SR_2, R_1, "parse", "failed", version=2)
    await add_stage_run(session, SR_3, R_1, "chunk", "done")

    latest = await stages.latest_rows(session, R_1)

    assert set(latest) == {"parse", "chunk"}
    assert latest["parse"].id == SR_2
    assert latest["parse"].version == 2
    assert latest["parse"].status == "failed"
    assert latest["chunk"].id == SR_3
    assert latest["chunk"].version == 1


def test_active_row_returns_row_only_when_latest_status_is_done() -> None:
    done = make_stage_run("parse", "done")
    assert stages.active_row({"parse": done}, "parse") is done

    assert stages.active_row({"parse": make_stage_run("parse", "failed")}, "parse") is None
    assert stages.active_row({"parse": make_stage_run("parse", "stale")}, "parse") is None
    assert stages.active_row({"parse": make_stage_run("parse", "queued")}, "parse") is None
    assert stages.active_row({}, "parse") is None


def test_check_can_start_chunk_without_done_parse_raises_prerequisite_missing() -> None:
    with pytest.raises(AppError) as exc:
        stages.check_can_start({}, "chunk")
    assert exc.value.code == "STAGE_PREREQUISITE_MISSING"
    assert exc.value.details == {"stage": "chunk", "missing": "parse"}

    with pytest.raises(AppError) as exc:
        stages.check_can_start({"parse": make_stage_run("parse", "running")}, "chunk")
    assert exc.value.code == "STAGE_PREREQUISITE_MISSING"
    assert exc.value.details == {"stage": "chunk", "missing": "parse"}


def test_check_can_start_queued_stage_raises_already_running() -> None:
    with pytest.raises(AppError) as exc:
        stages.check_can_start({"parse": make_stage_run("parse", "queued")}, "parse")
    assert exc.value.code == "STAGE_ALREADY_RUNNING"
    assert exc.value.details == {"stage": "parse"}


def test_check_can_start_retrieve_needs_nothing_generate_needs_retrieve() -> None:
    stages.check_can_start({}, "retrieve")

    with pytest.raises(AppError) as exc:
        stages.check_can_start({}, "generate")
    assert exc.value.code == "STAGE_PREREQUISITE_MISSING"
    assert exc.value.details == {"stage": "generate", "missing": "retrieve"}


def test_mark_stale_stales_done_or_failed_downstream_rows_in_pipeline_order() -> None:
    chunk = make_stage_run("chunk", "done", stage_run_id=SR_1)
    embed = make_stage_run("embed", "failed", stage_run_id=SR_2)
    store = make_stage_run("store", "queued", stage_run_id=SR_3)
    latest = {"chunk": chunk, "embed": embed, "store": store}

    changed = stages.mark_stale(latest, "parse")

    assert changed == ["chunk", "embed"]
    assert chunk.status == "stale"
    assert embed.status == "stale"
    assert store.status == "queued"


async def test_start_stage_ingest_parse_inserts_queued_row_enqueues_and_publishes(
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

    async def fake_build_payload(*_: Any, **__: Any) -> dict[str, Any]:
        return {"p": 1}

    monkeypatch.setattr("rag_api.services.job_payloads.build_payload", fake_build_payload)

    row = await stages.start_stage(session, queue, bus, run, "parse", {"strategy": "auto"})

    assert re.fullmatch(UUID7_RE, row.id) is not None
    assert row.run_id == R_1
    assert row.run_kind == "ingest"
    assert row.stage == "parse"
    assert row.version == 1
    assert row.status == "queued"
    assert row.params == {"strategy": "auto"}
    assert row.created_at == T_NEW
    assert queue.jobs == [("parse", {"p": 1}, "ingest")]
    assert bus.published == [
        (
            R_1,
            {
                "type": "run.updated",
                "run_id": R_1,
                "run_kind": "ingest",
                "reason": "stage_queued",
                "ts": ISO_NEW,
            },
        )
    ]


async def test_start_stage_rerun_bumps_version_stales_done_downstream_and_publishes_both(
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
    await add_stage_run(session, SR_1, R_1, "parse", "done")
    await add_stage_run(session, SR_2, R_1, "chunk", "done")

    async def fake_build_payload(*_: Any, **__: Any) -> dict[str, Any]:
        return {"p": 1}

    monkeypatch.setattr("rag_api.services.job_payloads.build_payload", fake_build_payload)

    row = await stages.start_stage(session, queue, bus, run, "parse", {"strategy": "auto"})

    assert re.fullmatch(UUID7_RE, row.id) is not None
    assert row.version == 2
    assert row.status == "queued"

    parse_1 = await session.get(StageRunRow, SR_1)
    chunk_1 = await session.get(StageRunRow, SR_2)
    assert parse_1 is not None
    assert parse_1.status == "done"
    assert chunk_1 is not None
    assert chunk_1.status == "stale"

    assert queue.jobs == [("parse", {"p": 1}, "ingest")]
    assert bus.published == [
        (
            R_1,
            {
                "type": "run.updated",
                "run_id": R_1,
                "run_kind": "ingest",
                "reason": "stage_queued",
                "ts": ISO_NEW,
            },
        ),
        (
            R_1,
            {
                "type": "run.updated",
                "run_id": R_1,
                "run_kind": "ingest",
                "reason": "stages_stale",
                "ts": ISO_NEW,
            },
        ),
    ]


async def test_start_stage_clears_run_all_plan_unless_keep_plan(
    session: AsyncSession,
    queue: FakeJobQueue,
    bus: FakeEventBus,
    monkeypatch: pytest.MonkeyPatch,
    frozen_now: object,
) -> None:
    col = await add_collection(session, "docs")
    await add_batch(session, B_1)
    await add_file(session, F_1, B_1)
    plan_1 = [{"stage": "chunk", "params": {"strategy": "auto"}}]
    plan_2 = [{"stage": "chunk", "params": {"strategy": "auto"}}]
    run = await add_ingest_run(session, R_1, F_1, col.id, run_all_plan=plan_1)
    run_2 = await add_ingest_run(session, R_2, F_1, col.id, run_all_plan=plan_2)

    async def fake_build_payload(*_: Any, **__: Any) -> dict[str, Any]:
        return {"p": 1}

    monkeypatch.setattr("rag_api.services.job_payloads.build_payload", fake_build_payload)

    await stages.start_stage(session, queue, bus, run, "parse", {"strategy": "auto"})
    await session.refresh(run)
    assert run.run_all_plan == []

    await stages.start_stage(
        session, queue, bus, run_2, "parse", {"strategy": "auto"}, keep_plan=True
    )
    await session.refresh(run_2)
    assert run_2.run_all_plan == plan_2


def test_stage_run_out_formats_timestamps_with_to_iso_and_keeps_none() -> None:
    row = StageRunRow(
        id=SR_1,
        run_id=R_1,
        run_kind="ingest",
        stage="parse",
        version=1,
        params={"strategy": "auto"},
        status="done",
        artifact_key="artifacts/parse",
        summary={"pages": 3},
        error=None,
        created_at=T_OLD,
        started_at=T_NEW,
        finished_at=None,
    )

    out = stages.stage_run_out(row)

    assert out.model_dump() == {
        "id": SR_1,
        "run_id": R_1,
        "run_kind": "ingest",
        "stage": "parse",
        "version": 1,
        "params": {"strategy": "auto"},
        "status": "done",
        "artifact_key": "artifacts/parse",
        "summary": {"pages": 3},
        "error": None,
        "created_at": ISO_OLD,
        "started_at": ISO_NEW,
        "finished_at": None,
    }
