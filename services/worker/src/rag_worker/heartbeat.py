"""Worker liveness key (contracts/events/worker.heartbeat.schema.json)."""

import asyncio
import json
from collections.abc import Callable
from typing import Any

import structlog

from rag_worker.ids import to_iso, utcnow

log = structlog.get_logger()


def heartbeat_key(queue: str) -> str:
    return f"ragfun:worker:{queue}:heartbeat"


def heartbeat_value(queue: str, backend: str, jobs_running: int, ts: str) -> dict[str, Any]:
    return {"queue": queue, "ts": ts, "model_backend": backend, "jobs_running": jobs_running}


async def beat_once(redis: Any, queue: str, backend: str, jobs_running: int) -> None:
    """SET heartbeat_key(queue) json(heartbeat_value(..., ts=to_iso(utcnow()))) EX 30."""
    value = heartbeat_value(queue, backend, jobs_running, ts=to_iso(utcnow()))
    await redis.set(heartbeat_key(queue), json.dumps(value, separators=(",", ":")), ex=30)


async def heartbeat_loop(
    redis: Any, queue: str, backend: str, running: Callable[[], int], interval: float = 10.0
) -> None:
    """Forever: beat_once(..., running()); sleep(interval). Errors are logged, loop continues."""
    while True:
        try:
            await beat_once(redis, queue, backend, running())
        except Exception as e:  # noqa: BLE001
            log.warning("heartbeat beat failed", queue=queue, error=str(e)[:300])
        await asyncio.sleep(interval)
