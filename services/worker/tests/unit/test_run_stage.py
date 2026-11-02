"""Unit tests for run_stage: the generic job wrapper every jobs/<stage>.py uses —
payload validation, stage lifecycle reporting (started -> done | failed), error
mapping and the ctx['running'] counter. run_stage is a stub — every test here is
red until T-worker-009."""

import json
from typing import Any

from rag_worker.contracts_gen.jobs.chunk_schema import JobPayloadChunk
from rag_worker.errors import WorkerError
from rag_worker.report import StageReporter, run_stage
from tests.conftest import FIXTURES
from tests.contract import errors

PAYLOAD = json.loads((FIXTURES / "jobs__chunk.json").read_text())
RUN_ID = "019a4b2c-2000-7c00-9000-000000000002"
STAGE_RUN_ID = "019a4b2c-2100-7c00-9000-000000000003"
TS = "2026-11-01T18:22:05.123Z"
ARTIFACT_BUCKET = "artifacts"
ARTIFACT_KEY = f"{RUN_ID}/chunk/v1.json"
ARTIFACT = {"a": 1}
SUMMARY = {
    "stage": "chunk",
    "chunks": 42,
    "min_chars": 120,
    "max_chars": 998,
    "mean_chars": 731.5,
}
PARSE_FAILED_BODY = {"code": "PARSE_FAILED", "message": "Document conversion failed", "details": {}}
INTERNAL_ERROR_BODY = {
    "code": "INTERNAL_ERROR",
    "message": "Unexpected error",
    "details": {"exception": "ValueError"},
}


def _stage_event(event_type: str, **extra: Any) -> dict[str, Any]:
    return {
        "type": event_type,
        "run_id": RUN_ID,
        "stage_run_id": STAGE_RUN_ID,
        "stage": "chunk",
        "version": 1,
        "ts": TS,
        **extra,
    }


async def test_valid_payload_returns_done_result_and_reports_result(ctx, frozen_now) -> None:
    assert errors(PAYLOAD, "jobs/chunk.schema.json") == []

    async def body(
        job: Any, reporter: StageReporter, ctx_: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        assert isinstance(job, JobPayloadChunk)
        assert job.stage == "chunk" and job.stage_run_id == STAGE_RUN_ID
        assert ctx_ is ctx
        assert reporter.ctx.stage_run_id == STAGE_RUN_ID and reporter.ctx.stage == "chunk"
        return ARTIFACT, SUMMARY

    result = await run_stage(ctx, PAYLOAD, JobPayloadChunk, body)

    assert result == {"status": "done", "summary": SUMMARY}
    assert ctx["api"].started == [(STAGE_RUN_ID, TS)]
    assert ctx["api"].results == [
        {
            "stage_run_id": STAGE_RUN_ID,
            "status": "done",
            "artifact_key": ARTIFACT_KEY,
            "summary": SUMMARY,
            "error": None,
            "started_at": TS,
            "finished_at": TS,
        }
    ]
    assert json.loads(ctx["store"].objects[(ARTIFACT_BUCKET, ARTIFACT_KEY)]) == ARTIFACT
    assert ctx["events"].events == [
        (RUN_ID, _stage_event("stage.started")),
        (RUN_ID, _stage_event("stage.completed", artifact_key=ARTIFACT_KEY, summary=SUMMARY)),
    ]
    assert errors(ctx["events"].events[0][1], "events/stage.started.schema.json") == []
    assert errors(ctx["events"].events[1][1], "events/stage.completed.schema.json") == []
    assert ctx["running"] == 0


async def test_worker_error_body_returns_failed_result_with_code(ctx, frozen_now) -> None:
    async def body(
        job: Any, reporter: StageReporter, ctx_: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        raise WorkerError("PARSE_FAILED")

    result = await run_stage(ctx, PAYLOAD, JobPayloadChunk, body)

    assert result == {"status": "failed", "code": "PARSE_FAILED"}
    assert ctx["api"].results == [
        {
            "stage_run_id": STAGE_RUN_ID,
            "status": "failed",
            "artifact_key": None,
            "summary": None,
            "error": PARSE_FAILED_BODY,
            "started_at": TS,
            "finished_at": TS,
        }
    ]
    assert ctx["events"].events == [
        (RUN_ID, _stage_event("stage.started")),
        (RUN_ID, _stage_event("stage.failed", error=PARSE_FAILED_BODY)),
    ]
    assert errors(ctx["events"].events[1][1], "events/stage.failed.schema.json") == []
    assert ctx["running"] == 0


async def test_unexpected_exception_returns_internal_error(ctx, frozen_now) -> None:
    async def body(
        job: Any, reporter: StageReporter, ctx_: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        raise ValueError("boom")

    result = await run_stage(ctx, PAYLOAD, JobPayloadChunk, body)

    assert result == {"status": "failed", "code": "INTERNAL_ERROR"}
    assert ctx["api"].results == [
        {
            "stage_run_id": STAGE_RUN_ID,
            "status": "failed",
            "artifact_key": None,
            "summary": None,
            "error": INTERNAL_ERROR_BODY,
            "started_at": TS,
            "finished_at": TS,
        }
    ]
    assert ctx["events"].events == [
        (RUN_ID, _stage_event("stage.started")),
        (RUN_ID, _stage_event("stage.failed", error=INTERNAL_ERROR_BODY)),
    ]
    assert ctx["running"] == 0


async def test_invalid_payload_returns_invalid_without_api_calls(ctx, frozen_now) -> None:
    invalid_payload = {key: value for key, value in PAYLOAD.items() if key != "stage_run_id"}
    assert errors(PAYLOAD, "jobs/chunk.schema.json") == []
    assert errors(invalid_payload, "jobs/chunk.schema.json")

    async def body(
        job: Any, reporter: StageReporter, ctx_: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        raise AssertionError("body must not run for an invalid payload")

    result = await run_stage(ctx, invalid_payload, JobPayloadChunk, body)

    assert result == {"status": "invalid"}
    assert ctx["api"].started == []
    assert ctx["api"].results == []
    assert ctx["api"].calls == []
    assert ctx["events"].events == []
    assert ctx["running"] == 0


async def test_running_is_one_while_body_runs(ctx, frozen_now) -> None:
    seen: list[int] = []

    async def body(
        job: Any, reporter: StageReporter, ctx_: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        assert ctx_["running"] == 1
        seen.append(ctx_["running"])
        return ARTIFACT, SUMMARY

    result = await run_stage(ctx, PAYLOAD, JobPayloadChunk, body)

    assert seen == [1]
    assert result == {"status": "done", "summary": SUMMARY}
    assert ctx["running"] == 0
