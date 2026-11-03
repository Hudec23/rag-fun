---
id: T-api-012t
kind: test
feature: F-settings
title: 'Write tests: app settings get/put/resolve'
service: api
depends_on: []
edit:
- services/api/tests/integration/test_app_settings.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_app_settings.py && uv run --frozen ruff check tests/integration/test_app_settings.py && uv run --frozen pytest -q --collect-only tests/integration/test_app_settings.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_app_settings.py
max_attempts: 3
---

## Goal
Write unit tests for: app settings get/put/resolve. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-012 implements it.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test).

Stub in `services/api/src/rag_api/services/app_settings.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Settings row 'app' (R-020). Value shape: autospec/plan/services/api.schema.sql (settings table comment)."""
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from rag_api.schemas.settings import SettingsOut, SettingsUpdate


def mask_key(key: str | None) -> str | None:
    """None/'' -> None; len < 8 -> '…' + last 2 chars; else first 3 + '…' + last 4 ('sk-…abcd')."""
    raise NotImplementedError("not implemented")

async def load_value(session: AsyncSession) -> dict[str, Any]:
    """settings.value of key 'app'. Missing row -> AppError('INTERNAL_ERROR', 'settings not initialised')."""
    raise NotImplementedError("not implemented")

async def get_settings_out(session: AsyncSession) -> SettingsOut:
    raise NotImplementedError("not implemented")

async def put_settings(session: AsyncSession, body: SettingsUpdate) -> SettingsOut:
    """api_key None keeps the stored key, '' deletes it, other replaces it.
    chat_provider anthropic without resulting key -> VALIDATION_ERROR (details.field='anthropic.api_key');
    openai_compatible without base_url or model -> VALIDATION_ERROR (field 'openai_compatible.base_url'
    or 'openai_compatible.model'). updated_at = utcnow."""
    raise NotImplementedError("not implemented")

async def resolve_chat(session: AsyncSession) -> dict[str, Any]:
    """ChatModelConfig for job payloads: ollama -> {provider, model: ollama.chat_model,
    base_url: ollama.url, api_key: None}; anthropic -> {model, base_url: None, api_key};
    openai_compatible -> {model, base_url, api_key}."""
    raise NotImplementedError("not implemented")

async def ollama_url(session: AsyncSession) -> str:
    raise NotImplementedError("not implemented")

async def reranker_model(session: AsyncSession) -> str:
    raise NotImplementedError("not implemented")
```

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. mask_key(None) is None; mask_key('') is None; mask_key('abc') == '…bc'; mask_key('sk-ant-secret-abcd') == 'sk-…abcd'
2. get_settings_out with add_settings default → chat_provider 'ollama', anthropic.api_key_set False, api_key_masked None
3. put_settings anthropic with api_key 'sk-ant-secret-abcd' → api_key_set True, masked 'sk-…abcd'; stored value keeps the full key
4. put_settings with api_key None keeps the stored key; with '' removes it
5. chat_provider 'anthropic' and no key (none stored) → VALIDATION_ERROR details {'field': 'anthropic.api_key'}
6. chat_provider 'openai_compatible' without base_url → field 'openai_compatible.base_url'; with base_url but no model → 'openai_compatible.model'
7. resolve_chat: ollama → {'provider': 'ollama', 'model': 'qwen3:8b', 'base_url': ollama.url, 'api_key': None}; anthropic → base_url None + stored key; openai_compatible → base_url + key
8. load_value without a settings row → AppError INTERNAL_ERROR

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
