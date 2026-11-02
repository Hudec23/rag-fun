"""Integration tests for GET /api/v1/status (rag_api.services.status.get_status).
Real postgres via the `client`/`session` fixtures; redis and the qdrant client are
small stubs wired onto app.state, outbound HTTP (ollama) is mocked with respx so no
real sockets are opened. The service is still a stub — every test here is red until
T-api-023."""

import asyncio
import time
from typing import Any

import httpx
import respx
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.qdrant_read import QdrantReader
from rag_api.schemas.system import COMPONENT_ORDER
from tests.conftest import add_settings
from tests.fakes import FakeObjectStore

OLLAMA_TAGS_URL = "http://ollama-fake:11434/api/tags"
HEARTBEATS = {
    "ragfun:worker:ingest:heartbeat": 1,
    "ragfun:worker:query:heartbeat": 1,
}


class StubRedis:
    """ping() -> True (sleeps 10 s first when hang_ping); exists(*keys) counts hits in heartbeats."""

    def __init__(self, heartbeats: dict[str, int], hang_ping: bool = False) -> None:
        self.heartbeats = heartbeats
        self.hang_ping = hang_ping

    async def ping(self) -> bool:
        if self.hang_ping:
            await asyncio.sleep(10)
        return True

    async def exists(self, *keys: str) -> int:
        return sum(1 for k in keys if k in self.heartbeats)


class StubQdrantClient:
    async def get_collections(self) -> list[Any]:
        return []


def _wire(client: httpx.AsyncClient, redis: StubRedis) -> None:
    """The `client` fixture leaves redis/qdrant None; ASGITransport never runs lifespan."""
    app = client.app  # type: ignore[attr-defined]
    app.state.redis = redis
    app.state.qdrant = QdrantReader(StubQdrantClient())


async def test_all_healthy(client: httpx.AsyncClient, session: AsyncSession) -> None:
    await add_settings(session)
    await session.commit()
    _wire(client, StubRedis(HEARTBEATS))

    async with respx.mock() as mock:
        mock.get(OLLAMA_TAGS_URL).respond(json={"models": []})
        r = await client.get("/api/v1/status")
        assert r.status_code == 200
        components = r.json()["components"]

    assert [c["name"] for c in components] == COMPONENT_ORDER
    for c in components:
        assert c["ok"] is True
        assert c["detail"] is None
        assert c["latency_ms"] >= 0


async def test_worker_query_heartbeat_missing(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    await add_settings(session)
    await session.commit()
    _wire(client, StubRedis({"ragfun:worker:ingest:heartbeat": 1}))

    async with respx.mock() as mock:
        mock.get(OLLAMA_TAGS_URL).respond(json={"models": []})
        r = await client.get("/api/v1/status")
        assert r.status_code == 200
        by = {c["name"]: c for c in r.json()["components"]}

    assert by["worker-query"]["ok"] is False
    assert by["worker-query"]["detail"] == "heartbeat missing"
    for name in COMPONENT_ORDER:
        if name != "worker-query":
            assert by[name]["ok"] is True
            assert by[name]["detail"] is None


async def test_s3_down(
    client: httpx.AsyncClient, session: AsyncSession, store: FakeObjectStore
) -> None:
    store.fail = True
    await add_settings(session)
    await session.commit()
    _wire(client, StubRedis(HEARTBEATS))

    async with respx.mock() as mock:
        mock.get(OLLAMA_TAGS_URL).respond(json={"models": []})
        r = await client.get("/api/v1/status")
        assert r.status_code == 200
        by = {c["name"]: c for c in r.json()["components"]}

    assert by["s3"]["ok"] is False
    assert by["s3"]["detail"] == "fake s3 down"
    for name in COMPONENT_ORDER:
        if name != "s3":
            assert by[name]["ok"] is True
            assert by[name]["detail"] is None


async def test_ollama_connect_error(client: httpx.AsyncClient, session: AsyncSession) -> None:
    await add_settings(session)
    await session.commit()
    _wire(client, StubRedis(HEARTBEATS))

    async with respx.mock() as mock:
        mock.get(OLLAMA_TAGS_URL).mock(side_effect=httpx.ConnectError("ollama down"))
        r = await client.get("/api/v1/status")
        assert r.status_code == 200
        by = {c["name"]: c for c in r.json()["components"]}

    assert by["ollama"]["ok"] is False
    assert by["ollama"]["detail"] is not None
    assert "ollama down" in by["ollama"]["detail"]
    for name in COMPONENT_ORDER:
        if name != "ollama":
            assert by[name]["ok"] is True
            assert by[name]["detail"] is None


async def test_hanging_check_times_out(client: httpx.AsyncClient, session: AsyncSession) -> None:
    await add_settings(session)
    await session.commit()
    _wire(client, StubRedis(HEARTBEATS, hang_ping=True))

    async with respx.mock() as mock:
        mock.get(OLLAMA_TAGS_URL).respond(json={"models": []})
        start = time.monotonic()
        r = await client.get("/api/v1/status")
        elapsed = time.monotonic() - start
        assert r.status_code == 200
        by = {c["name"]: c for c in r.json()["components"]}

    assert elapsed < 5
    assert by["redis"]["ok"] is False
    assert by["redis"]["detail"] is not None
    for name in COMPONENT_ORDER:
        if name != "redis":
            assert by[name]["ok"] is True
            assert by[name]["detail"] is None
