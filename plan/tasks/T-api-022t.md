---
id: T-api-022t
kind: test
feature: F-settings
title: 'Write tests: test_connection probes'
service: api
depends_on: []
edit:
- services/api/tests/integration/test_connection_probe.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_connection_probe.py && uv run --frozen ruff check tests/integration/test_connection_probe.py && uv run --frozen pytest -q --collect-only tests/integration/test_connection_probe.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_connection_probe.py
max_attempts: 3
---

## Goal
Write unit tests for: test_connection probes. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-022 implements it.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test). Mock HTTP with respx (`respx.mock` decorator/context). Pass `httpx.AsyncClient()` as http.

Stub in `services/api/src/rag_api/services/connection_test.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.schemas.settings import TestConnectionRequest, TestConnectionResult


async def test_connection(
    session: AsyncSession, http: httpx.AsyncClient, body: TestConnectionRequest
) -> TestConnectionResult:
    """Never raises for provider problems; timeout 10 s. Values: override fields when given
    (api_key None -> stored key), else stored settings.
    ollama: GET {url}/api/tags -> models = [m['name'] for m in models].
    anthropic: GET https://api.anthropic.com/v1/models, headers x-api-key + anthropic-version
    '2023-06-01' -> models = [d['id'] for d in data].
    openai_compatible: GET {base_url}/models, Authorization 'Bearer <key>' if key -> data[].id.
    Non-2xx -> ok False, detail 'HTTP <status>'; network error -> ok False, detail = str(exc)[:500];
    missing key/base_url -> ok False, detail 'not configured', latency 0."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. ollama: respx GET http://ollama-fake:11434/api/tags → {'models': [{'name': 'qwen3:8b'}]} → ok True, models ['qwen3:8b'], latency_ms ≥ 0
2. ollama connect error (respx side_effect httpx.ConnectError('x')) → ok False, detail contains 'x', models []
3. anthropic with stored key: GET https://api.anthropic.com/v1/models has headers x-api-key and anthropic-version '2023-06-01', response {'data': [{'id': 'claude-sonnet-5-5'}]} → models ['claude-sonnet-5-5']
4. anthropic without key → ok False, detail 'not configured', latency_ms 0, no HTTP call
5. openai_compatible override base_url 'http://lm:1234/v1' + key 'k' → GET http://lm:1234/v1/models with Authorization 'Bearer k'
6. HTTP 401 → ok False, detail 'HTTP 401'

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
