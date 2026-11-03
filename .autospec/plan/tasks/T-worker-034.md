---
id: T-worker-034
kind: impl
feature: F-rerank
title: rerank pipeline + artifact
service: worker
depends_on:
- T-worker-034t
- T-worker-030
edit:
- services/worker/src/rag_worker/pipelines/rerank.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_rerank_pipeline.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/pipelines/rerank.py && uv run --frozen ruff check src/rag_worker/pipelines/rerank.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_rerank_pipeline.py
max_attempts: 3
---

## Goal
Implement: rerank pipeline + artifact. The tests written by T-worker-034t define done.

## Context
Stub in `services/worker/src/rag_worker/pipelines/rerank.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from haystack import Pipeline
from rag_worker.models.registry import ModelSet


def build_rerank_pipeline(model: str, top_n: int, models: ModelSet) -> Pipeline:
    """'ranker' = models.ranker(model, top_n)."""
    raise NotImplementedError("not implemented")

def rerank_artifact(
    enabled: bool,
    model: str | None,
    top_n: int,
    query: str,
    before: list[dict[str, Any]],
    reranked: list[Any] | None,
) -> dict[str, Any]:
    """contracts/artifacts/rerank.schema.json. enabled: after[i] = {'hit': to_hit(doc, rank i+1,
    score), 'previous_rank': rank of doc_id in before, 'rerank_score': score}; ties already ordered by
    the ranker, re-sort score desc then doc_id asc. disabled: after = before[:top_n] with
    previous_rank = rank, rerank_score None, model None."""
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
