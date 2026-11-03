"""Unit tests for the generate job (rag_worker.jobs.generate.generate): read the rerank or retrieve
artifact named by the payload, select context within the token budget (bge-m3 tokenizer), stream the
fake chat reply as generate.token events, store the generate artifact and report the done/failed
stage result. The generate job is a stub — every test here is red until T-worker-038."""

import copy
import json
from typing import Any

from haystack.dataclasses import ChatMessage

from rag_worker import keys
from rag_worker.components.context_builder import select_context
from rag_worker.jobs.generate import generate
from rag_worker.models import fakes
from rag_worker.pipelines.prompts import ANSWER_SYSTEM
from tests.conftest import FIXTURES
from tests.contract import errors

RUN_ID = "019a4b2c-2000-7c00-9000-000000000002"
STAGE_RUN_ID = "019a4b2c-2100-7c00-9000-000000000003"
VERSION = 1
TS = "2026-11-01T18:22:05.123Z"
ARTIFACT_KEY = keys.artifact_key(RUN_ID, "generate", VERSION)
RERANK_KEY = keys.artifact_key(RUN_ID, "rerank", VERSION)
RETRIEVE_KEY = keys.artifact_key(RUN_ID, "retrieve", VERSION)
PAYLOAD = json.loads((FIXTURES / "jobs__generate.json").read_text())
RERANK = json.loads((FIXTURES / "artifact_rerank.json").read_text())
RETRIEVE = json.loads((FIXTURES / "artifact_retrieve.json").read_text())
QUESTION = PAYLOAD["question"]
# FakeChatGenerator answers 'Fake answer to: <first line of the user message> [1]'; the user
# message rendered from prompts.ANSWER_USER starts with 'Context:'.
ANSWER = "Fake answer to: Context: [1]"
TOKENS = ["Fake ", "answer ", "to: ", "Context: ", "[1]"]


def _payload(context_source: str, max_context_tokens: int = 4000) -> dict[str, Any]:
    """The jobs__generate fixture reading the rerank or retrieve artifact of the same run."""
    payload = copy.deepcopy(PAYLOAD)
    payload["context_source"] = context_source
    payload["context_artifact_key"] = RERANK_KEY if context_source == "rerank" else RETRIEVE_KEY
    payload["params"]["max_context_tokens"] = max_context_tokens
    return payload


def _token_count(ctx: dict[str, Any], text: str) -> int:
    tok = ctx["models"].tokenizer("bge-m3")
    return len(tok.encode(text, add_special_tokens=False).ids)


def _long_rerank() -> dict[str, Any]:
    """The rerank fixture with every hit's content repeated 6x, so a few hits exceed the minimum
    max_context_tokens (256) and the budget has to drop some."""
    rerank = copy.deepcopy(RERANK)
    for a in rerank["after"]:
        a["hit"]["content"] = " ".join([a["hit"]["content"]] * 6)
    return rerank


async def _seed(ctx: dict[str, Any], rerank: dict[str, Any] = RERANK) -> None:
    """Store the rerank and retrieve fixtures where the rerank/retrieve jobs would write them."""
    bucket = ctx["settings"].s3_bucket_artifacts
    await ctx["store"].put_json(bucket, RERANK_KEY, rerank)
    await ctx["store"].put_json(bucket, RETRIEVE_KEY, RETRIEVE)


async def _run(
    ctx: dict[str, Any], payload: dict[str, Any], rerank: dict[str, Any] = RERANK
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Seed the upstream artifacts, run the generate job and read the artifact back."""
    await _seed(ctx, rerank)
    result = await generate(ctx, payload)
    bucket = ctx["settings"].s3_bucket_artifacts
    if (bucket, ARTIFACT_KEY) not in ctx["store"].objects:
        return result, None
    return result, await ctx["store"].get_json(bucket, ARTIFACT_KEY)


async def test_rerank_context_uses_after_hits_and_artifact_validates(ctx, frozen_now) -> None:
    payload = _payload("rerank")
    assert errors(payload, "jobs/generate.schema.json") == []

    result, artifact = await _run(ctx, payload)

    assert result["status"] == "done"
    assert artifact is not None
    assert errors(artifact, "artifacts/generate.schema.json") == []
    assert [c["hit"] for c in artifact["context"]] == [a["hit"] for a in RERANK["after"]]
    assert [c["n"] for c in artifact["context"]] == list(range(1, len(RERANK["after"]) + 1))
    assert artifact["budget"]["chunks_included"] == len(RERANK["after"])
    assert artifact["budget"]["chunks_dropped"] == 0
    assert artifact["answer"] == ANSWER
    assert artifact["citations"] == [1]
    assert artifact["model"] == {
        "provider": PAYLOAD["chat"]["provider"],
        "model": PAYLOAD["chat"]["model"],
    }
    assert ctx["api"].calls[:2] == ["started", "stage.started"]
    assert ctx["api"].calls[-2:] == ["result", "stage.completed"]
    assert ctx["running"] == 0


async def test_retrieve_context_uses_fused_hits(ctx, frozen_now) -> None:
    payload = _payload("retrieve")
    assert errors(payload, "jobs/generate.schema.json") == []

    result, artifact = await _run(ctx, payload)

    assert result["status"] == "done"
    assert artifact is not None
    assert [c["hit"] for c in artifact["context"]] == [f["hit"] for f in RETRIEVE["fused"]]
    assert [c["n"] for c in artifact["context"]] == list(range(1, len(RETRIEVE["fused"]) + 1))
    assert errors(artifact, "artifacts/generate.schema.json") == []


async def test_token_events_contiguous_from_zero_and_join_to_answer(ctx, frozen_now) -> None:
    result, artifact = await _run(ctx, _payload("rerank"))

    assert result["status"] == "done"
    assert artifact is not None
    tokens = [e for _, e in ctx["events"].events if e["type"] == "generate.token"]
    assert [e["index"] for e in tokens] == list(range(len(TOKENS)))
    assert [e["text"] for e in tokens] == TOKENS
    assert "".join(e["text"] for e in tokens) == artifact["answer"]
    for event in tokens:
        assert errors(event, "events/generate.token.schema.json") == []
        assert event["run_id"] == RUN_ID
        assert event["stage_run_id"] == STAGE_RUN_ID
        assert event["stage"] == "generate"
        assert event["version"] == VERSION
        assert event["ts"] == TS
    types = ctx["events"].types()
    assert types[0] == "stage.started"
    assert types[-1] == "stage.completed"


async def test_budget_counts_with_bge_m3_tokenizer_and_drops_overflow(ctx, frozen_now) -> None:
    rerank = _long_rerank()
    hits = [a["hit"] for a in rerank["after"]]
    counts = [_token_count(ctx, h["content"]) for h in hits]
    budget = 256  # minimum allowed max_context_tokens
    included, used, dropped = select_context(hits, counts, budget)
    assert 1 <= len(included) < len(hits)
    assert dropped >= 1

    result, artifact = await _run(ctx, _payload("rerank", max_context_tokens=budget), rerank)

    assert result["status"] == "done"
    assert artifact is not None
    assert artifact["budget"] == {
        "max_context_tokens": budget,
        "system_tokens": _token_count(ctx, ANSWER_SYSTEM),
        "question_tokens": _token_count(ctx, QUESTION),
        "used_context_tokens": used,
        "chunks_included": len(included),
        "chunks_dropped": dropped,
    }
    assert artifact["budget"]["used_context_tokens"] <= budget
    assert artifact["context"] == included
    assert sum(c["tokens"] for c in artifact["context"]) == used
    assert errors(artifact, "artifacts/generate.schema.json") == []


async def test_summary_from_fake_usage(ctx, frozen_now) -> None:
    result, artifact = await _run(ctx, _payload("rerank"))

    assert result["status"] == "done"
    assert artifact is not None
    prompt_tokens = sum(len(fakes.words(m["content"])) for m in artifact["messages"])
    completion_tokens = len(fakes.words(ANSWER))
    assert artifact["usage"] == {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }
    assert result["summary"] == {
        "stage": "generate",
        "answer_chars": len(ANSWER),
        "citations": 1,
        "chunks_included": len(RERANK["after"]),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }
    assert errors(result["summary"], "shared/summary.schema.json#/$defs/GenerateSummary") == []
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


async def test_chat_generator_error_fails_with_llm_error(ctx, frozen_now, monkeypatch) -> None:
    def _boom(messages: list[ChatMessage]) -> str:
        raise RuntimeError("boom")

    monkeypatch.setattr(fakes, "fake_reply", _boom)
    result, artifact = await _run(ctx, _payload("rerank"))

    assert result == {"status": "failed", "code": "LLM_ERROR"}
    assert artifact is None
    [failed] = ctx["api"].results
    assert failed["status"] == "failed"
    assert failed["artifact_key"] is None
    assert failed["error"]["code"] == "LLM_ERROR"
    assert failed["error"]["message"] == "Chat model call failed"
    assert ctx["api"].calls == ["started", "stage.started", "result", "stage.failed"]
    assert ctx["events"].types() == ["stage.started", "stage.failed"]
    assert errors(ctx["events"].events[1][1], "events/stage.failed.schema.json") == []
    assert ctx["running"] == 0
