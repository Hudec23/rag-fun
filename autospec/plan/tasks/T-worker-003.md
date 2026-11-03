---
id: T-worker-003
kind: impl
feature: F-embed
title: PCA + UMAP projections
service: worker
depends_on:
- T-worker-003t
edit:
- services/worker/src/rag_worker/viz/projection.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_viz_projection.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/viz/projection.py && uv run --frozen ruff check src/rag_worker/viz/projection.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_viz_projection.py
max_attempts: 3
---

## Goal
Implement: PCA + UMAP projections. The tests written by T-worker-003t define done.

## Context
Generate inputs with numpy.random.default_rng(0).normal(size=(n, d)).tolist().

Stub in `services/worker/src/rag_worker/viz/projection.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
def pca(vectors: list[list[float]], k: int) -> tuple[list[list[float]] | None, list[float]]:
    """sklearn PCA(n_components=k, random_state=42) -> (coords rounded 6, explained_variance_ratio_
    rounded 6). len(vectors) < k -> (None, []). All-identical vectors -> coords all 0.0 and
    explained variance [] (no exception)."""
    raise NotImplementedError("not implemented")

def umap_project(vectors: list[list[float]], k: int) -> list[list[float]] | None:
    """umap.UMAP(n_components=k, n_neighbors=min(15, n-1), random_state=42, metric='cosine')
    .fit_transform -> rounded 6. n < 5 -> None."""
    raise NotImplementedError("not implemented")
```

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
