"""Idempotent startup bootstrap (SYSTEM.md §5 Bootstrap)."""

from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.config import Settings
from rag_api.s3 import ObjectStore


def run_migrations(database_url: str) -> None:
    """alembic upgrade head programmatically (Config('alembic.ini') with script_location of the
    package root, attributes['database_url'] = database_url)."""
    raise NotImplementedError("not implemented")


async def seed(session: AsyncSession, store: ObjectStore, settings: Settings) -> None:
    """1. store.ensure_bucket(uploads) and (artifacts). 2. If no settings row 'app': insert
    catalog.DEFAULT_SETTINGS with ollama.url = settings.ollama_url_default. 3. If no collection exists:
    create catalog.DEFAULT_COLLECTION via collections.create_collection. Commit. Running twice changes
    nothing."""
    raise NotImplementedError("not implemented")
