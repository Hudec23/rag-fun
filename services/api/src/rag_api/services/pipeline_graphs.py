from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.schemas.system import PipelineGraphList


async def put_graph(session: AsyncSession, stage: str, variant: str, graph: dict[str, Any]) -> None:
    """graph['stage'] != stage or graph['variant'] != variant -> VALIDATION_ERROR
    (details.field='stage' or 'variant'). Upsert row, updated_at utcnow."""
    raise NotImplementedError("not implemented")


async def list_graphs(session: AsyncSession) -> PipelineGraphList:
    """Order: stage pipeline order (parse, chunk, embed, store, transform, retrieve, rerank,
    generate), then variant ascending."""
    raise NotImplementedError("not implemented")


async def get_graph(session: AsyncSession, stage: str, variant: str) -> dict[str, Any]:
    """404 PIPELINE_GRAPH_NOT_FOUND (details.stage, details.variant)."""
    raise NotImplementedError("not implemented")
