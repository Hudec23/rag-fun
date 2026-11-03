---
id: T-worker-004
kind: impl
feature: F-embed
title: cosine similarity matrix
service: worker
depends_on:
- T-worker-004t
edit:
- services/worker/src/rag_worker/viz/similarity.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_viz_similarity.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/viz/similarity.py && uv run --frozen ruff check src/rag_worker/viz/similarity.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_viz_similarity.py
max_attempts: 3
---

## Goal
Implement: cosine similarity matrix. The tests written by T-worker-004t define done.

## Context
Stub in `services/worker/src/rag_worker/viz/similarity.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
def cosine_matrix(vectors: list[list[float]]) -> list[list[float]]:
    """Square cosine similarity matrix, values clipped to [-1, 1], rounded 6, diagonal exactly 1.0
    (also for zero vectors). [] -> []."""
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
