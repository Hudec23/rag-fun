"""Unit tests for the chunk job (rag_worker.jobs.chunk.chunk): read the parse artifact from the
store, run the chunk pipeline for the payload's strategy, store the chunk artifact and report the
done/failed stage result. The chunk job is a stub — every test here is red until T-worker-022."""

import copy
import json
from typing import Any

from docling_core.types.doc import DocItemLabel, DoclingDocument, Size

from rag_worker import keys
from rag_worker.jobs.chunk import chunk
from rag_worker.viz.stats import chunk_stats
from tests.conftest import FIXTURES
from tests.contract import errors

RUN_ID = "019a4b2c-2000-7c00-9000-000000000002"
STAGE_RUN_ID = "019a4b2c-2100-7c00-9000-000000000003"
VERSION = 1
FILE_ID = "019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a01"
TS = "2026-11-01T18:22:05.123Z"
PARSE_KEY = keys.artifact_key(RUN_ID, "parse", VERSION)
DOC_LING_KEY = keys.docling_json_key(RUN_ID, VERSION)
ARTIFACT_KEY = keys.artifact_key(RUN_ID, "chunk", VERSION)
CUSTOM_DOC_LING_KEY = f"{RUN_ID}/parse/v1/custom-docling.json"
PAYLOAD = json.loads((FIXTURES / "jobs__chunk.json").read_text())
PARSE = json.loads((FIXTURES / "artifact_parse.json").read_text())
NOT_FOUND_BODY = {
    "code": "ARTIFACT_NOT_FOUND",
    "message": "Stage artifact not found",
    "details": {"key": PARSE_KEY},
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


def _report_doc() -> DoclingDocument:
    doc = DoclingDocument(name="q3-report")
    doc.add_page(page_no=1, size=Size(width=612, height=792))
    doc.add_page(page_no=2, size=Size(width=612, height=792))
    doc.add_title("Q3 Report")
    doc.add_heading("Overview", level=1)
    doc.add_text(
        label=DocItemLabel.TEXT,
        text="Revenue grew by twelve percent compared with the same quarter last year overall.",
    )
    doc.add_text(
        label=DocItemLabel.TEXT,
        text="The main driver was expansion of the enterprise business segment across three regions.",
    )
    doc.add_text(
        label=DocItemLabel.TEXT,
        text="Costs stayed flat in absolute terms while headcount grew modestly through the quarter.",
    )
    doc.add_heading("Details", level=2)
    doc.add_text(
        label=DocItemLabel.TEXT,
        text="Engineering spent the quarter consolidating the internal build pipeline and tooling stack.",
    )
    doc.add_text(
        label=DocItemLabel.TEXT,
        text="Customer support tickets fell by roughly nine percent after the new onboarding flow shipped.",
    )
    doc.add_text(
        label=DocItemLabel.TEXT,
        text="Marketing launched two campaigns targeting mid-market accounts in the second half of the quarter.",
    )
    return doc


async def _seed_parse(ctx: dict[str, Any], parse: dict[str, Any] | None = None) -> None:
    """Store the parse artifact at the payload's parse_artifact_key (and the docling JSON it points
    to, built from _report_doc), so the chunk job can read exactly what the parse job would write."""
    if parse is None:
        parse = PARSE
    store = ctx["store"]
    bucket = ctx["settings"].s3_bucket_artifacts
    await store.put_json(bucket, PAYLOAD["parse_artifact_key"], parse)
    if parse["docling_json_key"] is not None:
        await store.put_bytes(
            bucket,
            parse["docling_json_key"],
            _report_doc().model_dump_json().encode(),
            "application/json",
        )


async def _run(
    ctx: dict[str, Any], payload: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    result = await chunk(ctx, payload)
    artifact = await ctx["store"].get_json(ctx["settings"].s3_bucket_artifacts, ARTIFACT_KEY)
    return result, artifact


async def test_done_copies_source_text_and_parse_strategy(ctx, frozen_now) -> None:
    assert errors(PAYLOAD, "jobs/chunk.schema.json") == []
    assert PAYLOAD["parse_artifact_key"] == PARSE_KEY
    assert PARSE["docling_json_key"] == DOC_LING_KEY

    await _seed_parse(ctx)
    result, artifact = await _run(ctx, PAYLOAD)

    assert result["status"] == "done"
    store = ctx["store"]
    artifacts = ctx["settings"].s3_bucket_artifacts
    assert set(store.objects) == {
        (artifacts, PARSE_KEY),
        (artifacts, DOC_LING_KEY),
        (artifacts, ARTIFACT_KEY),
    }
    assert artifact["schema_version"] == 1
    assert artifact["stage"] == "chunk"
    assert artifact["strategy"] == "recursive"
    assert artifact["params"] == PAYLOAD["params"]
    assert artifact["parse_strategy"] == PARSE["strategy"]
    assert artifact["source_text"] == PARSE["full_text"]
    assert artifact["semantic"] is None
    assert errors(artifact, "artifacts/chunk.schema.json") == []
    assert ctx["api"].started == [(STAGE_RUN_ID, TS)]
    assert ctx["api"].results == [
        {
            "stage_run_id": STAGE_RUN_ID,
            "status": "done",
            "artifact_key": ARTIFACT_KEY,
            "summary": result["summary"],
            "error": None,
            "started_at": TS,
            "finished_at": TS,
        }
    ]
    assert ctx["events"].events == [
        (RUN_ID, _stage_event("stage.started")),
        (
            RUN_ID,
            _stage_event("stage.completed", artifact_key=ARTIFACT_KEY, summary=result["summary"]),
        ),
    ]
    assert errors(ctx["events"].events[0][1], "events/stage.started.schema.json") == []
    assert errors(ctx["events"].events[1][1], "events/stage.completed.schema.json") == []
    assert ctx["running"] == 0


async def test_summary_consistent_with_artifact_stats(ctx, frozen_now) -> None:
    await _seed_parse(ctx)
    result, artifact = await _run(ctx, PAYLOAD)

    assert result["status"] == "done"
    stats = artifact["stats"]
    assert stats["count"] == len(artifact["chunks"])
    assert result["summary"] == {
        "stage": "chunk",
        "chunks": stats["count"],
        "min_chars": stats["min_chars"],
        "max_chars": stats["max_chars"],
        "mean_chars": stats["mean_chars"],
    }
    assert errors(result["summary"], "shared/summary.schema.json#/$defs/ChunkSummary") == []
    assert ctx["api"].started == [(STAGE_RUN_ID, TS)]
    assert ctx["api"].results == [
        {
            "stage_run_id": STAGE_RUN_ID,
            "status": "done",
            "artifact_key": ARTIFACT_KEY,
            "summary": result["summary"],
            "error": None,
            "started_at": TS,
            "finished_at": TS,
        }
    ]
    assert ctx["events"].events == [
        (RUN_ID, _stage_event("stage.started")),
        (
            RUN_ID,
            _stage_event("stage.completed", artifact_key=ARTIFACT_KEY, summary=result["summary"]),
        ),
    ]
    assert errors(ctx["events"].events[0][1], "events/stage.started.schema.json") == []
    assert errors(ctx["events"].events[1][1], "events/stage.completed.schema.json") == []
    assert ctx["running"] == 0


async def test_doc_ids_zero_padded_and_stats_from_chunk_stats(ctx, frozen_now) -> None:
    assert FILE_ID == PAYLOAD["file"]["file_id"]

    await _seed_parse(ctx)
    result, artifact = await _run(ctx, PAYLOAD)

    assert result["status"] == "done"
    chunks = artifact["chunks"]
    assert len(chunks) >= 1
    expected_doc_ids = [keys.doc_id(FILE_ID, index) for index in range(len(chunks))]
    assert [c["doc_id"] for c in chunks] == expected_doc_ids
    assert chunks[0]["doc_id"] == f"{FILE_ID}:00000"
    assert [c["index"] for c in chunks] == list(range(len(chunks)))
    assert artifact["stats"] == chunk_stats([c["char_count"] for c in chunks])
    assert ctx["api"].started == [(STAGE_RUN_ID, TS)]
    assert ctx["api"].results == [
        {
            "stage_run_id": STAGE_RUN_ID,
            "status": "done",
            "artifact_key": ARTIFACT_KEY,
            "summary": result["summary"],
            "error": None,
            "started_at": TS,
            "finished_at": TS,
        }
    ]
    assert ctx["events"].events == [
        (RUN_ID, _stage_event("stage.started")),
        (
            RUN_ID,
            _stage_event("stage.completed", artifact_key=ARTIFACT_KEY, summary=result["summary"]),
        ),
    ]
    assert errors(ctx["events"].events[0][1], "events/stage.started.schema.json") == []
    assert errors(ctx["events"].events[1][1], "events/stage.completed.schema.json") == []
    assert ctx["running"] == 0


async def test_structure_reads_docling_json_from_parse_artifact(ctx, frozen_now) -> None:
    payload = copy.deepcopy(PAYLOAD)
    payload["params"] = {"strategy": "structure", "max_tokens": 64, "merge_peers": True}
    assert errors(payload, "jobs/chunk.schema.json") == []
    parse = copy.deepcopy(PARSE)
    parse["docling_json_key"] = CUSTOM_DOC_LING_KEY

    await _seed_parse(ctx, parse)
    result, artifact = await _run(ctx, payload)

    assert result["status"] == "done"
    assert artifact["strategy"] == "structure"
    assert artifact["params"] == payload["params"]
    assert artifact["parse_strategy"] == "docling_layout"
    assert artifact["source_text"] == PARSE["full_text"]
    assert errors(artifact, "artifacts/chunk.schema.json") == []
    chunks = artifact["chunks"]
    assert len(chunks) >= 1
    assert all(c["char_start"] is None and c["char_end"] is None for c in chunks)
    assert any("Revenue grew by twelve percent" in c["text"] for c in chunks)
    store = ctx["store"]
    artifacts = ctx["settings"].s3_bucket_artifacts
    assert set(store.objects) == {
        (artifacts, PARSE_KEY),
        (artifacts, CUSTOM_DOC_LING_KEY),
        (artifacts, ARTIFACT_KEY),
    }
    assert ctx["api"].started == [(STAGE_RUN_ID, TS)]
    assert ctx["api"].results == [
        {
            "stage_run_id": STAGE_RUN_ID,
            "status": "done",
            "artifact_key": ARTIFACT_KEY,
            "summary": result["summary"],
            "error": None,
            "started_at": TS,
            "finished_at": TS,
        }
    ]
    assert ctx["events"].events == [
        (RUN_ID, _stage_event("stage.started")),
        (
            RUN_ID,
            _stage_event("stage.completed", artifact_key=ARTIFACT_KEY, summary=result["summary"]),
        ),
    ]
    assert errors(ctx["events"].events[0][1], "events/stage.started.schema.json") == []
    assert errors(ctx["events"].events[1][1], "events/stage.completed.schema.json") == []
    assert ctx["running"] == 0


async def test_missing_parse_artifact_fails_artifact_not_found(ctx, frozen_now) -> None:
    assert ctx["store"].objects == {}

    result = await chunk(ctx, PAYLOAD)

    assert result == {"status": "failed", "code": "ARTIFACT_NOT_FOUND"}
    assert ctx["api"].started == [(STAGE_RUN_ID, TS)]
    assert ctx["api"].results == [
        {
            "stage_run_id": STAGE_RUN_ID,
            "status": "failed",
            "artifact_key": None,
            "summary": None,
            "error": NOT_FOUND_BODY,
            "started_at": TS,
            "finished_at": TS,
        }
    ]
    assert ctx["store"].objects == {}
    assert ctx["events"].events == [
        (RUN_ID, _stage_event("stage.started")),
        (RUN_ID, _stage_event("stage.failed", error=NOT_FOUND_BODY)),
    ]
    assert errors(ctx["events"].events[1][1], "events/stage.failed.schema.json") == []
    assert ctx["running"] == 0
