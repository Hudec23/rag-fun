"""Query runs (F-transform): create runs per question, get/list runs, stage progress."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.models import QueryRunRow, StageRunRow
from rag_api.errors import AppError
from rag_api.ids import new_id, to_iso, utcnow
from rag_api.schemas.base import PageInfo
from rag_api.schemas.runs import QueryRunCreate, QueryRunOut, QueryRunPage, QueryStages, StageRunOut
from rag_api.services import collections, stages


def _stage_out(row: StageRunRow | None) -> StageRunOut | None:
    """A stage's latest row -> DTO; None if the stage never ran."""
    if row is None:
        return None
    return stages.stage_run_out(row)


async def run_out_for(session: AsyncSession, row: QueryRunRow) -> QueryRunOut:
    """Run + latest row per stage (None if never ran) + run_all_pending = plan stages."""
    latest = await stages.latest_rows(session, row.id)
    return QueryRunOut(
        id=row.id,
        collection_id=row.collection_id,
        question=row.question,
        created_at=to_iso(row.created_at),
        run_all_pending=[entry["stage"] for entry in row.run_all_plan],
        stages=QueryStages(
            transform=_stage_out(latest.get("transform")),
            retrieve=_stage_out(latest.get("retrieve")),
            rerank=_stage_out(latest.get("rerank")),
            generate=_stage_out(latest.get("generate")),
        ),
    )


async def load_query_run(session: AsyncSession, run_id: str) -> QueryRunRow:
    """404 RUN_NOT_FOUND (details.run_id)."""
    row = await session.get(QueryRunRow, run_id)
    if row is None:
        raise AppError("RUN_NOT_FOUND", details={"run_id": run_id})
    return row


async def query_run_out(session: AsyncSession, run_id: str) -> QueryRunOut:
    """Run + latest row per stage (None if never ran) + run_all_pending = plan stages."""
    return await run_out_for(session, await load_query_run(session, run_id))


async def create_query_run(session: AsyncSession, body: QueryRunCreate) -> QueryRunOut:
    """404 COLLECTION_NOT_FOUND. Question stored stripped; empty after strip -> VALIDATION_ERROR
    (details.field='question')."""
    await collections.load_collection(session, body.collection_id)
    question = body.question.strip()
    if not question:
        raise AppError("VALIDATION_ERROR", details={"field": "question"})
    row = QueryRunRow(
        id=new_id(),
        collection_id=body.collection_id,
        question=question,
        run_all_plan=[],
        created_at=utcnow(),
    )
    session.add(row)
    await session.flush()
    return await run_out_for(session, row)


async def list_query_runs(
    session: AsyncSession, limit: int, offset: int, collection_id: str | None
) -> QueryRunPage:
    """Order created_at desc, id desc."""
    stmt = select(QueryRunRow)
    count_stmt = select(func.count()).select_from(QueryRunRow)
    if collection_id is not None:
        stmt = stmt.where(QueryRunRow.collection_id == collection_id)
        count_stmt = count_stmt.where(QueryRunRow.collection_id == collection_id)
    total = await session.scalar(count_stmt)
    rows = (
        await session.scalars(
            stmt.order_by(QueryRunRow.created_at.desc(), QueryRunRow.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    items = [await run_out_for(session, row) for row in rows]
    return QueryRunPage(
        items=items,
        page=PageInfo(total=int(total or 0), limit=limit, offset=offset),
    )
