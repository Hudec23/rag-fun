---
id: T-api-024t
kind: test
feature: F-status
title: 'Write tests: model catalog'
service: api
depends_on: []
edit:
- services/api/tests/integration/test_models_catalog.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_models_catalog.py && uv run --frozen ruff check tests/integration/test_models_catalog.py && uv run --frozen pytest -q --collect-only tests/integration/test_models_catalog.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_models_catalog.py
max_attempts: 3
---

## Goal
Write unit tests for: model catalog. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-024 implements it.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test). respx for ollama.

Stub in `services/api/src/rag_api/services/models_catalog.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.schemas.settings import ModelCatalog


async def get_catalog(session: AsyncSession, http: httpx.AsyncClient) -> ModelCatalog:
    """GET {ollama_url}/api/tags (timeout 3 s). dense = catalog.DENSE_MODELS in catalog order;
    installed = some installed name == model or startswith(model + ':'). Ollama error ->
    ollama_reachable False, ollama_installed [], installed False everywhere."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. ollama tags ['bge-m3:latest', 'qwen3:8b'] → ollama_reachable True, dense installed: bge-m3 True, others False; order bge-m3, nomic-embed-text, mxbai-embed-large, all-minilm with dims 1024, 768, 1024, 384 and max_tokens 8192, 8192, 512, 256
2. tag 'all-minilm' (no suffix) counts as installed
3. 'bge-m3x:latest' does not count as bge-m3
4. ollama down → reachable False, installed [] and every installed False
5. sparse == ['Qdrant/bm25', 'prithivida/Splade_PP_en_v1'] and rerank == catalog.RERANK_MODELS

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
