"""Integration tests for rag_api.services.bootstrap: run_migrations + seed.
`seed` runs against postgres-test via the `session` fixture with the fake store;
`run_migrations` runs against a throwaway database created on postgres-test.
The service is still a stub — every test here is red until T-api-026."""

import asyncio
import os
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from rag_api.config import Settings
from rag_api.db.models import CollectionRow, SettingsRow
from rag_api.db.session import make_engine
from rag_api.services.bootstrap import run_migrations, seed
from tests.conftest import add_collection
from tests.fakes import FakeObjectStore

CHANGED_SETTINGS = {
    "chat_provider": "anthropic",
    "ollama": {"url": "http://changed:11434", "chat_model": "qwen3:8b"},
    "anthropic": {"model": "claude-sonnet-5-5", "api_key": "sk-ant-kept"},
    "openai_compatible": {"base_url": None, "model": None, "api_key": None},
    "reranker_model": "Xenova/ms-marco-MiniLM-L-6-v2",
}

SCHEMA_TABLES = [
    "batches",
    "collections",
    "files",
    "ingest_runs",
    "pipeline_graphs",
    "query_runs",
    "settings",
    "stage_runs",
]


async def _autocommit(url: str, ddl: str) -> None:
    """Run DDL (CREATE/DROP DATABASE) outside a transaction block."""
    eng = make_engine(url)
    try:
        conn = await eng.connect()
        conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
        try:
            await conn.execute(text(ddl))
        finally:
            await conn.close()
    finally:
        await eng.dispose()


async def _public_table_names(eng: AsyncEngine) -> list[str]:
    async with eng.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables"
                    " WHERE table_schema = 'public' ORDER BY table_name"
                )
            )
        ).all()
    return [name for (name,) in rows]


async def _alembic_versions(eng: AsyncEngine) -> list[str]:
    async with eng.connect() as conn:
        rows = (await conn.execute(text("SELECT version_num FROM alembic_version"))).all()
    return [version for (version,) in rows]


async def test_seed_on_empty_db(
    session: AsyncSession, store: FakeObjectStore, settings: Settings
) -> None:
    await seed(session, store, settings)

    assert store.buckets == {"uploads", "artifacts"}
    settings_row = (await session.execute(select(SettingsRow))).scalars().one()
    assert settings_row.key == "app"
    assert settings_row.value == {
        "chat_provider": "ollama",
        "ollama": {"url": settings.ollama_url_default, "chat_model": "qwen3:8b"},
        "anthropic": {"model": "claude-sonnet-5-5", "api_key": None},
        "openai_compatible": {"base_url": None, "model": None, "api_key": None},
        "reranker_model": "Xenova/ms-marco-MiniLM-L-6-v2",
    }
    collection = (await session.execute(select(CollectionRow))).scalars().one()
    assert collection.name == "default"
    assert collection.dense_model == "bge-m3"
    assert collection.dense_dims == 1024
    assert collection.sparse_model == "Qdrant/bm25"


async def test_seed_twice_does_not_overwrite_existing_settings(
    session: AsyncSession, store: FakeObjectStore, settings: Settings
) -> None:
    await seed(session, store, settings)
    row = (await session.execute(select(SettingsRow))).scalars().one()
    row.value = CHANGED_SETTINGS
    await session.flush()
    await seed(session, store, settings)

    row = (await session.execute(select(SettingsRow))).scalars().one()
    assert row.value == CHANGED_SETTINGS
    collection = (await session.execute(select(CollectionRow))).scalars().one()
    assert collection.name == "default"
    assert store.buckets == {"uploads", "artifacts"}


async def test_seed_skips_default_collection_when_one_exists(
    session: AsyncSession, store: FakeObjectStore, settings: Settings
) -> None:
    await add_collection(session, "mylib")
    await seed(session, store, settings)

    rows = (await session.execute(select(CollectionRow))).scalars().all()
    assert [c.name for c in rows] == ["mylib"]
    settings_row = (await session.execute(select(SettingsRow))).scalars().one()
    assert settings_row.key == "app"
    assert settings_row.value["ollama"]["url"] == settings.ollama_url_default
    assert store.buckets == {"uploads", "artifacts"}


async def test_run_migrations_creates_all_tables_and_second_run_is_no_op() -> None:
    dbname = "ragfun_mig_" + uuid4().hex[:8]
    admin_url = os.environ["DATABASE_URL"]
    mig_url = admin_url.rsplit("/", 1)[0] + "/" + dbname
    eng = make_engine(mig_url)
    try:
        await _autocommit(admin_url, f"CREATE DATABASE {dbname}")
        await asyncio.to_thread(run_migrations, mig_url)

        tables = await _public_table_names(eng)
        assert [t for t in tables if t != "alembic_version"] == SCHEMA_TABLES
        assert "alembic_version" in tables
        assert await _alembic_versions(eng) == ["0001"]

        await asyncio.to_thread(run_migrations, mig_url)
        assert await _public_table_names(eng) == tables
        assert await _alembic_versions(eng) == ["0001"]
    finally:
        await eng.dispose()  # close pooled sessions first, or Postgres refuses the DROP
        await _autocommit(admin_url, f"DROP DATABASE IF EXISTS {dbname}")
