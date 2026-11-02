"""Unit tests for the transform pipeline + transform artifact (services/worker/src/rag_worker/pipelines/transform.py):
build/run the 'prompt' -> 'llm' pipeline over FakeModelSet, and check transform_artifact output against
contracts/artifacts/transform.schema.json. The module is a stub raising NotImplementedError, so every
test here is red until T-worker-028 lands."""

import pytest
from haystack.dataclasses import ChatRole

from rag_worker.contracts_gen.shared.common_schema import ChatModelConfig
from rag_worker.models.registry import FakeModelSet
from rag_worker.pipelines.transform import build_transform_pipeline, transform_artifact
from tests.contract import errors

QUESTION = "What was our Q3 revenue?"
OLLAMA = ChatModelConfig(
    provider="ollama", model="qwen3:8b", base_url="http://ollama:11434", api_key=None
)
MODEL = {"provider": "ollama", "model": "qwen3:8b"}
MESSAGES = [
    {"role": "system", "content": "You rewrite a user question into one precise search query."},
    {"role": "user", "content": QUESTION},
]


def test_none_artifact_is_passthrough() -> None:
    artifact = transform_artifact("none", QUESTION, None, [], None, 3)
    assert errors(artifact, "artifacts/transform.schema.json") == []
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


def test_rewrite_uses_first_nonempty_reply_line_or_question() -> None:
    artifact = transform_artifact(
        "rewrite", QUESTION, "  better query \n second", MESSAGES, OLLAMA, 3
    )
    assert errors(artifact, "artifacts/transform.schema.json") == []
    assert artifact["queries"] == ["better query"]
    assert artifact["hyde_document"] is None
    assert artifact["messages"] == MESSAGES
    assert artifact["model"] == MODEL

    empty = transform_artifact("rewrite", QUESTION, "", MESSAGES, OLLAMA, 3)
    assert empty["queries"] == [QUESTION]
    assert empty["model"] == MODEL


def test_multi_query_strips_prefixes_dedupes_and_drops_question() -> None:
    messages = [
        {"role": "system", "content": "You write 3 different search queries."},
        {"role": "user", "content": "q"},
    ]
    artifact = transform_artifact("multi_query", "q", "1. a\n- b\n\nb\nq", messages, OLLAMA, 3)
    assert errors(artifact, "artifacts/transform.schema.json") == []
    assert artifact["question"] == "q"
    assert artifact["queries"] == ["q", "a", "b"]
    assert artifact["hyde_document"] is None
    assert artifact["messages"] == messages
    assert artifact["model"] == MODEL


def test_hyde_queries_and_document_are_stripped_reply() -> None:
    artifact = transform_artifact("hyde", QUESTION, "  passage ", MESSAGES, OLLAMA, 3)
    assert errors(artifact, "artifacts/transform.schema.json") == []
    assert artifact["queries"] == ["passage"]
    assert artifact["hyde_document"] == "passage"
    assert artifact["messages"] == MESSAGES
    assert artifact["model"] == MODEL


def test_build_pipeline_multi_query_runs_and_shapes_reply() -> None:
    pipeline = build_transform_pipeline("multi_query", OLLAMA, FakeModelSet())
    assert set(pipeline.to_dict()["components"]) == {"prompt", "llm"}
    out = pipeline.run({"prompt": {"question": "q", "n": 3}})
    [system, user] = out["prompt"]
    assert system.role == ChatRole.SYSTEM
    assert "3 different search queries" in system.text
    assert user.role == ChatRole.USER
    assert user.text == "q"
    [reply] = out["llm"]["replies"]
    assert reply.text == "Fake answer to: q [1]"


def test_build_pipeline_none_raises_value_error() -> None:
    with pytest.raises(ValueError):
        build_transform_pipeline("none", OLLAMA, FakeModelSet())
