from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.models import QueryRunRow
from rag_api.schemas.runs import QueryRunCreate, QueryRunOut, QueryRunPage


async def load_query_run(session: AsyncSession, run_id: str) -> QueryRunRow:
    """404 RUN_NOT_FOUND (details.run_id)."""
    raise NotImplementedError("not implemented")


async def query_run_out(session: AsyncSession, run_id: str) -> QueryRunOut:
    raise NotImplementedError("not implemented")


async def create_query_run(session: AsyncSession, body: QueryRunCreate) -> QueryRunOut:
    """404 COLLECTION_NOT_FOUND. Question stored stripped; empty after strip -> VALIDATION_ERROR
    (details.field='question')."""
    raise NotImplementedError("not implemented")


async def list_query_runs(
    session: AsyncSession, limit: int, offset: int, collection_id: str | None
) -> QueryRunPage:
    """Order created_at desc, id desc."""
    raise NotImplementedError("not implemented")
