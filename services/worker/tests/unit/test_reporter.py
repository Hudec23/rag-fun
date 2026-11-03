"""Unit tests for StageReporter: started -> progress* -> done | failed (callbacks + events + artifact)."""

import json
from typing import Any

from rag_worker.report import StageContext, StageReporter
from tests.conftest import FIXTURES
from tests.contract import errors

RUN_ID = "019a4b2c-2000-7c00-9000-000000000002"
STAGE_RUN_ID = "019a4b2c-2100-7c00-9000-000000000003"
STAGE = "parse"
VERSION = 1
TS = "2026-11-01T18:22:05.123Z"
ARTIFACT_BUCKET = "artifacts"
ARTIFACT_KEY = f"{RUN_ID}/{STAGE}/v{VERSION}.json"
ARTIFACT = json.loads((FIXTURES / "artifact_parse.json").read_text())
SUMMARY: dict[str, Any] = {
    "stage": "parse",
    "pages": 2,
    "elements": 8,
    "tables": 0,
    "pictures": 0,
    "chars": 350,
    "ocr_used": False,
}
ERROR_BODY: dict[str, Any] = {
    "code": "PARSE_FAILED",
    "message": "docling crashed on page 2",
    "details": {"page_no": 2},
}


def _reporter(ctx: dict[str, Any], t: list[float]) -> StageReporter:
    stage_ctx = StageContext(STAGE_RUN_ID, RUN_ID, STAGE, VERSION)
    return StageReporter(
        stage_ctx,
        ctx["api"],
        ctx["events"],
        ctx["store"],
        ctx["settings"].s3_bucket_artifacts,
        clock=lambda: t[0],
    )


def _started_event() -> dict[str, Any]:
    return {
        "type": "stage.started",
        "run_id": RUN_ID,
        "stage_run_id": STAGE_RUN_ID,
        "stage": STAGE,
        "version": VERSION,
        "ts": TS,
    }


def _progress_event(done: int, total: int, message: str) -> dict[str, Any]:
    return {
        "type": "stage.progress",
        "run_id": RUN_ID,
        "stage_run_id": STAGE_RUN_ID,
        "stage": STAGE,
        "version": VERSION,
        "ts": TS,
        "done": done,
        "total": total,
        "message": message,
    }


async def test_started_records_callback_and_publishes_event(ctx, frozen_now) -> None:
    t = [0.0]
    reporter = _reporter(ctx, t)
    await reporter.started()
    assert ctx["api"].started == [(STAGE_RUN_ID, TS)]
    assert ctx["events"].events == [
        (
            RUN_ID,
            {
                "type": "stage.started",
                "run_id": RUN_ID,
                "stage_run_id": STAGE_RUN_ID,
                "stage": STAGE,
                "version": VERSION,
                "ts": TS,
            },
        )
    ]
    assert errors(ctx["events"].events[0][1], "events/stage.started.schema.json") == []


async def test_progress_throttled_per_half_second_and_final_always_sent(ctx, frozen_now) -> None:
    t = [0.0]
    reporter = _reporter(ctx, t)
    await reporter.progress(1, 4, "m")
    t[0] = 0.1
    await reporter.progress(2, 4, "m")
    await reporter.progress(4, 4, "m")
    assert ctx["events"].types() == ["stage.progress", "stage.progress"]
    assert ctx["events"].events == [
        (RUN_ID, _progress_event(1, 4, "m")),
        (RUN_ID, _progress_event(4, 4, "m")),
    ]
    for _, event in ctx["events"].events:
        assert errors(event, "events/stage.progress.schema.json") == []


async def test_progress_clamps_done_and_sends_nothing_for_empty_total(ctx, frozen_now) -> None:
    t = [0.0]
    reporter = _reporter(ctx, t)
    await reporter.progress(9, 4, "m")
    await reporter.progress(0, 0, "m")
    assert ctx["events"].events == [(RUN_ID, _progress_event(4, 4, "m"))]


async def test_done_stores_artifact_and_reports_result(ctx, frozen_now) -> None:
    t = [0.0]
    reporter = _reporter(ctx, t)
    await reporter.started()
    key = await reporter.done(ARTIFACT, SUMMARY)
    assert key == ARTIFACT_KEY
    assert (ARTIFACT_BUCKET, ARTIFACT_KEY) in ctx["store"].objects
    assert json.loads(ctx["store"].objects[(ARTIFACT_BUCKET, ARTIFACT_KEY)]) == ARTIFACT
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


async def test_done_reports_result_before_publishing_completed(ctx, frozen_now) -> None:
    t = [0.0]
    reporter = _reporter(ctx, t)
    await reporter.started()
    await reporter.done(ARTIFACT, SUMMARY)
    assert ctx["api"].calls[-2:] == ["result", "stage.completed"]
    assert ctx["events"].events == [
        (RUN_ID, _started_event()),
        (
            RUN_ID,
            {
                "type": "stage.completed",
                "run_id": RUN_ID,
                "stage_run_id": STAGE_RUN_ID,
                "stage": STAGE,
                "version": VERSION,
                "ts": TS,
                "artifact_key": ARTIFACT_KEY,
                "summary": SUMMARY,
            },
        ),
    ]
    assert errors(ctx["events"].events[1][1], "events/stage.completed.schema.json") == []


async def test_failed_reports_error_and_publishes_event(ctx, frozen_now) -> None:
    t = [0.0]
    reporter = _reporter(ctx, t)
    await reporter.started()
    await reporter.failed(ERROR_BODY)
    assert ctx["api"].results == [
        {
            "stage_run_id": STAGE_RUN_ID,
            "status": "failed",
            "artifact_key": None,
            "summary": None,
            "error": ERROR_BODY,
            "started_at": TS,
            "finished_at": TS,
        }
    ]
    assert ctx["events"].events == [
        (RUN_ID, _started_event()),
        (
            RUN_ID,
            {
                "type": "stage.failed",
                "run_id": RUN_ID,
                "stage_run_id": STAGE_RUN_ID,
                "stage": STAGE,
                "version": VERSION,
                "ts": TS,
                "error": ERROR_BODY,
            },
        ),
    ]
    assert errors(ctx["events"].events[1][1], "events/stage.failed.schema.json") == []


async def test_failed_publishes_event_even_when_callback_fails(ctx, frozen_now) -> None:
    t = [0.0]
    reporter = _reporter(ctx, t)
    ctx["api"].fail_results = True
    await reporter.started()
    await reporter.failed(ERROR_BODY)
    assert ctx["api"].results == []
    assert ctx["api"].calls == ["started", "stage.started", "result", "stage.failed"]
    assert ctx["events"].events == [
        (RUN_ID, _started_event()),
        (
            RUN_ID,
            {
                "type": "stage.failed",
                "run_id": RUN_ID,
                "stage_run_id": STAGE_RUN_ID,
                "stage": STAGE,
                "version": VERSION,
                "ts": TS,
                "error": ERROR_BODY,
            },
        ),
    ]
