"""Unit tests for sse_messages in rag_api.services.sse: mapping EventBus events to SSE frames."""

import asyncio
import json
from typing import Any

from rag_api.services.sse import sse_messages
from tests.fakes import FakeEventBus


def publish_after_subscription(
    bus: FakeEventBus, publishes: list[tuple[str, dict[str, Any]]]
) -> asyncio.Task[None]:
    """Publish (run_id, event) pairs one tick later, so the sse stream is already subscribed."""

    async def _publish() -> None:
        await asyncio.sleep(0)
        for run_id, event in publishes:
            await bus.publish(run_id, event)

    return asyncio.create_task(_publish())


async def first_sse_item(
    bus: FakeEventBus, run_id: str, publishes: list[tuple[str, dict[str, Any]]]
) -> dict[str, Any]:
    """First frame yielded by sse_messages(bus, run_id) once the given events are published."""
    agen = sse_messages(bus, run_id)
    pub = publish_after_subscription(bus, publishes)
    try:
        return await asyncio.wait_for(agen.__anext__(), 2)
    finally:
        await pub
        await agen.aclose()


async def test_event_published_after_subscribing_is_yielded_as_sse_frame(
    bus: FakeEventBus,
) -> None:
    item = await first_sse_item(bus, "r", [("r", {"type": "stage.started", "run_id": "r"})])
    assert item == {"event": "stage.started", "data": '{"type":"stage.started","run_id":"r"}'}


async def test_events_without_str_type_are_skipped(bus: FakeEventBus) -> None:
    item = await first_sse_item(
        bus,
        "r",
        [
            ("r", {"run_id": "r"}),
            ("r", {"type": None}),
            ("r", {"type": 42}),
            ("r", {"type": "run.updated", "run_id": "r"}),
        ],
    )
    assert item == {"event": "run.updated", "data": '{"type":"run.updated","run_id":"r"}'}


async def test_events_of_other_runs_are_not_yielded(bus: FakeEventBus) -> None:
    item = await first_sse_item(
        bus,
        "r",
        [
            ("other", {"type": "stage.started", "run_id": "other"}),
            ("r", {"type": "stage.started", "run_id": "r"}),
        ],
    )
    assert item == {"event": "stage.started", "data": '{"type":"stage.started","run_id":"r"}'}
    assert ("other", {"type": "stage.started", "run_id": "other"}) in bus.published


async def test_unicode_in_event_data_is_preserved(bus: FakeEventBus) -> None:
    event = {"type": "stage.finished", "run_id": "r", "label": "café ☕ 東京"}
    item = await first_sse_item(bus, "r", [("r", event)])
    assert item["event"] == "stage.finished"
    assert json.loads(item["data"]) == event
