"""Unit tests for the rerank job (rag_worker.jobs.rerank.rerank): read the retrieve artifact from the
store, rerank its fused hits with the ranker when params.enabled (else pass the before order through),
store the rerank artifact and report the done/failed stage result. The rerank job is a stub — every
test here is red until T-worker-035."""

import copy
import json
from typing import Any

from rag_worker import keys
from rag_worker.components.hits import hit_to_document, to_hit
from rag_worker.jobs.rerank import rerank
from tests.conftest import FIXTURES
from tests.contract import errors

RUN_ID = "019a4b2c-2000-7c00-9000-000000000002"
STAGE_RUN_ID = "019a4b2c-2100-7c00-9000-000000000003"
VERSION = 1
TS = "2026-11-01T18:22:05.123Z"
RETRIEVE_KEY = keys.artifact_key(RUN_ID, "retrieve", VERSION)
ARTIFACT_KEY = keys.artifact_key(RUN_ID, "rerank", VERSION)
PAYLOAD = json.loads((FIXTURES / "jobs__rerank.json").read_text())
RETRIEVE = json.loads((FIXTURES / "artifact_retrieve.json").read_text())
BEFORE: list[dict[str, Any]] = [entry["hit"] for entry in RETRIEVE["fused"]]
QUESTION = PAYLOAD["question"]
MODEL = PAYLOAD["model"]
SCORE = 0.285714  # fake ranker: 2 of the 6 query words overlap -> 2 / (1 + 6), round 6
NOT_FOUND_BODY = {
    "code": "ARTIFACT_NOT_FOUND",
    "message": "Stage artifact not found",
    "details": {"key": RETRIEVE_KEY},
}


def _payload(enabled: bool, top_n: int = 2) -> dict[str, Any]:
    """The jobs__rerank fixture with the given params (RerankParams: enabled, top_n); the result must
    validate against jobs/rerank.schema.json."""
    payload = copy.deepcopy(PAYLOAD)
    payload["params"] = {"enabled": enabled, "top_n": top_n}
    return payload


def _stage_event(event_type: str, **extra: Any) -> dict[str, Any]:
    return {
        "type": event_type,
        "run_id": RUN_ID,
        "stage_run_id": STAGE_RUN_ID,
        "stage": "rerank",
        "version": VERSION,
        "ts": TS,
        **extra,
    }


async def _seed_retrieve(ctx: dict[str, Any]) -> None:
    """Store the retrieve fixture at the payload's retrieve_artifact_key, so the job reads exactly what
    the retrieve job would write."""
    await ctx["store"].put_json(
        ctx["settings"].s3_bucket_artifacts, PAYLOAD["retrieve_artifact_key"], RETRIEVE
    )


async def _run(
    ctx: dict[str, Any], payload: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run the rerank job and read the artifact back from the artifacts bucket."""
    result = await rerank(ctx, payload)
    artifact = await ctx["store"].get_json(ctx["settings"].s3_bucket_artifacts, ARTIFACT_KEY)
    return result, artifact


async def test_enabled_after_reranked_to_top_n(ctx, frozen_now) -> None:
    payload = _payload(enabled=True, top_n=2)
    assert errors(payload, "jobs/rerank.schema.json") == []
    assert PAYLOAD["retrieve_artifact_key"] == RETRIEVE_KEY
    assert len(BEFORE) == 4

    await _seed_retrieve(ctx)
    result, artifact = await _run(ctx, payload)

    assert result["status"] == "done"
    assert artifact == {
        "schema_version": 1,
        "stage": "rerank",
        "enabled": True,
        "model": MODEL,
        "top_n": 2,
        "query": QUESTION,
        "before": BEFORE,
        "after": [
            {
                "hit": to_hit(hit_to_document(BEFORE[2]), 1, SCORE),
                "previous_rank": 3,
                "rerank_score": SCORE,
            },
            {
                "hit": to_hit(hit_to_document(BEFORE[1]), 2, SCORE),
                "previous_rank": 2,
                "rerank_score": SCORE,
            },
        ],
    }
    assert len(artifact["after"]) == 2
    assert errors(artifact, "artifacts/rerank.schema.json") == []
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
    assert ctx["api"].calls == ["started", "stage.started", "result", "stage.completed"]
    assert ctx["events"].events == [
        (RUN_ID, _stage_event("stage.started")),
        (
            RUN_ID,
            _stage_event("stage.completed", artifact_key=ARTIFACT_KEY, summary=result["summary"]),
        ),
    ]
    assert errors(ctx["events"].events[0][1], "events/stage.started.schema.json") == []
    assert errors(ctx["events"].events[1][1], "events/stage.completed.schema.json") == []
    artifacts = ctx["settings"].s3_bucket_artifacts
    assert set(ctx["store"].objects) == {(artifacts, RETRIEVE_KEY), (artifacts, ARTIFACT_KEY)}
    assert ctx["running"] == 0


async def test_disabled_after_order_equals_before_and_skips_ranker(
    ctx, frozen_now, monkeypatch
) -> None:
    payload = _payload(enabled=False, top_n=2)
    assert errors(payload, "jobs/rerank.schema.json") == []

    def _boom(model: str, top_k: int) -> None:
        raise AssertionError("the ranker must not be built when rerank is disabled")

    monkeypatch.setattr(ctx["models"], "ranker", _boom)
    await _seed_retrieve(ctx)
    result, artifact = await _run(ctx, payload)

    assert result["status"] == "done"
    assert artifact["enabled"] is False
    assert artifact["model"] is None
    assert artifact["after"] == [
        {"hit": BEFORE[0], "previous_rank": 1, "rerank_score": None},
        {"hit": BEFORE[1], "previous_rank": 2, "rerank_score": None},
    ]
    assert errors(artifact, "artifacts/rerank.schema.json") == []
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
    assert ctx["api"].calls == ["started", "stage.started", "result", "stage.completed"]
    assert ctx["events"].events == [
        (RUN_ID, _stage_event("stage.started")),
        (
            RUN_ID,
            _stage_event("stage.completed", artifact_key=ARTIFACT_KEY, summary=result["summary"]),
        ),
    ]
    assert ctx["events"].types() == ["stage.started", "stage.completed"]
    artifacts = ctx["settings"].s3_bucket_artifacts
    assert set(ctx["store"].objects) == {(artifacts, RETRIEVE_KEY), (artifacts, ARTIFACT_KEY)}
    assert ctx["running"] == 0


async def test_summary_counts_before_and_after(ctx, frozen_now) -> None:
    payload = _payload(enabled=True, top_n=2)
    assert errors(payload, "jobs/rerank.schema.json") == []

    await _seed_retrieve(ctx)
    result, artifact = await _run(ctx, payload)

    assert result["status"] == "done"
    assert result["summary"] == {
        "stage": "rerank",
        "enabled": True,
        "in": len(artifact["before"]),
        "out": len(artifact["after"]),
    }
    assert result["summary"] == {"stage": "rerank", "enabled": True, "in": 4, "out": 2}
    assert errors(result["summary"], "shared/summary.schema.json#/$defs/RerankSummary") == []
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
    assert ctx["api"].calls == ["started", "stage.started", "result", "stage.completed"]
    assert ctx["running"] == 0


async def test_missing_retrieve_artifact_fails_artifact_not_found(ctx, frozen_now) -> None:
    assert ctx["store"].objects == {}

    result = await rerank(ctx, PAYLOAD)

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
    assert ctx["api"].calls == ["started", "stage.started", "result", "stage.failed"]
    assert ctx["store"].objects == {}
    assert ctx["events"].events == [
        (RUN_ID, _stage_event("stage.started")),
        (RUN_ID, _stage_event("stage.failed", error=NOT_FOUND_BODY)),
    ]
    assert ctx["events"].types() == ["stage.started", "stage.failed"]
    assert errors(ctx["events"].events[1][1], "events/stage.failed.schema.json") == []
    assert ctx["running"] == 0
