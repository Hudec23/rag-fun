---
id: T-api-020t
kind: test
feature: F-live-progress
title: 'Write tests: SSE message mapping'
service: api
depends_on: []
edit:
- services/api/tests/unit/test_sse.py
read:
- services/api/tests/integration/test_collections_get.py
verify:
- docker compose -f docker-compose.dev.yml run --rm api-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_sse.py && uv run --frozen ruff check tests/unit/test_sse.py && uv run --frozen pytest -q --collect-only tests/unit/test_sse.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm api-dev uv run --frozen pytest -q tests/unit/test_sse.py
max_attempts: 3
---

## Goal
Write unit tests for: SSE message mapping. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-api-020 implements it.

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

Fixtures (services/api/tests/conftest.py): `client` (httpx AsyncClient on the app wired to postgres-test + fakes; `client.app.state` holds them), `session` (AsyncSession, tables truncated after each test), `queue` (FakeJobQueue: `.jobs` = [(function, payload, queue)]), `bus` (FakeEventBus: `.published` = [(run_id, event)], `.types()`), `store` (FakeObjectStore: `.objects[(bucket, key)] = (data, content_type)`, buckets uploads + artifacts exist), `settings`, `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z); factories `add_collection(session, name, **kw)`, `add_settings(session, value=None)`. Contract validation: `from tests.contract import errors` → `errors(instance, 'jobs/chunk.schema.json') == []`. Contract fixtures: `tests.conftest.FIXTURES / 'artifact_parse.json'`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. FakeEventBus publish {'type': 'stage.started', 'run_id': 'r'} after subscribing → first yielded item == {'event': 'stage.started', 'data': '{"type":"stage.started","run_id":"r"}'}
2. events without 'type' or with non-str type are skipped
3. events of other run ids are not yielded
4. unicode in event data is preserved (json.loads(item['data']) equals the event)

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
