---
id: T-worker-010t
kind: test
feature: F-status
title: 'Write tests: worker heartbeat'
service: worker
depends_on: []
edit:
- services/worker/tests/integration/test_heartbeat.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/integration/test_heartbeat.py && uv run --frozen ruff check tests/integration/test_heartbeat.py && uv run --frozen pytest -q --collect-only tests/integration/test_heartbeat.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/integration/test_heartbeat.py
max_attempts: 3
---

## Goal
Write unit tests for: worker heartbeat. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-010 implements it.

## Context
Integration test against redis-test.

Stub in `services/worker/src/rag_worker/heartbeat.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Worker liveness key (contracts/events/worker.heartbeat.schema.json)."""
from collections.abc import Callable
from typing import Any


def heartbeat_key(queue: str) -> str:
    return f"ragfun:worker:{queue}:heartbeat"

def heartbeat_value(queue: str, backend: str, jobs_running: int, ts: str) -> dict[str, Any]:
    return {"queue": queue, "ts": ts, "model_backend": backend, "jobs_running": jobs_running}

async def beat_once(redis: Any, queue: str, backend: str, jobs_running: int) -> None:
    """SET heartbeat_key(queue) json(heartbeat_value(..., ts=to_iso(utcnow()))) EX 30."""
    raise NotImplementedError("not implemented")

async def heartbeat_loop(
    redis: Any, queue: str, backend: str, running: Callable[[], int], interval: float = 10.0
) -> None:
    """Forever: beat_once(..., running()); sleep(interval). Errors are logged, loop continues."""
    raise NotImplementedError("not implemented")
```

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. beat_once(redis, 'ingest', 'fake', 2) → key 'ragfun:worker:ingest:heartbeat' exists with TTL 25..30 s and JSON value validating events/worker.heartbeat.schema.json with jobs_running 2
2. heartbeat_loop with interval 0.05 called for ~0.2 s (asyncio.wait_for … cancel) writes the key and uses running() each time
3. heartbeat_loop survives a redis error on one beat (stub redis raising once) and keeps going

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
