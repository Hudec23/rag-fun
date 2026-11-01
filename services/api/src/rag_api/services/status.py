from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.config import Settings
from rag_api.qdrant_read import QdrantReader
from rag_api.s3 import ObjectStore
from rag_api.schemas.system import Status


async def get_status(
    session: AsyncSession,
    redis: Any,
    store: ObjectStore,
    qdrant: QdrantReader,
    http: httpx.AsyncClient,
    settings: Settings,
) -> Status:
    """8 components in schemas.system.COMPONENT_ORDER, each check timeout 2 s, never raises.
    worker-ingest/worker-query: redis EXISTS 'ragfun:worker:{queue}:heartbeat'. postgres: SELECT 1.
    redis: PING. qdrant: qdrant.client.get_collections(). s3: store.head_bucket(uploads).
    ollama: GET {app_settings.ollama_url}/api/tags. latency_ms = elapsed ms (int); detail = error
    text (≤500 chars) or 'heartbeat missing' for workers, None when ok."""
    raise NotImplementedError("not implemented")
