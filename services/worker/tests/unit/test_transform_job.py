"""Unit tests for the transform job (rag_worker.jobs.transform.transform): apply the params.strategy
to the question (none skips the LLM, else build_transform_pipeline + the fake chat reply), store the
transform artifact and report the done/failed stage result. The transform job is a stub — every test
here is red until T-worker-029."""

import copy
import json
from typing import Any

from haystack.dataclasses import ChatMessage

from rag_worker import keys
from rag_worker.jobs.transform import transform
from rag_worker.models import fakes
from rag_worker.pipelines.prompts import HYDE_SYSTEM, MULTI_QUERY_SYSTEM
from tests.conftest import FIXTURES
from tests.contract import errors

RUN_ID = "019a4b2c-2000-7c00-9000-000000000002"
STAGE_RUN_ID = "019a4b2c-2100-7c00-9000-000000000003"
VERSION = 1
TS = "2026-11-01T18:22:05.123Z"
ARTIFACT_KEY = keys.artifact_key(RUN_ID, "transform", VERSION)
PAYLOAD = json.loads((FIXTURES / "jobs__transform.json").read_text())
QUESTION = PAYLOAD["question"]
MODEL = {"provider": PAYLOAD["chat"]["provider"], "model": PAYLOAD["chat"]["model"]}
REPLY = f"Fake answer to: {QUESTION} [1]"
LLM_ERROR_BODY = {
    "code": "LLM_ERROR",
    "message": "Chat model call failed",
    "details": {"reason": "boom"},
}


def _payload(strategy: str, num_queries: int = 3) -> dict[str, Any]:
    """The jobs__transform fixture with the given params (TransformParams needs num_queries for
    every strategy); the result must validate against jobs/transform.schema.json."""
    payload = copy.deepcopy(PAYLOAD)
    payload["params"] = {"strategy": strategy, "num_queries": num_queries}
    return payload


def _stage_event(event_type: str, **extra: Any) -> dict[str, Any]:
    return {
        "type": event_type,
        "run_id": RUN_ID,
        "stage_run_id": STAGE_RUN_ID,
        "stage": "transform",
        "version": VERSION,
        "ts": TS,
        **extra,
    }


async def _run(ctx: dict[str, Any], payload: dict[str, Any]) -> tuple[dict[str, Any], Any]:
    """Run the transform job and read the artifact back from the artifacts bucket (None when the
    job failed and stored nothing)."""
    result = await transform(ctx, payload)
    bucket = ctx["settings"].s3_bucket_artifacts
    if (bucket, ARTIFACT_KEY) not in ctx["store"].objects:
        return result, None
    return result, await ctx["store"].get_json(bucket, ARTIFACT_KEY)


async def test_none_skips_llm_and_passes_question_through(ctx, frozen_now, monkeypatch) -> None:
    payload = _payload(strategy="none")
    assert errors(payload, "jobs/transform.schema.json") == []

    def _boom(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("the chat model must not be called for strategy none")

    monkeypatch.setattr(ctx["models"], "chat_generator", _boom)
    result, artifact = await _run(ctx, payload)

    assert result["status"] == "done"
    assert artifact == {
        "schema_version": 1,
        "stage": "transform",
        "strategy": "none",
        "question": QUESTION,
        "queries": [QUESTION],
        "hyde_document": None,
        "messages": [],
        "model": None,
    }
    assert errors(artifact, "artifacts/transform.schema.json") == []
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
    assert ctx["running"] == 0


async def test_multi_query_artifact(ctx, frozen_now) -> None:
    payload = _payload(strategy="multi_query")
    assert errors(payload, "jobs/transform.schema.json") == []

    result, artifact = await _run(ctx, payload)

    assert result["status"] == "done"
    assert errors(artifact, "artifacts/transform.schema.json") == []
    assert artifact["schema_version"] == 1
    assert artifact["stage"] == "transform"
    assert artifact["strategy"] == "multi_query"
    assert artifact["question"] == QUESTION
    assert artifact["queries"] == [QUESTION, REPLY]
    assert artifact["queries"][0] == QUESTION
    assert artifact["hyde_document"] is None
    assert artifact["messages"] == [
        {"role": "system", "content": MULTI_QUERY_SYSTEM.replace("{{ n }}", "3")},
        {"role": "user", "content": QUESTION},
    ]
    assert artifact["messages"][0]["role"] == "system"
    assert artifact["model"] == MODEL
    assert ctx["running"] == 0


async def test_hyde_document_matches_queries(ctx, frozen_now) -> None:
    payload = _payload(strategy="hyde")
    assert errors(payload, "jobs/transform.schema.json") == []

    result, artifact = await _run(ctx, payload)

    assert result["status"] == "done"
    assert artifact["queries"] == [REPLY]
    assert artifact["hyde_document"] == artifact["queries"][0]
    assert artifact["hyde_document"] == REPLY
    assert artifact["messages"] == [
        {"role": "system", "content": HYDE_SYSTEM},
        {"role": "user", "content": QUESTION},
    ]
    assert artifact["model"] == MODEL
    assert ctx["running"] == 0


async def test_summary_counts_queries(ctx, frozen_now) -> None:
    payload = _payload(strategy="multi_query")
    assert errors(payload, "jobs/transform.schema.json") == []

    result, artifact = await _run(ctx, payload)

    assert result["status"] == "done"
    assert result["summary"] == {"stage": "transform", "queries": len(artifact["queries"])}
    assert result["summary"] == {"stage": "transform", "queries": 2}
    assert errors(result["summary"], "shared/summary.schema.json#/$defs/TransformSummary") == []
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
    assert ctx["running"] == 0


async def test_chat_generator_error_fails_with_llm_error(ctx, frozen_now, monkeypatch) -> None:
    payload = _payload(strategy="multi_query")
    assert errors(payload, "jobs/transform.schema.json") == []

    def _boom(messages: list[ChatMessage]) -> str:
        raise RuntimeError("boom")

    monkeypatch.setattr(fakes, "fake_reply", _boom)
    result, artifact = await _run(ctx, payload)

    assert result == {"status": "failed", "code": "LLM_ERROR"}
    assert ctx["api"].started == [(STAGE_RUN_ID, TS)]
    assert ctx["api"].results == [
        {
            "stage_run_id": STAGE_RUN_ID,
            "status": "failed",
            "artifact_key": None,
            "summary": None,
            "error": LLM_ERROR_BODY,
            "started_at": TS,
            "finished_at": TS,
        }
    ]
    assert ctx["api"].calls == ["started", "stage.started", "result", "stage.failed"]
    assert ctx["events"].events == [
        (RUN_ID, _stage_event("stage.started")),
        (RUN_ID, _stage_event("stage.failed", error=LLM_ERROR_BODY)),
    ]
    assert ctx["events"].types() == ["stage.started", "stage.failed"]
    assert errors(ctx["events"].events[1][1], "events/stage.failed.schema.json") == []
    assert ctx["store"].objects == {}
    assert ctx["running"] == 0
