---
id: T-worker-006
kind: impl
feature: F-stage-flow
title: ApiClient callbacks with retries
service: worker
depends_on:
- T-worker-006t
edit:
- services/worker/src/rag_worker/callbacks.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_callbacks.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/callbacks.py && uv run --frozen ruff check src/rag_worker/callbacks.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_callbacks.py
max_attempts: 3
---

## Goal
Implement: ApiClient callbacks with retries. The tests written by T-worker-006t define done.

## Context
Use respx to mock http://api:8000; pass `sleep=recorder` where `async def recorder(s): sleeps.append(s)`.

Stub in `services/worker/src/rag_worker/callbacks.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""REST callbacks to the api (contracts/openapi/internal.yaml)."""
from collections.abc import Awaitable, Callable
from typing import Any
import httpx
RETRY_DELAYS = [1, 2, 4, 8, 16]  # seconds between the 5 attempts' failures


class ApiClient:
    """POST/PUT with header X-Internal-Token. Retry on httpx.TransportError or 5xx: up to 5 attempts
    total, sleeping RETRY_DELAYS[i] after failed attempt i (no sleep after the last). 4xx: no retry,
    raise httpx.HTTPStatusError. After the last failed attempt re-raise the last error."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        token: str,
        sleep: Callable[[float], Awaitable[None]] | None = None,
    ) -> None:
        self.http = http
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.sleep = sleep  # None -> asyncio.sleep; tests pass a recorder

    async def stage_started(self, stage_run_id: str, started_at: str) -> None:
        """POST /internal/v1/stage-started {stage_run_id, started_at}."""
        raise NotImplementedError("not implemented")

    async def stage_result(self, result: dict[str, Any]) -> None:
        """POST /internal/v1/stage-results with the StageResult body."""
        raise NotImplementedError("not implemented")

    async def put_graph(self, graph: dict[str, Any]) -> None:
        """PUT /internal/v1/pipeline-graphs/{graph['stage']}/{graph['variant']}."""
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
