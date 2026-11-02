"""Status of all components (R-024). One 2 s check per component; a failure is reported
in the component's `detail` field — get_status itself never raises."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.config import Settings
from rag_api.qdrant_read import QdrantReader
from rag_api.s3 import ObjectStore
from rag_api.schemas.system import COMPONENT_ORDER, ComponentName, ComponentStatus, Status
from rag_api.services import app_settings

CHECK_TIMEOUT_S = 2.0
DETAIL_LIMIT = 500
WORKER_HEARTBEATS: dict[ComponentName, str] = {
    "worker-ingest": "ragfun:worker:ingest:heartbeat",
    "worker-query": "ragfun:worker:query:heartbeat",
}


def _detail(exc: BaseException) -> str:
    """Error text of a failed check: never empty, at most DETAIL_LIMIT chars."""
    return (str(exc) or type(exc).__name__)[:DETAIL_LIMIT]


async def _run(name: ComponentName, body: Callable[[], Awaitable[str | None]]) -> ComponentStatus:
    """Run one component check with a 2 s timeout. detail is None when ok, error text otherwise."""
    start = time.perf_counter()
    try:
        detail: str | None = await asyncio.wait_for(body(), timeout=CHECK_TIMEOUT_S)
    except Exception as exc:  # the status endpoint never raises; the error goes to detail
        detail = _detail(exc)
    return ComponentStatus(
        name=name,
        ok=detail is None,
        latency_ms=int((time.perf_counter() - start) * 1000),
        detail=detail,
    )


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

    async def api_detail() -> str | None:
        return None  # this process is serving the request

    async def worker_detail(name: ComponentName) -> str | None:
        if await redis.exists(WORKER_HEARTBEATS[name]):
            return None
        return "heartbeat missing"

    async def postgres_detail() -> str | None:
        await session.execute(text("SELECT 1"))
        return None

    async def redis_detail() -> str | None:
        await redis.ping()
        return None

    async def qdrant_detail() -> str | None:
        await qdrant.client.get_collections()
        return None

    async def s3_detail() -> str | None:
        await store.head_bucket(settings.s3_bucket_uploads)
        return None

    async def ollama_detail() -> str | None:
        url = await app_settings.ollama_url(session)
        resp = await http.get(f"{url}/api/tags", timeout=CHECK_TIMEOUT_S)
        if resp.status_code >= 400:
            return f"ollama HTTP {resp.status_code}"
        return None

    checks: dict[ComponentName, Callable[[], Awaitable[str | None]]] = {
        "api": api_detail,
        "worker-ingest": lambda: worker_detail("worker-ingest"),
        "worker-query": lambda: worker_detail("worker-query"),
        "postgres": postgres_detail,
        "redis": redis_detail,
        "qdrant": qdrant_detail,
        "s3": s3_detail,
        "ollama": ollama_detail,
    }
    components = [await _run(name, checks[name]) for name in COMPONENT_ORDER]
    return Status(components=components)
