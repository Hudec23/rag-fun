"""Idempotent startup bootstrap (SYSTEM.md §5 Bootstrap)."""

from copy import deepcopy
from pathlib import Path
from typing import Any

from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alembic import command
from rag_api.catalog import DEFAULT_COLLECTION, DEFAULT_SETTINGS
from rag_api.config import Settings
from rag_api.db.models import CollectionRow, SettingsRow
from rag_api.ids import utcnow
from rag_api.s3 import ObjectStore
from rag_api.schemas.collections import CollectionCreate
from rag_api.services import collections


def run_migrations(database_url: str) -> None:
    """alembic upgrade head programmatically: cfg = alembic.config.Config();
    cfg.set_main_option('script_location', str(Path(__file__).resolve().parents[3] / 'alembic'))
    (= services/api/alembic in dev, /app/alembic in the runtime image); cfg.attributes['database_url']
    = database_url; alembic.command.upgrade(cfg, 'head'). Synchronous: alembic/env.py calls
    asyncio.run, so callers inside an event loop must use asyncio.to_thread(run_migrations, url)."""
    cfg = Config()
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parents[3] / "alembic"))
    cfg.attributes["database_url"] = database_url
    command.upgrade(cfg, "head")


async def seed(session: AsyncSession, store: ObjectStore, settings: Settings) -> None:
    """1. store.ensure_bucket(uploads) and (artifacts). 2. If no settings row 'app': insert
    catalog.DEFAULT_SETTINGS with ollama.url = settings.ollama_url_default. 3. If no collection exists:
    create catalog.DEFAULT_COLLECTION via collections.create_collection. Commit. Running twice changes
    nothing."""
    await store.ensure_bucket(settings.s3_bucket_uploads)
    await store.ensure_bucket(settings.s3_bucket_artifacts)

    if await session.scalar(select(SettingsRow).where(SettingsRow.key == "app")) is None:
        value: dict[str, Any] = deepcopy(DEFAULT_SETTINGS)
        value["ollama"]["url"] = settings.ollama_url_default
        session.add(SettingsRow(key="app", value=value, updated_at=utcnow()))

    if await session.scalar(select(CollectionRow).limit(1)) is None:
        await collections.create_collection(
            session, CollectionCreate.model_validate(DEFAULT_COLLECTION)
        )

    await session.commit()
