---
id: T-api-022
kind: impl
feature: F-settings
title: test_connection probes
service: api
depends_on:
- T-api-022t
- T-api-012
edit:
- services/api/src/rag_api/services/connection_test.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_connection_probe.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/connection_test.py && uv run --frozen ruff check src/rag_api/services/connection_test.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_connection_probe.py
max_attempts: 3
---

## Goal
Implement: test_connection probes. The tests written by T-api-022t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
