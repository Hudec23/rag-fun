"""Progress events on Redis channel 'events:{run_id}' (contracts/events/*.schema.json)."""

import json
from typing import Any, Protocol

import structlog
from redis.exceptions import RedisError

log = structlog.get_logger()


class EventPublisher(Protocol):
    async def publish(self, run_id: str, event: dict[str, Any]) -> None: ...


class RedisEventPublisher:
    """redis.publish(f'events:{run_id}', json.dumps(event, separators=(',', ':'))). Errors are logged
    and swallowed (events are lossy by contract)."""

    def __init__(self, redis: Any) -> None:
        self.redis = redis

    async def publish(self, run_id: str, event: dict[str, Any]) -> None:
        try:
            await self.redis.publish(f"events:{run_id}", json.dumps(event, separators=(",", ":")))
        except RedisError as e:
            log.warning("event publish failed", run_id=run_id, error=str(e)[:300])
