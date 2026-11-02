"""Pipeline graph export: graph_of turns a built Haystack Pipeline into the
contracts/shared/pipeline-graph.schema.json shape; all_graphs builds every VARIANTS pipeline
with contract defaults and reports all of them (PUT /internal/v1/pipeline-graphs, see main)."""

import json
from typing import Any

from haystack import Pipeline

from rag_worker.contracts_gen.shared.common_schema import (
    ChatModelConfig,
    CollectionRef,
    DenseModelConfig,
)
from rag_worker.models.registry import ModelSet
from rag_worker.pipelines.chunk import build_chunk_pipeline
from rag_worker.pipelines.embed import build_embed_pipeline
from rag_worker.pipelines.generate import build_generate_pipeline
from rag_worker.pipelines.parse import build_parse_pipeline
from rag_worker.pipelines.rerank import build_rerank_pipeline
from rag_worker.pipelines.retrieve import build_retrieve_pipeline
from rag_worker.pipelines.store import build_store_pipeline
from rag_worker.pipelines.transform import build_transform_pipeline
from rag_worker.qdrant_admin import document_store

# (stage, variant) pairs reported at startup (contracts/shared/pipeline-graph.schema.json)
VARIANTS: list[tuple[str, str]] = (
    [("parse", v) for v in ("docling_layout", "docling_ocr", "plain_text")]
    + [("chunk", v) for v in ("fixed", "sentence", "recursive", "semantic", "structure", "table")]
    + [("embed", "default"), ("store", "default")]
    + [("transform", v) for v in ("rewrite", "multi_query", "hyde")]
    + [("retrieve", v) for v in ("dense", "sparse", "hybrid")]
    + [("rerank", "default"), ("generate", "default")]
)

# placeholder for all_graphs: contract defaults of a fresh bge-m3 / Qdrant-bm25 collection on
# Ollama chat (contracts/shared/common.schema.json), never a real deployment target
_OLLAMA_URL = "http://ollama:11434"
_PLACEHOLDER_ID = "00000000-0000-7000-8000-000000000000"
_PLACEHOLDER_QDRANT_NAME = "rf_" + "0" * 32
_RERANK_MODEL = "Xenova/ms-marco-MiniLM-L-6-v2"
_PARSE_PARAMS: dict[str, dict[str, Any]] = {
    "docling_layout": {"strategy": "docling_layout", "extract_tables": True, "page_images": True},
    "docling_ocr": {"strategy": "docling_ocr", "extract_tables": True, "page_images": True},
    "plain_text": {"strategy": "plain_text"},
}
_CHUNK_PARAMS: dict[str, dict[str, Any]] = {
    "fixed": {"strategy": "fixed", "split_by": "word", "length": 200, "overlap": 20},
    "sentence": {"strategy": "sentence", "length": 5, "overlap": 1},
    "recursive": {
        "strategy": "recursive",
        "length": 1000,
        "overlap": 100,
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


def _param_value(name: str, value: Any) -> str:
    """init_params value as a JSON string (schema maxLength 2000); param names that hold
    credentials ('key', 'token' or 'secret' in the name) are masked."""
    if any(marker in name for marker in ("key", "token", "secret")):
        return '"***"'
    return json.dumps(value, default=str)[:2000]


def _edge(sender: str, receiver: str) -> dict[str, str]:
    """'a.out' / 'b.in' -> {'sender': 'a', 'sender_socket': 'out', 'receiver': 'b',
    'receiver_socket': 'in'} (socket = everything after the last dot)."""
    src, _, src_socket = sender.rpartition(".")
    dst, _, dst_socket = receiver.rpartition(".")
    return {
        "sender": src,
        "sender_socket": src_socket,
        "receiver": dst,
        "receiver_socket": dst_socket,
    }


def graph_of(pipeline: Pipeline, stage: str, variant: str) -> dict[str, Any]:
    """pipeline.to_dict() -> {'stage', 'variant', 'nodes': [{'name', 'type', 'custom':
    type.startswith('rag_worker.components'), 'init_params': [{'name', 'value': json.dumps(value,
    default=str)[:2000]}] (keys containing 'key', 'token' or 'secret' -> value '"***"')}], 'edges':
    [{'sender', 'sender_socket', 'receiver', 'receiver_socket'}] from to_dict()['connections']
    ('a.out' -> sender a, socket out)}. Nodes sorted by name, edges in to_dict order."""
    data = pipeline.to_dict()
    nodes: list[dict[str, Any]] = [
        {
            "name": name,
            "type": spec["type"],
            "custom": spec["type"].startswith("rag_worker.components"),
            "init_params": [
                {"name": param, "value": _param_value(param, value)}
                for param, value in spec["init_parameters"].items()
            ],
        }
        for name, spec in data["components"].items()
    ]
    nodes.sort(key=lambda node: node["name"])
    edges = [_edge(conn["sender"], conn["receiver"]) for conn in data["connections"]]
    return {"stage": stage, "variant": variant, "nodes": nodes, "edges": edges}


def all_graphs(models: ModelSet, qdrant_url: str) -> list[dict[str, Any]]:
    """Build every VARIANTS pipeline (19 pairs) with default params (contracts defaults) and a placeholder
    collection (bge-m3, 1024 dims, Qdrant/bm25, qdrant name rf_000…0, Ollama chat qwen3:8b) and
    return graph_of for each, in VARIANTS order. Must not contact any server."""
    dense = DenseModelConfig(model="bge-m3", dims=1024, ollama_url=_OLLAMA_URL)
    chat = ChatModelConfig(provider="ollama", model="qwen3:8b", base_url=_OLLAMA_URL, api_key=None)
    collection = CollectionRef(
        id=_PLACEHOLDER_ID,
        qdrant_name=_PLACEHOLDER_QDRANT_NAME,
        dense=dense,
        sparse_model="Qdrant/bm25",
    )
    # store and retrieve share one document store (lazy client: no network at construction)
    store = document_store(qdrant_url, collection.qdrant_name, dense.dims)

    def build(stage: str, variant: str) -> Pipeline:
        if stage == "parse":
            return build_parse_pipeline(variant, _PARSE_PARAMS[variant])
        if stage == "chunk":
            return build_chunk_pipeline(variant, _CHUNK_PARAMS[variant], models, dense)
        if stage == "embed":
            return build_embed_pipeline(collection, 16, models)
        if stage == "store":
            return build_store_pipeline(store)
        if stage == "transform":
            return build_transform_pipeline(variant, chat, models)
        if stage == "retrieve":
            return build_retrieve_pipeline(variant, collection, store, 10, models)
        if stage == "rerank":
            return build_rerank_pipeline(_RERANK_MODEL, 5, models)
        return build_generate_pipeline(chat, 0.2, 800, models, None)

    return [graph_of(build(stage, variant), stage, variant) for stage, variant in VARIANTS]
