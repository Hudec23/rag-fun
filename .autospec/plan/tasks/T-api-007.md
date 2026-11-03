---
id: T-api-007
kind: impl
feature: F-qdrant-browser
title: QdrantReader info/scroll/count/facet/get_point
service: api
depends_on:
- T-api-007t
- T-api-006
edit:
- services/api/src/rag_api/qdrant_read.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_qdrant_reader.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/qdrant_read.py && uv run --frozen ruff check src/rag_api/qdrant_read.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_qdrant_reader.py
max_attempts: 3
---

## Goal
Implement: QdrantReader info/scroll/count/facet/get_point. The tests written by T-api-007t define done.

## Context
Integration test against qdrant-test (QDRANT_URL) with qdrant_client.AsyncQdrantClient; collection name 'rf_' + uuid4().hex, delete it after the test. Point ids are 32-hex strings; payload from tests.conftest.FIXTURES / 'qdrant__payload.json'.

Stub in `services/api/src/rag_api/qdrant_read.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Read-only Qdrant access for the browser (R-011). Never upserts or deletes."""
from typing import Any
from qdrant_client import models
from rag_api.contracts_gen.shared.common_schema import (
    FilterCondition,
    MatchAnyCondition,
    PayloadFilter,
    RangeCondition,
)
from rag_api.schemas.qdrant import FacetResponse, QdrantInfo, QdrantPoint, ScrollResponse


class QdrantReader:
    def __init__(self, client: Any) -> None:
        self.client = client  # qdrant_client.AsyncQdrantClient

    async def info(self, qdrant_name: str) -> QdrantInfo:
        raise NotImplementedError("not implemented")

    async def scroll(
        self,
        qdrant_name: str,
        flt: PayloadFilter,
        limit: int,
        offset: str | None,
        with_vectors: bool,
    ) -> ScrollResponse:
        raise NotImplementedError("not implemented")

    async def count(self, qdrant_name: str, flt: PayloadFilter) -> int:
        raise NotImplementedError("not implemented")

    async def facet(self, qdrant_name: str, key: str) -> FacetResponse:
        raise NotImplementedError("not implemented")

    async def get_point(self, qdrant_name: str, point_id: str) -> QdrantPoint:
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
