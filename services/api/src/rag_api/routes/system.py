from typing import Any

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.config import Settings
from rag_api.db.session import get_session
from rag_api.deps import get_http, get_qdrant, get_redis, get_store, settings_dep
from rag_api.qdrant_read import QdrantReader
from rag_api.s3 import ObjectStore
from rag_api.schemas.settings import ModelCatalog
from rag_api.schemas.system import PipelineGraphList, Status
from rag_api.services import models_catalog, pipeline_graphs, status

router = APIRouter(tags=["system"])


@router.get("/status", response_model=Status)
async def get_status(
    session: AsyncSession = Depends(get_session),
    redis: Any = Depends(get_redis),
    store: ObjectStore = Depends(get_store),
    qdrant: QdrantReader = Depends(get_qdrant),
    http: httpx.AsyncClient = Depends(get_http),
    settings: Settings = Depends(settings_dep),
) -> Status:
    return await status.get_status(session, redis, store, qdrant, http, settings)


@router.get("/models", response_model=ModelCatalog)
async def get_models(
    session: AsyncSession = Depends(get_session), http: httpx.AsyncClient = Depends(get_http)
) -> ModelCatalog:
    return await models_catalog.get_catalog(session, http)


@router.get("/pipeline-graphs", response_model=PipelineGraphList)
async def list_pipeline_graphs(session: AsyncSession = Depends(get_session)) -> PipelineGraphList:
    return await pipeline_graphs.list_graphs(session)


@router.get("/pipeline-graphs/{stage}/{variant}")
async def get_pipeline_graph(
    stage: str, variant: str, session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    return await pipeline_graphs.get_graph(session, stage, variant)
