---
id: T-api-012
kind: impl
feature: F-settings
title: app settings get/put/resolve
service: api
depends_on:
- T-api-012t
edit:
- services/api/src/rag_api/services/app_settings.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_app_settings.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/app_settings.py && uv run --frozen ruff check src/rag_api/services/app_settings.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_app_settings.py
max_attempts: 3
---

## Goal
Implement: app settings get/put/resolve. The tests written by T-api-012t define done.

## Context
Integration test: uses the `session`/`client` fixtures (postgres-test).

Stub in `services/api/src/rag_api/services/app_settings.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Settings row 'app' (R-020). Value shape: .autospec/plan/services/api.schema.sql (settings table comment)."""
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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or .autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
