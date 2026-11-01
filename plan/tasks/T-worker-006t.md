---
id: T-worker-006t
kind: test
feature: F-stage-flow
title: 'Write tests: ApiClient callbacks with retries'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_callbacks.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_callbacks.py && uv run --frozen ruff check tests/unit/test_callbacks.py && uv run --frozen pytest -q --collect-only tests/unit/test_callbacks.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_callbacks.py
max_attempts: 3
---

## Goal
Write unit tests for: ApiClient callbacks with retries. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-006 implements it.

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

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. stage_started('id1', ts) → POST {base}/internal/v1/stage-started with JSON {'stage_run_id': 'id1', 'started_at': ts} and header X-Internal-Token
2. stage_result(body) → POST /internal/v1/stage-results with the body unchanged
3. put_graph({'stage': 'chunk', 'variant': 'fixed', ...}) → PUT /internal/v1/pipeline-graphs/chunk/fixed
4. 503, 503, 204 → succeeds after 3 calls; recorded sleeps == [1, 2]
5. five ConnectErrors → raises httpx.ConnectError after 5 attempts; sleeps == [1, 2, 4, 8]
6. 404 → raises httpx.HTTPStatusError after 1 call, no sleep
7. base_url with trailing slash 'http://api:8000/' builds 'http://api:8000/internal/v1/…'

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
