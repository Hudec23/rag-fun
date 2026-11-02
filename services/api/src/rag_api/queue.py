"""Enqueue worker jobs (contracts/jobs/*.schema.json) on arq queues 'ingest' / 'query'."""

from typing import Any, Protocol


class JobQueue(Protocol):
    async def enqueue(self, function: str, payload: dict[str, Any], queue: str) -> None:
        """function = job name (e.g. 'chunk'); payload = the job JSON; queue = 'ingest' | 'query'."""
        ...


class ArqJobQueue:
    """Wraps arq.connections.ArqRedis: enqueue_job(function, payload, _queue_name=queue).
    _job_id = payload['stage_run_id'] when present (arq then drops duplicates)."""

    def __init__(self, redis: Any) -> None:
        self.redis = redis

    async def enqueue(self, function: str, payload: dict[str, Any], queue: str) -> None:
        await self.redis.enqueue_job(
            function, payload, _job_id=payload.get("stage_run_id"), _queue_name=queue
        )
