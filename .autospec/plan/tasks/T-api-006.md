---
id: T-api-006
kind: impl
feature: F-qdrant-browser
title: to_qdrant_filter
service: api
depends_on:
- T-api-006t
edit:
- services/api/src/rag_api/qdrant_read.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/unit/test_qdrant_filter.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/qdrant_read.py && uv run --frozen ruff check src/rag_api/qdrant_read.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/unit/test_qdrant_filter.py
max_attempts: 3
---

## Goal
Implement: to_qdrant_filter. The tests written by T-api-006t define done.

## Context
Build inputs with `PayloadFilter.model_validate({...})` (from rag_api.contracts_gen.shared.common_schema import PayloadFilter). Compare with `qdrant_client.models` objects using ==.

Stub in `services/api/src/rag_api/qdrant_read.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Read-only Qdrant access for the browser (R-011). Never upserts or deletes."""
from typing import Any
from rag_api.contracts_gen.shared.common_schema import PayloadFilter
from rag_api.schemas.qdrant import FacetResponse, QdrantInfo, QdrantPoint, ScrollResponse


def to_qdrant_filter(f: PayloadFilter) -> Any:
    """PayloadFilter -> qdrant_client.models.Filter (None when the filter is empty).
    key 'tags' -> 'meta.tags'; match.value -> MatchValue; match.any -> MatchAny; range -> Range."""
    raise NotImplementedError("not implemented")
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
