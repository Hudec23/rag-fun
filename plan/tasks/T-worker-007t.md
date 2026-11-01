---
id: T-worker-007t
kind: test
feature: F-live-progress
title: 'Write tests: RedisEventPublisher'
service: worker
depends_on: []
edit:
- services/worker/tests/integration/test_publisher.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_publisher.py && uv run --frozen ruff check tests/integration/test_publisher.py && uv run --frozen pytest -q --collect-only tests/integration/test_publisher.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/integration/test_publisher.py
max_attempts: 3
---

## Goal
Write unit tests for: RedisEventPublisher. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-007 implements it.

## Context
Integration test against redis-test (redis.asyncio.from_url(REDIS_URL)).

Stub in `services/worker/src/rag_worker/publisher.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Progress events on Redis channel 'events:{run_id}' (contracts/events/*.schema.json)."""
from typing import Any, Protocol


class EventPublisher(Protocol):
    async def publish(self, run_id: str, event: dict[str, Any]) -> None: ...

class RedisEventPublisher:
    """redis.publish(f'events:{run_id}', json.dumps(event, separators=(',', ':'))). Errors are logged
    and swallowed (events are lossy by contract)."""

    def __init__(self, redis: Any) -> None:
        self.redis = redis

    async def publish(self, run_id: str, event: dict[str, Any]) -> None:
        raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. publish('r1', {'type': 'stage.started', 'x': 'ü'}) → a raw subscriber on 'events:r1' receives a message whose json.loads equals the event
2. message is compact JSON (no spaces after ':' or ',')
3. redis client whose publish raises ConnectionError → publish returns without raising

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
