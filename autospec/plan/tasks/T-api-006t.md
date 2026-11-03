---
id: T-api-006t
kind: test
feature: F-qdrant-browser
title: 'Write tests: to_qdrant_filter'
service: api
depends_on: []
edit:
- services/api/tests/unit/test_qdrant_filter.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_qdrant_filter.py && uv run --frozen ruff check tests/unit/test_qdrant_filter.py && uv run --frozen pytest -q --collect-only tests/unit/test_qdrant_filter.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/unit/test_qdrant_filter.py
max_attempts: 3
---

## Goal
Write unit tests for: to_qdrant_filter. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-006 implements it.

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

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. PayloadFilter() (empty) → None; PayloadFilter(must=[]) → None
2. must [{key: tags, match: {any: ['hr']}}] → models.Filter(must=[FieldCondition(key='meta.tags', match=MatchAny(any=['hr']))])
3. must [{key: file_id, match: {value: 'abc'}}] → FieldCondition(key='meta.file_id', match=MatchValue(value='abc'))
4. must [{key: page, range: {gte: 1, lte: 3}}] → FieldCondition(key='meta.page', range=Range(gte=1, lte=3)); only gte given → lte None
5. should and must_not lists map to Filter.should / Filter.must_not with the same conversion

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
