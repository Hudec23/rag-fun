---
id: T-worker-039
kind: impl
feature: F-pipeline-graph
title: pipeline graph export
service: worker
depends_on:
- T-worker-039t
- T-worker-016
- T-worker-021
- T-worker-024
- T-worker-026
- T-worker-028
- T-worker-032
- T-worker-034
- T-worker-037
edit:
- services/worker/src/rag_worker/pipelines/graphs.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_graphs.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/pipelines/graphs.py && uv run --frozen ruff check src/rag_worker/pipelines/graphs.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_graphs.py
max_attempts: 3
---

## Goal
Implement: pipeline graph export. The tests written by T-worker-039t define done.

## Context
Stub in `services/worker/src/rag_worker/pipelines/graphs.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from haystack import Pipeline
from rag_worker.models.registry import ModelSet
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
```

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
