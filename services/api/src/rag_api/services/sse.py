import json
from collections.abc import AsyncIterator
from typing import Any

from rag_api.events import EventBus


async def sse_messages(events: EventBus, run_id: str) -> AsyncIterator[dict[str, Any]]:
    """For every event from events.subscribe(run_id) yield {'event': event['type'],
    'data': json.dumps(event, separators=(',', ':'))} unchanged otherwise. Events without a str
    'type' are skipped."""
    async for event in events.subscribe(run_id):
        event_type = event.get("type")
        if not isinstance(event_type, str):
            continue
        yield {"event": event_type, "data": json.dumps(event, separators=(",", ":"))}
