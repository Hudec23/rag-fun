from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sse_starlette.sse import EventSourceResponse

from rag_api.deps import get_events
from rag_api.events import EventBus
from rag_api.schemas.base import Id
from rag_api.services.sse import sse_messages

router = APIRouter(tags=["system"])


@router.get("/events")
async def stream_events(
    run_id: Annotated[Id, Query()], events: EventBus = Depends(get_events)
) -> EventSourceResponse:
    stream: AsyncIterator[dict[str, Any]] = sse_messages(events, run_id)
    return EventSourceResponse(
        stream, ping=15, headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
