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
