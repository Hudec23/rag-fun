"""Unit tests for the chunk pipelines (services/worker/src/rag_worker/pipelines/chunk.py):
build per strategy, run against parse-artifact fixtures, assert chunk records."""

import json
from typing import Any

import nltk
import pytest
from haystack import Pipeline

from rag_worker.contracts_gen.shared.common_schema import DenseModelConfig
from rag_worker.errors import WorkerError
from rag_worker.pipelines.chunk import build_chunk_pipeline, run_chunk
from tests.conftest import FIXTURES

DENSE = DenseModelConfig(model="all-minilm", dims=384, ollama_url="http://x")

PARAMS: dict[str, dict[str, Any]] = {
    "fixed": {"strategy": "fixed", "split_by": "word", "length": 4, "overlap": 2},
    "sentence": {"strategy": "sentence", "length": 1, "overlap": 0},
    "recursive": {
        "strategy": "recursive",
        "length": 80,
        "overlap": 0,
        "separators": ["\n\n", "sentence", "\n", " "],
    },
    "semantic": {
        "strategy": "semantic",
        "breakpoint_percentile": 90,
        "min_sentences": 2,
        "max_sentences": 20,
    },
    "structure": {"strategy": "structure", "max_tokens": 512, "merge_peers": True},
    "table": {"strategy": "table", "row_chunks": False, "text_length": 1000, "text_overlap": 100},
}


def _load(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text())


def _build(ctx: dict[str, Any], strategy: str, params: dict[str, Any]) -> Pipeline:
    return build_chunk_pipeline(strategy, params, ctx["models"], DENSE)


def _run(
    ctx: dict[str, Any],
    strategy: str,
    params: dict[str, Any],
    artifact: dict[str, Any],
    docling_json: str | None = None,
) -> dict[str, Any]:
    return run_chunk(
        _build(ctx, strategy, params), strategy, artifact, docling_json, artifact["file_id"]
    )


def test_fixed_word_chunks_overlap_and_span(ctx: dict[str, Any]) -> None:
    artifact = _load("artifact_parse.json")
    chunks = _run(ctx, "fixed", PARAMS["fixed"], artifact)["chunks"]
    assert chunks
    full_text = artifact["full_text"]
    for chunk in chunks:
        assert len(chunk["text"].split()) <= 4
        assert full_text[chunk["char_start"] : chunk["char_end"]] == chunk["text"]
    for prev, nxt in zip(chunks, chunks[1:], strict=False):
        assert prev["text"].split()[-2:] == nxt["text"].split()[:2]


def test_fixed_char_chunks_cover_full_text(ctx: dict[str, Any]) -> None:
    artifact = _load("artifact_parse.json")
    params = {"strategy": "fixed", "split_by": "char", "length": 10, "overlap": 0}
    chunks = _run(ctx, "fixed", params, artifact)["chunks"]
    assert chunks
    assert all(len(chunk["text"]) <= 10 for chunk in chunks)
    assert "".join(chunk["text"] for chunk in chunks) == artifact["full_text"]


def test_sentence_one_per_sentence_and_recursive_within_length(ctx: dict[str, Any]) -> None:
    artifact = _load("artifact_parse.json")
    result = _run(ctx, "sentence", PARAMS["sentence"], artifact)
    sentences = nltk.sent_tokenize(artifact["full_text"])
    chunks = result["chunks"]
    assert len(chunks) == len(sentences)
    for chunk, sentence in zip(chunks, sentences, strict=False):
        assert chunk["text"].strip() == sentence.strip()

    recursive = _run(ctx, "recursive", PARAMS["recursive"], artifact)
    assert recursive["chunks"]
    assert all(len(chunk["text"]) <= 80 for chunk in recursive["chunks"])


def test_semantic_reports_gaps_others_dont(ctx: dict[str, Any]) -> None:
    artifact = _load("artifact_parse.json")
    result = _run(ctx, "semantic", PARAMS["semantic"], artifact)
    semantic = result["semantic"]
    assert semantic is not None
    assert isinstance(semantic["gaps"], list)
    for gap in semantic["gaps"]:
        assert set(gap) == {"after_sentence", "distance", "is_break"}

    for strategy in ("fixed", "sentence", "recursive", "table"):
        assert _run(ctx, strategy, PARAMS[strategy], artifact)["semantic"] is None


def test_structure_without_docling_json_raises_unsupported(ctx: dict[str, Any]) -> None:
    artifact = _load("artifact_parse.json")
    with pytest.raises(WorkerError) as exc_info:
        _run(ctx, "structure", PARAMS["structure"], artifact)
    assert exc_info.value.code == "UNSUPPORTED_FOR_STRATEGY"
    assert exc_info.value.details == {"parse_strategy": "plain_text"}


def test_table_strategy_emits_table_chunk(ctx: dict[str, Any]) -> None:
    artifact = _load("artifacts__parse.json")
    chunks = _run(ctx, "table", PARAMS["table"], artifact)["chunks"]
    table_chunks = [chunk for chunk in chunks if chunk["element_type"] == "table"]
    assert len(table_chunks) == 1
    table = table_chunks[0]
    assert table["text"] == "| Q | Rev |\n|---|---|\n| Q3 | 12 |"
    assert table["element_ids"] == ["e-0001"]
    assert table["page_numbers"] == [1]


def test_pipeline_graph_names_splitter_and_annotator(ctx: dict[str, Any]) -> None:
    for strategy, params in PARAMS.items():
        pipeline = _build(ctx, strategy, params)
        assert set(pipeline.to_dict()["components"]) == {"splitter", "annotator"}
