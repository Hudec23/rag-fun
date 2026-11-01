---
id: T-api-025t
kind: test
feature: F-pipeline-graph
title: 'Write tests: pipeline graph store'
service: api
depends_on: []
edit:
- services/api/tests/integration/test_pipeline_graphs_service.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_pipeline_graphs_service.py && uv run --frozen ruff check tests/integration/test_pipeline_graphs_service.py && uv run --frozen pytest -q --collect-only tests/integration/test_pipeline_graphs_service.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_pipeline_graphs_service.py
max_attempts: 3
---

## Goal
Write unit tests for: pipeline graph store. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-025 implements it.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test). Graph fixture: tests.conftest.FIXTURES / 'shared__pipeline-graph.json' (stage chunk, variant fixed); copy and change stage/variant for others.

Stub in `services/api/src/rag_api/services/pipeline_graphs.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.schemas.system import PipelineGraphList


async def put_graph(session: AsyncSession, stage: str, variant: str, graph: dict[str, Any]) -> None:
    """graph['stage'] != stage or graph['variant'] != variant -> VALIDATION_ERROR
    (details.field='stage' or 'variant'). Upsert row, updated_at utcnow."""
    raise NotImplementedError("not implemented")

async def list_graphs(session: AsyncSession) -> PipelineGraphList:
    """Order: stage pipeline order (parse, chunk, embed, store, transform, retrieve, rerank,
    generate), then variant ascending."""
    raise NotImplementedError("not implemented")

async def get_graph(session: AsyncSession, stage: str, variant: str) -> dict[str, Any]:
    """404 PIPELINE_GRAPH_NOT_FOUND (details.stage, details.variant)."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. put_graph('chunk', 'fixed', fixture graph) then get_graph → same dict
2. put twice → second replaces the first (one row)
3. body stage mismatch → VALIDATION_ERROR details {'field': 'stage'}; variant mismatch → field 'variant'
4. list_graphs order: put generate/default, chunk/semantic, chunk/fixed, parse/plain_text → parse/plain_text, chunk/fixed, chunk/semantic, generate/default
5. get_graph unknown → PIPELINE_GRAPH_NOT_FOUND details {'stage', 'variant'}

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
