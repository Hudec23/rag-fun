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
