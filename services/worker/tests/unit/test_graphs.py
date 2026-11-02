"""Unit tests for pipeline graph export (rag_worker.pipelines.graphs): graph_of / all_graphs
must emit pipeline-graph.schema.json-valid graphs for every VARIANTS pair without touching
the network."""

import socket
from typing import Any

import pytest
from haystack import Pipeline
from haystack.utils import Secret
from haystack_integrations.components.generators.anthropic import AnthropicChatGenerator

from rag_worker.models.registry import FakeModelSet
from rag_worker.pipelines.graphs import VARIANTS, all_graphs, graph_of
from tests.contract import errors

QDRANT_URL = "http://127.0.0.1:1"


def _graph(graphs: list[dict[str, Any]], stage: str, variant: str) -> dict[str, Any]:
    for g in graphs:
        if g["stage"] == stage and g["variant"] == variant:
            return g
    raise AssertionError(f"no graph for {stage}/{variant}")


def test_all_graphs_returns_every_variant_and_validates_against_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def no_socket(*args: Any, **kwargs: Any) -> socket.socket:
        raise AssertionError("socket.create_connection was called during all_graphs")

    monkeypatch.setattr(socket, "create_connection", no_socket)
    graphs = all_graphs(FakeModelSet(), QDRANT_URL)
    assert len(graphs) == 19
    assert [(g["stage"], g["variant"]) for g in graphs] == VARIANTS
    for g in graphs:
        assert errors(g, "shared/pipeline-graph.schema.json") == []


def test_chunk_semantic_graph_has_custom_splitter_and_edge() -> None:
    graph = _graph(all_graphs(FakeModelSet(), QDRANT_URL), "chunk", "semantic")
    splitter = next(n for n in graph["nodes"] if n["name"] == "splitter")
    assert splitter["custom"] is True
    assert splitter["type"].endswith("SemanticSplitter")
    assert {
        "sender": "splitter",
        "sender_socket": "documents",
        "receiver": "annotator",
        "receiver_socket": "documents",
    } in graph["edges"]


def test_retrieve_hybrid_graph_has_both_embedder_and_retriever_nodes() -> None:
    graph = _graph(all_graphs(FakeModelSet(), QDRANT_URL), "retrieve", "hybrid")
    names = [n["name"] for n in graph["nodes"]]
    for name in ("dense_embedder", "dense_retriever", "sparse_embedder", "sparse_retriever"):
        assert name in names


def test_graph_of_masks_secret_init_params() -> None:
    pipeline = Pipeline()
    pipeline.add_component(
        "generator",
        AnthropicChatGenerator(
            api_key=Secret.from_env_var("ANTHROPIC_API_KEY"),
            model="claude-sonnet-5-5",
        ),
    )
    graph = graph_of(pipeline, "generate", "default")
    node = next(n for n in graph["nodes"] if n["name"] == "generator")
    params = {p["name"]: p["value"] for p in node["init_params"]}
    assert params["api_key"] == '"***"'
    assert params["model"] == '"claude-sonnet-5-5"'


def test_all_graphs_nodes_sorted_by_name() -> None:
    graphs = all_graphs(FakeModelSet(), QDRANT_URL)
    for g in graphs:
        names = [n["name"] for n in g["nodes"]]
        assert names == sorted(names)
