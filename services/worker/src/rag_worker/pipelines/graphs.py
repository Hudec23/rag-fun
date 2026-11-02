from typing import Any

from haystack import Pipeline

from rag_worker.models.registry import ModelSet

# (stage, variant) pairs reported at startup (contracts/shared/pipeline-graph.schema.json)
VARIANTS: list[tuple[str, str]] = (
    [("parse", v) for v in ("docling_layout", "docling_ocr", "plain_text")]
    + [("chunk", v) for v in ("fixed", "sentence", "recursive", "semantic", "structure", "table")]
    + [("embed", "default"), ("store", "default")]
    + [("transform", v) for v in ("rewrite", "multi_query", "hyde")]
    + [("retrieve", v) for v in ("dense", "sparse", "hybrid")]
    + [("rerank", "default"), ("generate", "default")]
)


def graph_of(pipeline: Pipeline, stage: str, variant: str) -> dict[str, Any]:
    """pipeline.to_dict() -> {'stage', 'variant', 'nodes': [{'name', 'type', 'custom':
    type.startswith('rag_worker.components'), 'init_params': [{'name', 'value': json.dumps(value,
    default=str)[:2000]}] (keys containing 'key', 'token' or 'secret' -> value '"***"')}], 'edges':
    [{'sender', 'sender_socket', 'receiver', 'receiver_socket'}] from to_dict()['connections']
    ('a.out' -> sender a, socket out)}. Nodes sorted by name, edges in to_dict order."""
    raise NotImplementedError("not implemented")


def all_graphs(models: ModelSet, qdrant_url: str) -> list[dict[str, Any]]:
    """Build every VARIANTS pipeline (19 pairs) with default params (contracts defaults) and a placeholder
    collection (bge-m3, 1024 dims, Qdrant/bm25, qdrant name rf_000…0, Ollama chat qwen3:8b) and
    return graph_of for each, in VARIANTS order. Must not contact any server."""
    raise NotImplementedError("not implemented")
