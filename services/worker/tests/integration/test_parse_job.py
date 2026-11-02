"""Parse job (rag_worker.jobs.parse.parse): read the upload from the store, run the parse pipeline
for the chosen strategy, store the artifact (+ page images + docling.json for docling strategies),
report progress and the stage result. Real Docling models for the docling_layout tests (baked into
worker-dev, slow). The parse job is a stub — every test here is red until T-worker-017."""

import copy
import json
from typing import Any

from rag_worker import keys
from rag_worker.jobs.parse import parse
from tests.conftest import FIXTURES, SAMPLES
from tests.contract import errors

RUN_ID = "019a4b2c-2000-7c00-9000-000000000002"
STAGE_RUN_ID = "019a4b2c-2100-7c00-9000-000000000003"
VERSION = 1
FILE_ID = "019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a01"
S3_KEY = "019a4b2c-1e00-7b00-8000-000000000001/019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a01/q3-report.pdf"
TS = "2026-11-01T18:22:05.123Z"
ARTIFACT_KEY = keys.artifact_key(RUN_ID, "parse", VERSION)
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
PAYLOAD = json.loads((FIXTURES / "jobs__parse.json").read_text())
FILE_NOT_FOUND_BODY = {
    "code": "FILE_NOT_FOUND",
    "message": "File not found",
    "details": {"key": S3_KEY},
}
UNSUPPORTED_BODY = {
    "code": "UNSUPPORTED_FOR_STRATEGY",
    "message": "This file type cannot be processed with the chosen strategy",
    "details": {"mime": "image/png"},
}
PLAIN_TEXTS = [
    "Employee Handbook",
    "Vacation",
    "Every employee has 25 vacation days per year. Unused days expire at the end of March.",
    "Remote work",
    "Remote work is allowed up to three days per week. Equipment is provided by the IT team.",
    "Expenses",
    "Travel expenses are reimbursed within 14 days after the receipt is uploaded.",
]
PLAIN_FULL_TEXT = "\n\n".join(PLAIN_TEXTS)
PLAIN_SUMMARY = {
    "stage": "parse",
    "pages": 0,
    "elements": 7,
    "tables": 0,
    "pictures": 0,
    "chars": len(PLAIN_FULL_TEXT),
    "ocr_used": False,
}


def _plain_element(
    index: int, el_type: str, text: str, level: int | None, section_path: list[str]
) -> dict[str, Any]:
    start = sum(len(t) for t in PLAIN_TEXTS[:index]) + 2 * index
    return {
        "id": f"e-{index:04d}",
        "type": el_type,
        "text": text,
        "page_no": None,
        "bbox": None,
        "heading_level": level,
        "section_path": section_path,
        "table": None,
        "from_ocr": False,
        "char_start": start,
        "char_end": start + len(text),
    }


PLAIN_ELEMENTS = [
    _plain_element(0, "heading", PLAIN_TEXTS[0], 1, []),
    _plain_element(1, "heading", PLAIN_TEXTS[1], 2, ["Employee Handbook"]),
    _plain_element(2, "text", PLAIN_TEXTS[2], None, ["Employee Handbook", "Vacation"]),
    _plain_element(3, "heading", PLAIN_TEXTS[3], 2, ["Employee Handbook"]),
    _plain_element(4, "text", PLAIN_TEXTS[4], None, ["Employee Handbook", "Remote work"]),
    _plain_element(5, "heading", PLAIN_TEXTS[5], 2, ["Employee Handbook"]),
    _plain_element(6, "text", PLAIN_TEXTS[6], None, ["Employee Handbook", "Expenses"]),
]
PLAIN_ARTIFACT = {
    "schema_version": 1,
    "stage": "parse",
    "strategy": "plain_text",
    "file_id": FILE_ID,
    "mime": "text/markdown",
    "ocr_used": False,
    "pages": [],
    "elements": PLAIN_ELEMENTS,
    "full_text": PLAIN_FULL_TEXT,
    "docling_json_key": None,
}


def _event(event_type: str, **extra: Any) -> dict[str, Any]:
    return {
        "type": event_type,
        "run_id": RUN_ID,
        "stage_run_id": STAGE_RUN_ID,
        "stage": "parse",
        "version": 1,
        "ts": TS,
        **extra,
    }


def _payload(filename: str, mime: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(PAYLOAD)
    payload["params"] = params
    payload["file"]["filename"] = filename
    payload["file"]["mime"] = mime
    return payload


def _upload(ctx: dict[str, Any], name: str) -> None:
    bucket = ctx["settings"].s3_bucket_uploads
    ctx["store"].objects[(bucket, S3_KEY)] = (SAMPLES / name).read_bytes()


async def _run_plain(ctx: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    _upload(ctx, "handbook.md")
    payload = _payload("handbook.md", "text/markdown", {"strategy": "plain_text"})
    result = await parse(ctx, payload)
    artifact = await ctx["store"].get_json(ctx["settings"].s3_bucket_artifacts, ARTIFACT_KEY)
    return result, artifact


async def test_plain_text_returns_done_and_stores_valid_artifact(ctx, frozen_now) -> None:
    assert errors(PAYLOAD, "jobs/parse.schema.json") == []

    result, artifact = await _run_plain(ctx)

    assert result == {"status": "done", "summary": PLAIN_SUMMARY}
    uploads = ctx["settings"].s3_bucket_uploads
    artifacts = ctx["settings"].s3_bucket_artifacts
    assert set(ctx["store"].objects) == {(uploads, S3_KEY), (artifacts, ARTIFACT_KEY)}
    assert ctx["api"].started == [(STAGE_RUN_ID, TS)]
    assert ctx["api"].results == [
        {
            "stage_run_id": STAGE_RUN_ID,
            "status": "done",
            "artifact_key": ARTIFACT_KEY,
            "summary": PLAIN_SUMMARY,
            "error": None,
            "started_at": TS,
            "finished_at": TS,
        }
    ]
    assert artifact == PLAIN_ARTIFACT
    assert errors(artifact, "artifacts/parse.schema.json") == []
    assert errors(PLAIN_SUMMARY, "shared/summary.schema.json#/$defs/ParseSummary") == []
    assert ctx["events"].events == [
        (RUN_ID, _event("stage.started")),
        (
            RUN_ID,
            _event("stage.completed", artifact_key=ARTIFACT_KEY, summary=PLAIN_SUMMARY),
        ),
    ]
    assert errors(ctx["events"].events[0][1], "events/stage.started.schema.json") == []
    assert errors(ctx["events"].events[1][1], "events/stage.completed.schema.json") == []
    assert ctx["running"] == 0


async def test_docling_stores_page_images_and_docling_json(ctx, frozen_now) -> None:
    _upload(ctx, "q3-report.pdf")

    result = await parse(ctx, PAYLOAD)

    assert result["status"] == "done"
    summary = result["summary"]
    uploads = ctx["settings"].s3_bucket_uploads
    artifacts = ctx["settings"].s3_bucket_artifacts
    assert ctx["api"].started == [(STAGE_RUN_ID, TS)]
    assert ctx["api"].results == [
        {
            "stage_run_id": STAGE_RUN_ID,
            "status": "done",
            "artifact_key": ARTIFACT_KEY,
            "summary": summary,
            "error": None,
            "started_at": TS,
            "finished_at": TS,
        }
    ]
    store = ctx["store"]
    docling_key = keys.docling_json_key(RUN_ID, VERSION)
    assert set(store.objects) == {
        (uploads, S3_KEY),
        (artifacts, ARTIFACT_KEY),
        (artifacts, keys.page_image_key(RUN_ID, VERSION, 1)),
        (artifacts, keys.page_image_key(RUN_ID, VERSION, 2)),
        (artifacts, docling_key),
    }
    artifact = await store.get_json(artifacts, ARTIFACT_KEY)
    assert [page["page_no"] for page in artifact["pages"]] == [1, 2]
    for page in artifact["pages"]:
        image_key = keys.page_image_key(RUN_ID, VERSION, page["page_no"])
        assert page["image_key"] == image_key
        assert store.objects[(artifacts, image_key)][:8] == PNG_MAGIC
        assert page["width"] > 0
        assert page["height"] > 0
    assert isinstance(json.loads(store.objects[(artifacts, docling_key)]), dict)
    assert artifact["strategy"] == "docling_layout"
    assert artifact["file_id"] == FILE_ID
    assert artifact["mime"] == "application/pdf"
    assert artifact["ocr_used"] is False
    assert artifact["docling_json_key"] == docling_key
    elements = artifact["elements"]
    assert summary == {
        "stage": "parse",
        "pages": len(artifact["pages"]),
        "elements": len(elements),
        "tables": sum(1 for element in elements if element["type"] == "table"),
        "pictures": sum(1 for element in elements if element["type"] == "picture"),
        "chars": len(artifact["full_text"]),
        "ocr_used": False,
    }
    assert errors(summary, "shared/summary.schema.json#/$defs/ParseSummary") == []
    assert errors(artifact, "artifacts/parse.schema.json") == []
    events = ctx["events"].events
    assert set(ctx["events"].types()) <= {"stage.started", "stage.progress", "stage.completed"}
    assert events[0] == (RUN_ID, _event("stage.started"))
    assert events[-1] == (
        RUN_ID,
        _event("stage.completed", artifact_key=ARTIFACT_KEY, summary=summary),
    )
    assert ctx["running"] == 0


async def test_element_char_spans_point_into_full_text(ctx, frozen_now) -> None:
    result, artifact = await _run_plain(ctx)

    assert result == {"status": "done", "summary": PLAIN_SUMMARY}
    elements = artifact["elements"]
    full_text = artifact["full_text"]
    assert len(elements) == 7
    assert full_text == PLAIN_FULL_TEXT
    for element in elements:
        start = element["char_start"]
        end = element["char_end"]
        assert start is not None
        assert end is not None
        assert full_text[start:end] == element["text"]
    assert "\n\n".join(element["text"] for element in elements) == full_text
    assert (elements[0]["char_start"], elements[0]["char_end"]) == (0, 17)
    assert (elements[1]["char_start"], elements[1]["char_end"]) == (19, 27)


async def test_missing_upload_fails_with_file_not_found(ctx, frozen_now) -> None:
    result = await parse(ctx, PAYLOAD)

    assert result == {"status": "failed", "code": "FILE_NOT_FOUND"}
    assert ctx["api"].started == [(STAGE_RUN_ID, TS)]
    assert ctx["api"].results == [
        {
            "stage_run_id": STAGE_RUN_ID,
            "status": "failed",
            "artifact_key": None,
            "summary": None,
            "error": FILE_NOT_FOUND_BODY,
            "started_at": TS,
            "finished_at": TS,
        }
    ]
    assert ctx["store"].objects == {}
    assert ctx["events"].events == [
        (RUN_ID, _event("stage.started")),
        (RUN_ID, _event("stage.failed", error=FILE_NOT_FOUND_BODY)),
    ]
    assert errors(ctx["events"].events[1][1], "events/stage.failed.schema.json") == []
    assert ctx["running"] == 0


async def test_plain_text_on_image_fails_unsupported_for_strategy(ctx, frozen_now) -> None:
    _upload(ctx, "scan-invoice.png")
    payload = _payload("scan-invoice.png", "image/png", {"strategy": "plain_text"})

    result = await parse(ctx, payload)

    assert result == {"status": "failed", "code": "UNSUPPORTED_FOR_STRATEGY"}
    assert ctx["api"].started == [(STAGE_RUN_ID, TS)]
    assert ctx["api"].results == [
        {
            "stage_run_id": STAGE_RUN_ID,
            "status": "failed",
            "artifact_key": None,
            "summary": None,
            "error": UNSUPPORTED_BODY,
            "started_at": TS,
            "finished_at": TS,
        }
    ]
    assert set(ctx["store"].objects) == {(ctx["settings"].s3_bucket_uploads, S3_KEY)}
    assert ctx["events"].events == [
        (RUN_ID, _event("stage.started")),
        (RUN_ID, _event("stage.failed", error=UNSUPPORTED_BODY)),
    ]
    assert errors(ctx["events"].events[1][1], "events/stage.failed.schema.json") == []
    assert ctx["running"] == 0


async def test_progress_events_reported_during_docling_run(ctx, frozen_now) -> None:
    _upload(ctx, "q3-report.pdf")

    result = await parse(ctx, PAYLOAD)

    assert result["status"] == "done"
    events = ctx["events"].events
    assert events[0][1]["type"] == "stage.started"
    assert events[-1][1]["type"] == "stage.completed"
    progress = [event for _, event in events if event["type"] == "stage.progress"]
    assert len(progress) >= 1
    for event in progress:
        assert event["run_id"] == RUN_ID
        assert event["stage_run_id"] == STAGE_RUN_ID
        assert event["stage"] == "parse"
        assert event["version"] == 1
        assert event["ts"] == TS
        assert 0 <= event["done"] <= event["total"]
        assert event["total"] >= 1
        assert isinstance(event["message"], str) and event["message"]
        assert errors(event, "events/stage.progress.schema.json") == []
    assert progress[-1]["done"] == progress[-1]["total"]
