---
id: T-worker-031
kind: impl
feature: F-retrieve
title: RRF fusion
service: worker
depends_on:
- T-worker-031t
edit:
- services/worker/src/rag_worker/components/rrf.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_rrf.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/components/rrf.py && uv run --frozen ruff check src/rag_worker/components/rrf.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_rrf.py
max_attempts: 3
---

## Goal
Implement: RRF fusion. The tests written by T-worker-031t define done.

## Context
Stub in `services/worker/src/rag_worker/components/rrf.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from haystack import Document, component


def rrf_fuse(
    lists: list[tuple[int, str, list[Document]]], rrf_k: int, top_k: int
) -> list[dict[str, Any]]:
    """lists = [(query_index, 'dense'|'sparse', ranked docs)]. score(d) = Σ 1/(rrf_k + rank) over
    every list containing d (rank 1-based; identity = doc.id). Sort score desc, then doc.id asc;
    keep top_k. Returns [{'doc': Document, 'score': float(round 6), 'source_ranks':
    [{'query_index', 'list', 'rank'}]}] with source_ranks in input-list order."""
    raise NotImplementedError("not implemented")

@component
class RRFJoiner:
    def __init__(self, rrf_k: int, top_k: int) -> None:
        self.rrf_k = rrf_k
        self.top_k = top_k

    @component.output_types(fused=list[dict[str, Any]])
    def run(self, lists: list[tuple[int, str, list[Document]]]) -> dict[str, Any]:
        return {"fused": rrf_fuse(lists, self.rrf_k, self.top_k)}
```

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or .autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
