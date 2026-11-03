---
id: T-worker-030
kind: impl
feature: F-retrieve
title: Hit conversions
service: worker
depends_on:
- T-worker-030t
edit:
- services/worker/src/rag_worker/components/hits.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_hits.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/components/hits.py && uv run --frozen ruff check src/rag_worker/components/hits.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_hits.py
max_attempts: 3
---

## Goal
Implement: Hit conversions. The tests written by T-worker-030t define done.

## Context
Stub in `services/worker/src/rag_worker/components/hits.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from haystack import Document
from rag_worker.contracts_gen.qdrant.payload_schema import Meta


def to_hit(doc: Document, rank: int, score: float | None = None) -> dict[str, Any]:
    """Retrieved Haystack Document -> Hit (contracts/shared/common.schema.json#/$defs/Hit):
    point_id = qdrant convert_id(doc.id), doc_id = doc.id, rank, score = score or doc.score or 0.0
    (round 6), content, meta = doc.meta (validated with Meta)."""
    _ = Meta
    raise NotImplementedError("not implemented")

def hit_to_document(hit: dict[str, Any]) -> Document:
    """Inverse for reranking: Document(id=doc_id, content, meta, score)."""
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
