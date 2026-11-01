import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from rag_api.config import get_settings
from rag_api.db.models import Base

target_metadata = Base.metadata


def _run(connection) -> None:  # type: ignore[no-untyped-def]
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def _main() -> None:
    url = context.config.attributes.get("database_url") or get_settings().database_url
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        await conn.run_sync(_run)
        await conn.commit()
    await engine.dispose()


asyncio.run(_main())
