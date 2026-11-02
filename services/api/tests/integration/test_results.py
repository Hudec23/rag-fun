"""Integration tests for rag_api.services.results: record_started, record_result.
The `session`/`client` fixtures (postgres-test) are used with the queue/bus fakes and a
monkeypatched job-payload builder. The service is still a stub — every test here is red
until T-api-018."""

import re
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.config import Settings
from rag_api.contracts_gen.shared.common_schema import ErrorBody
from rag_api.db.models import BatchRow, FileRow, IngestRunRow, StageRunRow
from rag_api.errors import AppError
from rag_api.schemas.system import StageResult, StageStarted
from rag_api.services import results
from tests.conftest import add_collection
from tests.fakes import FakeEventBus, FakeJobQueue

B_1 = "019a4b2c-1d00-7b00-8000-0000000000b1"
F_1 = "019a4b2c-1f00-7b00-8000-0000000000f1"
R_1 = "019a4b2c-1a00-7b00-8000-0000000000a1"
SR_1 = "019a4b2c-1c00-7b00-8000-0000000000c1"
SR_2 = "019a4b2c-1c00-7b00-8000-0000000000c2"
SR_MISSING = "019a4b2c-1c00-7b00-8000-0000000000c9"

T_OLD = datetime(2026, 11, 1, 18, 22, 3, 123000, tzinfo=UTC)
T_NEW = datetime(2026, 11, 1, 18, 22, 5, 123000, tzinfo=UTC)
ISO_NEW = "2026-11-01T18:22:05.123Z"
UUID7_RE = r"[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"

DATA = b"hello file"
SHA = "0" * 64

KEY_1 = "019a4b2c-2000-7c00-9000-000000000002/parse/v1.json"
KEY_2 = "019a4b2c-2000-7c00-9000-000000000002/parse/v2.json"

PARSE_SUMMARY = {
    "stage": "parse",
    "pages": 2,
    "elements": 3,
    "tables": 1,
    "pictures": 0,
    "chars": 120,
    "ocr_used": True,
}
PARSE_SUMMARY_2 = {
    "stage": "parse",
    "pages": 4,
    "elements": 9,
    "tables": 2,
    "pictures": 1,
    "chars": 500,
    "ocr_used": False,
}
ERROR_BODY = {
    "code": "UNSUPPORTED_FOR_STRATEGY",
    "message": "plain_text cannot read image/png",
    "details": {"mime": "image/png"},
}
HTTP_SUMMARY = {
    "stage": "parse",
    "pages": 0,
    "elements": 1,
    "tables": 0,
    "pictures": 0,
    "chars": 5,
    "ocr_used": False,
}


def plan() -> list[dict[str, Any]]:
    return [{"stage": "chunk", "params": {"strategy": "auto"}}]


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
    artifact_key: str | None = None,
    summary: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
) -> StageRunRow:
    row = StageRunRow(
        id=stage_run_id,
        run_id=run_id,
        run_kind="ingest",
        stage=stage,
        version=version,
        params={},
        status=status,
        artifact_key=artifact_key,
        summary=summary,
        error=error,
        created_at=T_OLD,
        started_at=started_at,
        finished_at=finished_at,
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


def stage_result_event(run_id: str) -> tuple[str, dict[str, Any]]:
    return (
        run_id,
        {
            "type": "run.updated",
            "run_id": run_id,
            "run_kind": "ingest",
            "reason": "stage_result",
            "ts": ISO_NEW,
        },
    )


async def test_record_started_marks_queued_running_and_leaves_done_unchanged(
    session: AsyncSession,
    frozen_now: object,
) -> None:
    col = await add_collection(session, "docs")
    await add_batch(session, B_1)
    await add_file(session, F_1, B_1)
    await add_ingest_run(session, R_1, F_1, col.id)
    queued = await add_stage_run(session, SR_1, R_1, "parse", "queued")
    done = await add_stage_run(
        session,
        SR_2,
        R_1,
        "embed",
        "done",
        artifact_key=KEY_1,
        summary=PARSE_SUMMARY,
        started_at=T_OLD,
        finished_at=T_OLD,
    )

    await results.record_started(session, StageStarted(stage_run_id=SR_1, started_at=ISO_NEW))
    await results.record_started(session, StageStarted(stage_run_id=SR_2, started_at=ISO_NEW))

    assert queued.status == "running"
    assert queued.started_at == T_NEW
    assert queued.finished_at is None
    assert done.status == "done"
    assert done.artifact_key == KEY_1
    assert done.summary == PARSE_SUMMARY
    assert done.started_at == T_OLD
    assert done.finished_at == T_OLD


async def test_record_result_done_stores_fields_and_publishes_stage_result(
    session: AsyncSession,
    queue: FakeJobQueue,
    bus: FakeEventBus,
    frozen_now: object,
) -> None:
    col = await add_collection(session, "docs")
    await add_batch(session, B_1)
    await add_file(session, F_1, B_1)
    await add_ingest_run(session, R_1, F_1, col.id)
    row = await add_stage_run(session, SR_1, R_1, "parse", "running", started_at=T_NEW)

    body = StageResult(
        stage_run_id=SR_1,
        status="done",
        artifact_key=KEY_1,
        summary=PARSE_SUMMARY,
        error=None,
        started_at=ISO_NEW,
        finished_at=ISO_NEW,
    )
    await results.record_result(session, queue, bus, body)

    assert row.status == "done"
    assert row.artifact_key == KEY_1
    assert row.summary == PARSE_SUMMARY
    assert row.error is None
    assert row.started_at == T_NEW
    assert row.finished_at == T_NEW
    assert queue.jobs == []
    assert bus.published == [stage_result_event(R_1)]


async def test_record_result_failed_stores_error_and_clears_run_all_plan(
    session: AsyncSession,
    queue: FakeJobQueue,
    bus: FakeEventBus,
    frozen_now: object,
) -> None:
    col = await add_collection(session, "docs")
    await add_batch(session, B_1)
    await add_file(session, F_1, B_1)
    run = await add_ingest_run(session, R_1, F_1, col.id, run_all_plan=plan())
    row = await add_stage_run(session, SR_1, R_1, "parse", "running", started_at=T_NEW)

    body = StageResult(
        stage_run_id=SR_1,
        status="failed",
        artifact_key=None,
        summary=None,
        error=ErrorBody(**ERROR_BODY),
        started_at=ISO_NEW,
        finished_at=ISO_NEW,
    )
    await results.record_result(session, queue, bus, body)

    assert row.status == "failed"
    assert row.artifact_key is None
    assert row.summary is None
    assert row.error == ERROR_BODY
    assert row.started_at == T_NEW
    assert row.finished_at == T_NEW
    assert run.run_all_plan == []
    assert queue.jobs == []
    assert bus.published == [stage_result_event(R_1)]


async def test_record_result_on_done_row_is_ignored_as_duplicate(
    session: AsyncSession,
    queue: FakeJobQueue,
    bus: FakeEventBus,
    frozen_now: object,
) -> None:
    col = await add_collection(session, "docs")
    await add_batch(session, B_1)
    await add_file(session, F_1, B_1)
    run = await add_ingest_run(session, R_1, F_1, col.id, run_all_plan=plan())
    row = await add_stage_run(
        session,
        SR_1,
        R_1,
        "parse",
        "done",
        artifact_key=KEY_1,
        summary=PARSE_SUMMARY,
        started_at=T_OLD,
        finished_at=T_OLD,
    )

    body = StageResult(
        stage_run_id=SR_1,
        status="done",
        artifact_key=KEY_2,
        summary=PARSE_SUMMARY_2,
        error=None,
        started_at=ISO_NEW,
        finished_at=ISO_NEW,
    )
    await results.record_result(session, queue, bus, body)

    assert row.status == "done"
    assert row.artifact_key == KEY_1
    assert row.summary == PARSE_SUMMARY
    assert row.error is None
    assert row.started_at == T_OLD
    assert row.finished_at == T_OLD
    assert run.run_all_plan == plan()
    assert queue.jobs == []
    assert bus.published == []


async def test_record_result_done_with_plan_queues_next_stage_and_shrinks_plan(
    session: AsyncSession,
    queue: FakeJobQueue,
    bus: FakeEventBus,
    monkeypatch: pytest.MonkeyPatch,
    frozen_now: object,
) -> None:
    col = await add_collection(session, "docs")
    await add_batch(session, B_1)
    await add_file(session, F_1, B_1)
    run = await add_ingest_run(session, R_1, F_1, col.id, run_all_plan=plan())
    row = await add_stage_run(session, SR_1, R_1, "parse", "running", started_at=T_NEW)
    patch_payload_builder(monkeypatch)

    body = StageResult(
        stage_run_id=SR_1,
        status="done",
        artifact_key=KEY_1,
        summary=PARSE_SUMMARY,
        error=None,
        started_at=ISO_NEW,
        finished_at=ISO_NEW,
    )
    await results.record_result(session, queue, bus, body)

    assert row.status == "done"
    assert row.finished_at == T_NEW
    chunk = (
        await session.scalars(
            select(StageRunRow).where(StageRunRow.run_id == R_1, StageRunRow.stage == "chunk")
        )
    ).one()
    assert re.fullmatch(UUID7_RE, chunk.id) is not None
    assert chunk.run_kind == "ingest"
    assert chunk.stage == "chunk"
    assert chunk.version == 1
    assert chunk.status == "queued"
    assert chunk.params == {"strategy": "auto"}
    assert chunk.artifact_key is None
    assert chunk.summary is None
    assert chunk.error is None
    assert chunk.created_at == T_NEW
    assert chunk.started_at is None
    assert chunk.finished_at is None
    assert run.run_all_plan == []
    assert queue.jobs == [("chunk", {}, "ingest")]
    assert bus.published == [stage_queued_event(R_1), stage_result_event(R_1)]


async def test_unknown_stage_run_id_raises_stage_run_not_found(
    session: AsyncSession,
    queue: FakeJobQueue,
    bus: FakeEventBus,
) -> None:
    with pytest.raises(AppError) as exc:
        await results.record_started(
            session, StageStarted(stage_run_id=SR_MISSING, started_at=ISO_NEW)
        )
    assert exc.value.code == "STAGE_RUN_NOT_FOUND"
    assert exc.value.details == {"stage_run_id": SR_MISSING}

    with pytest.raises(AppError) as exc:
        await results.record_result(
            session,
            queue,
            bus,
            StageResult(
                stage_run_id=SR_MISSING,
                status="done",
                artifact_key=KEY_1,
                summary=PARSE_SUMMARY,
                error=None,
                started_at=ISO_NEW,
                finished_at=ISO_NEW,
            ),
        )
    assert exc.value.code == "STAGE_RUN_NOT_FOUND"
    assert exc.value.details == {"stage_run_id": SR_MISSING}


async def test_post_stage_results_requires_internal_token_and_stores_done(
    client: httpx.AsyncClient,
    session: AsyncSession,
    queue: FakeJobQueue,
    bus: FakeEventBus,
    settings: Settings,
    frozen_now: object,
) -> None:
    col = await add_collection(session, "docs")
    await add_batch(session, B_1)
    await add_file(session, F_1, B_1)
    await add_ingest_run(session, R_1, F_1, col.id)
    row = await add_stage_run(session, SR_1, R_1, "parse", "queued")
    await session.commit()

    body = {
        "stage_run_id": SR_1,
        "status": "done",
        "artifact_key": "k",
        "summary": HTTP_SUMMARY,
        "error": None,
        "started_at": ISO_NEW,
        "finished_at": ISO_NEW,
    }

    denied = await client.post("/internal/v1/stage-results", json=body)
    assert denied.status_code == 401
    assert denied.json() == {
        "error": {
            "code": "UNAUTHORIZED",
            "message": "Missing or wrong X-Internal-Token",
            "details": {},
        }
    }

    ok = await client.post(
        "/internal/v1/stage-results",
        json=body,
        headers={"X-Internal-Token": settings.internal_token},
    )
    assert ok.status_code == 204

    await session.refresh(row)
    assert row.status == "done"
    assert row.artifact_key == "k"
    assert row.summary == HTTP_SUMMARY
    assert row.error is None
    assert row.started_at == T_NEW
    assert row.finished_at == T_NEW
    assert queue.jobs == []
    assert bus.published == [stage_result_event(R_1)]
