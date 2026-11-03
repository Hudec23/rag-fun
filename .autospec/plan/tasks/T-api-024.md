---
id: T-api-024
kind: impl
feature: F-status
title: model catalog
service: api
depends_on:
- T-api-024t
- T-api-012
edit:
- services/api/src/rag_api/services/models_catalog.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/integration/test_models_catalog.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/models_catalog.py && uv run --frozen ruff check src/rag_api/services/models_catalog.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/integration/test_models_catalog.py
max_attempts: 3
---

## Goal
Implement: model catalog. The tests written by T-api-024t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or .autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
