---
id: T-api-020
kind: impl
feature: F-live-progress
title: SSE message mapping
service: api
depends_on:
- T-api-020t
- T-api-005
edit:
- services/api/src/rag_api/services/sse.py
read:
- services/api/src/rag_api/services/collections.py
locked:
- services/api/tests/unit/test_sse.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check src/rag_api/services/sse.py && uv run --frozen ruff check src/rag_api/services/sse.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/unit/test_sse.py
max_attempts: 3
---

## Goal
Implement: SSE message mapping. The tests written by T-api-020t define done.

## Context
Unit test with tests.fakes.FakeEventBus; consume with `agen = sse_messages(bus, 'r')`; `await asyncio.wait_for(agen.__anext__(), 2)` after publishing from another task (publish after a `await asyncio.sleep(0)` so the subscription exists).

Stub in `services/api/src/rag_api/services/sse.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
import json
from collections.abc import AsyncIterator
from typing import Any
from rag_api.events import EventBus


async def sse_messages(events: EventBus, run_id: str) -> AsyncIterator[dict[str, Any]]:
    """For every event from events.subscribe(run_id) yield {'event': event['type'],
    'data': json.dumps(event, separators=(',', ':'))} unchanged otherwise. Events without a str
    'type' are skipped."""
    _ = json
    raise NotImplementedError("not implemented")
    yield {}  # pragma: no cover
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
