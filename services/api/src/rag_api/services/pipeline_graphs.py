from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.catalog import INGEST_STAGES, QUERY_STAGES
from rag_api.db.models import PipelineGraphRow
from rag_api.errors import AppError
from rag_api.ids import utcnow
from rag_api.schemas.system import PipelineGraphList

# pipeline stage order for list_graphs: ingest stages first, then query stages
STAGE_ORDER: list[str] = [*INGEST_STAGES, *QUERY_STAGES]


async def put_graph(session: AsyncSession, stage: str, variant: str, graph: dict[str, Any]) -> None:
    """graph['stage'] != stage or graph['variant'] != variant -> VALIDATION_ERROR
    (details.field='stage' or 'variant'). Upsert row, updated_at utcnow."""
    if graph.get("stage") != stage:
        raise AppError("VALIDATION_ERROR", details={"field": "stage"})
    if graph.get("variant") != variant:
        raise AppError("VALIDATION_ERROR", details={"field": "variant"})
    row = await session.get(PipelineGraphRow, (stage, variant))
    if row is None:
        row = PipelineGraphRow(stage=stage, variant=variant, graph=graph, updated_at=utcnow())
        session.add(row)
    else:
        row.graph = graph
        row.updated_at = utcnow()
    await session.flush()


async def list_graphs(session: AsyncSession) -> PipelineGraphList:
    """Order: stage pipeline order (parse, chunk, embed, store, transform, retrieve, rerank,
    generate), then variant ascending."""
    rows = (await session.scalars(select(PipelineGraphRow))).all()
    index = {stage: i for i, stage in enumerate(STAGE_ORDER)}
    ordered = sorted(rows, key=lambda row: (index.get(row.stage, len(index)), row.variant))
    return PipelineGraphList(items=[row.graph for row in ordered])


async def get_graph(session: AsyncSession, stage: str, variant: str) -> dict[str, Any]:
    """404 PIPELINE_GRAPH_NOT_FOUND (details.stage, details.variant)."""
    row = await session.get(PipelineGraphRow, (stage, variant))
    if row is None:
        raise AppError("PIPELINE_GRAPH_NOT_FOUND", details={"stage": stage, "variant": variant})
    return row.graph
