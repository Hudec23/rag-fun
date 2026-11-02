"""Unit tests for the generate pipeline + artifact (services/worker/src/rag_worker/pipelines/generate.py):
build/run the 'prompt' -> 'llm' pipeline over FakeModelSet (streaming callback included), and check
generate_artifact output against contracts/artifacts/generate.schema.json. The module is a stub
raising NotImplementedError, so every test here is red until T-worker-037 lands."""

import json

from haystack.dataclasses import ChatRole, StreamingChunk

from rag_worker.contracts_gen.shared.common_schema import ChatModelConfig
from rag_worker.models.registry import FakeModelSet
from rag_worker.pipelines.generate import build_generate_pipeline, generate_artifact
from rag_worker.pipelines.prompts import ANSWER_SYSTEM
from tests.conftest import FIXTURES
from tests.contract import errors

OLLAMA = ChatModelConfig(
    provider="ollama", model="qwen3:8b", base_url="http://ollama:11434", api_key=None
)
MODEL = {"provider": "ollama", "model": "qwen3:8b"}
PROMPT_INPUT = {"context": [{"n": 1, "text": "x"}], "question": "q"}
REPLY = "Fake answer to: Context: [1]"
MESSAGES = [
    {"role": "system", "content": ANSWER_SYSTEM},
    {"role": "user", "content": "Context:\n[1] x\n\nQuestion: q"},
]
BUDGET = {
    "max_context_tokens": 4000,
    "system_tokens": 60,
    "question_tokens": 8,
    "used_context_tokens": 40,
    "chunks_included": 1,
    "chunks_dropped": 0,
}
GEN = json.loads((FIXTURES / "artifact_generate.json").read_text())
CONTEXT = [{"n": 1, "hit": GEN["context"][0]["hit"], "tokens": 40}]


def test_build_pipeline_runs_prompt_and_llm_and_streams_chunks() -> None:
    streamed: list[str] = []

    def on_chunk(chunk: StreamingChunk) -> None:
        streamed.append(chunk.content)

    pipeline = build_generate_pipeline(OLLAMA, 0.2, 100, FakeModelSet(), on_chunk)
    assert set(pipeline.to_dict()["components"]) == {"prompt", "llm"}
    out = pipeline.run({"prompt": PROMPT_INPUT})
    [reply] = out["llm"]["replies"]
    assert reply.text == REPLY
    assert "".join(streamed) == REPLY


def test_prompt_messages_are_answer_system_and_rendered_user() -> None:
    pipeline = build_generate_pipeline(OLLAMA, 0.2, 100, FakeModelSet(), None)
    out = pipeline.run({"prompt": PROMPT_INPUT})
    [system, user] = out["prompt"]
    assert system.role == ChatRole.SYSTEM
    assert system.text == ANSWER_SYSTEM
    assert user.role == ChatRole.USER
    assert "[1] x" in user.text
    assert "Question: q" in user.text


def test_artifact_citations_parse_markers_within_context_and_validates() -> None:
    usage = {"prompt_tokens": 210, "completion_tokens": 18}
    artifact = generate_artifact(OLLAMA, MESSAGES, BUDGET, CONTEXT, "a [1] [2]", usage)
    assert artifact["schema_version"] == 1
    assert artifact["stage"] == "generate"
    assert artifact["model"] == MODEL
    assert artifact["messages"] == MESSAGES
    assert artifact["budget"] == BUDGET
    assert artifact["context"] == CONTEXT
    assert artifact["answer"] == "a [1] [2]"
    assert artifact["citations"] == [1]
    assert artifact["usage"] == usage
    assert errors(artifact, "artifacts/generate.schema.json") == []


def test_artifact_usage_is_passthrough_and_allows_nulls() -> None:
    usage = {"prompt_tokens": None, "completion_tokens": None}
    artifact = generate_artifact(OLLAMA, MESSAGES, BUDGET, CONTEXT, "a [1]", usage)
    assert artifact["citations"] == [1]
    assert artifact["usage"] == usage
    assert errors(artifact, "artifacts/generate.schema.json") == []
