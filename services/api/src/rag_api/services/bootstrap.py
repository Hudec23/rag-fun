"""Idempotent startup bootstrap (SYSTEM.md §5 Bootstrap)."""

from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.config import Settings
from rag_api.s3 import ObjectStore


def run_migrations(database_url: str) -> None:
    """alembic upgrade head programmatically: cfg = alembic.config.Config();
    cfg.set_main_option('script_location', str(Path(__file__).resolve().parents[3] / 'alembic'))
    (= services/api/alembic in dev, /app/alembic in the runtime image); cfg.attributes['database_url']
    = database_url; alembic.command.upgrade(cfg, 'head'). Synchronous: alembic/env.py calls
    asyncio.run, so callers inside an event loop must use asyncio.to_thread(run_migrations, url)."""
    raise NotImplementedError("not implemented")


async def seed(session: AsyncSession, store: ObjectStore, settings: Settings) -> None:
    """1. store.ensure_bucket(uploads) and (artifacts). 2. If no settings row 'app': insert
    catalog.DEFAULT_SETTINGS with ollama.url = settings.ollama_url_default. 3. If no collection exists:
    create catalog.DEFAULT_COLLECTION via collections.create_collection. Commit. Running twice changes
    nothing."""
    raise NotImplementedError("not implemented")
