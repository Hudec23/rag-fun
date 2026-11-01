---
id: T-worker-024
kind: impl
feature: F-embed
title: embed pipeline + embed artifact
service: worker
depends_on:
- T-worker-024t
- T-worker-002
- T-worker-003
- T-worker-004
- T-worker-023
edit:
- services/worker/src/rag_worker/pipelines/embed.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_embed_pipeline.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/pipelines/embed.py && uv run --frozen ruff check src/rag_worker/pipelines/embed.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_embed_pipeline.py
max_attempts: 3
---

## Goal
Implement: embed pipeline + embed artifact. The tests written by T-worker-024t define done.

## Context
Stub in `services/worker/src/rag_worker/pipelines/embed.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from haystack import Pipeline
from rag_worker.contracts_gen.shared.common_schema import CollectionRef
from rag_worker.models.registry import ModelSet


def build_embed_pipeline(collection: CollectionRef, batch_size: int, models: ModelSet) -> Pipeline:
    """'dense' (models.dense_document_embedder(collection.dense, batch_size)) -> 'sparse'
    (models.sparse_document_embedder(collection.sparse_model)) -> 'tokens' (TokenView(models.tokenizer
    (collection.dense.model), max_tokens from registry.TOKENIZERS))."""
    raise NotImplementedError("not implemented")

def embed_artifact(
    documents: list[Any], collection: CollectionRef, tokenizer_repo: str, max_tokens: int
) -> dict[str, Any]:
    """Embedded Documents (chunk order) -> embed artifact (contracts/artifacts/embed.schema.json):
    chunks [{index, doc_id, dense (round 6), sparse {indices, values (round 6)}, tokens, token_count,
    over_limit}], sample_indices (viz.sampling), projections (viz.projection pca 2/3 + umap 2/3 over the
    sample), similarity (viz.similarity over the sample)."""
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
