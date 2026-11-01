---
id: T-api-007t
kind: test
feature: F-qdrant-browser
title: 'Write tests: QdrantReader info/scroll/count/facet/get_point'
service: api
depends_on:
- T-api-006
edit:
- services/api/tests/integration/test_qdrant_reader.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_qdrant_reader.py && uv run --frozen ruff check tests/integration/test_qdrant_reader.py && uv run --frozen pytest -q --collect-only tests/integration/test_qdrant_reader.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_qdrant_reader.py
max_attempts: 3
---

## Goal
Write unit tests for: QdrantReader info/scroll/count/facet/get_point. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-007 implements it.

## Context
Integration test against qdrant-test (QDRANT_URL) with qdrant_client.AsyncQdrantClient; collection name 'rf_' + uuid4().hex, delete it after the test. Point ids are 32-hex strings; payload from tests.conftest.FIXTURES / 'qdrant__payload.json'.

Stub in `services/api/src/rag_api/qdrant_read.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Read-only Qdrant access for the browser (R-011). Never upserts or deletes."""
from typing import Any
from rag_api.contracts_gen.shared.common_schema import PayloadFilter
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

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. info on a missing collection → QdrantInfo(qdrant_name, exists=False, status=None, points_count=None, dense=None, sparse=None, payload_indexes=[])
2. seed: create collection 'rf_<32 hex>' with vectors {'text-dense': VectorParams(size=4, distance=COSINE)}, sparse {'text-sparse': SparseVectorParams(modifier=IDF)}, keyword index meta.tags, 3 points (payload = contract payload fixture with meta.tags ['hr'], ['hr'], ['tax']); info → exists True, points_count 3, dense == DenseInfo(name='text-dense', size=4, distance='Cosine'), sparse.modifier 'idf', payload_indexes contains key 'meta.tags' type 'keyword'
3. scroll(filter tags any ['hr'], limit 1, offset None, with_vectors False) → 1 point, vectors None, next_offset not None; second page with that offset → 1 point, next_offset None
4. scroll with_vectors True → vectors.dense has 4 floats, vectors.sparse.indices non-empty
5. count(empty filter) == 3; count(tags ['tax']) == 1; count on missing collection == 0
6. facet('tags') → values [{'value': 'hr', 'count': 2}, {'value': 'tax', 'count': 1}] (count desc)
7. get_point(existing id) → payload equals seeded payload; get_point(unknown 32-hex id) raises AppError POINT_NOT_FOUND

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
