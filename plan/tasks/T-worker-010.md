---
id: T-worker-010
kind: impl
feature: F-status
title: worker heartbeat
service: worker
depends_on:
- T-worker-010t
edit:
- services/worker/src/rag_worker/heartbeat.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/integration/test_heartbeat.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/heartbeat.py && uv run --frozen ruff check src/rag_worker/heartbeat.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/integration/test_heartbeat.py
max_attempts: 3
---

## Goal
Implement: worker heartbeat. The tests written by T-worker-010t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
