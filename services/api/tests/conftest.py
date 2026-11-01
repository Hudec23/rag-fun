"""Shared fixtures. DB fixtures connect to postgres-test (DATABASE_URL) only when requested."""

import os
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from rag_api import ids
from rag_api.config import Settings, get_settings
from rag_api.db.models import Base, CollectionRow, SettingsRow
from rag_api.db.session import make_engine, make_sessionmaker
from rag_api.main import create_app
from tests.fakes import FakeEventBus, FakeJobQueue, FakeObjectStore

REPO_ROOT = Path(__file__).resolve().parents[3]  # /workspace
CONTRACTS = REPO_ROOT / "contracts"
FIXTURES = REPO_ROOT / "tests" / "contract_fixtures"

FROZEN = datetime(2026, 11, 1, 18, 22, 5, 123000, tzinfo=UTC)


@pytest.fixture
def frozen_now(monkeypatch: pytest.MonkeyPatch) -> datetime:
    """ids.utcnow() returns 2026-11-01T18:22:05.123Z."""
    monkeypatch.setattr(ids, "_clock", lambda: FROZEN)
    return FROZEN


@pytest.fixture
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    eng = make_engine(os.environ["DATABASE_URL"])
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def maker(engine: AsyncEngine) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    m = make_sessionmaker(engine)
    yield m
    async with engine.begin() as conn:
        names = ", ".join(t.name for t in reversed(Base.metadata.sorted_tables))
        await conn.execute(text(f"TRUNCATE {names} CASCADE"))


@pytest.fixture
async def session(maker: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with maker() as s:
        yield s
        await s.commit()


@pytest.fixture
def queue() -> FakeJobQueue:
    return FakeJobQueue()


@pytest.fixture
def bus() -> FakeEventBus:
    return FakeEventBus()


@pytest.fixture
def store() -> FakeObjectStore:
    s = FakeObjectStore()
    s.buckets |= {"uploads", "artifacts"}
    return s


@pytest.fixture
async def client(
    maker: async_sessionmaker[AsyncSession],
    queue: FakeJobQueue,
    bus: FakeEventBus,
    store: FakeObjectStore,
) -> AsyncIterator[httpx.AsyncClient]:
    """App wired to postgres-test + fakes (queue, events, S3). Qdrant/http/redis: real test infra
    clients are created on demand by the test via app.state if needed."""
    app = create_app()
    app.state.sessionmaker = maker
    app.state.queue = queue
    app.state.events = bus
    app.state.store = store
    app.state.http = httpx.AsyncClient()
    app.state.redis = None
    app.state.qdrant = None
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        c.app = app  # type: ignore[attr-defined]
        yield c
    await app.state.http.aclose()


# ---------------------------------------------------------------- factories


async def add_collection(session: AsyncSession, name: str = "default", **kw: Any) -> CollectionRow:
    cid = ids.new_id()
    row = CollectionRow(
        id=cid,
        name=name,
        qdrant_name="rf_" + cid.replace("-", ""),
        dense_model=kw.get("dense_model", "bge-m3"),
        dense_dims=kw.get("dense_dims", 1024),
        sparse_model=kw.get("sparse_model", "Qdrant/bm25"),
        created_at=kw.get("created_at", ids.utcnow()),
    )
    session.add(row)
    await session.flush()
    return row


async def add_settings(session: AsyncSession, value: dict[str, Any] | None = None) -> SettingsRow:
    row = SettingsRow(
        key="app",
        value=value
        or {
            "chat_provider": "ollama",
            "ollama": {"url": "http://ollama-fake:11434", "chat_model": "qwen3:8b"},
            "anthropic": {"model": "claude-sonnet-5-5", "api_key": None},
            "openai_compatible": {"base_url": None, "model": None, "api_key": None},
            "reranker_model": "Xenova/ms-marco-MiniLM-L-6-v2",
        },
        updated_at=ids.utcnow(),
    )
    session.add(row)
    await session.flush()
    return row


@pytest.fixture
def no_network(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Unit tests: fail loudly if anything opens a real socket."""
    import socket

    def guard(*_: Any, **__: Any) -> None:
        raise RuntimeError("network access in a unit test")

    monkeypatch.setattr(socket, "create_connection", guard)
    yield
