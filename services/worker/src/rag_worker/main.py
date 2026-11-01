"""arq entrypoint: `arq rag_worker.main.WorkerSettings`. WORKER_QUEUE selects the job set."""

import asyncio
from typing import Any

import httpx
import structlog
from arq.connections import RedisSettings

from rag_worker.callbacks import ApiClient
from rag_worker.config import get_settings
from rag_worker.heartbeat import heartbeat_loop
from rag_worker.jobs import (
    chunk,
    embed,
    generate,
    maintenance,
    parse,
    rerank,
    retrieve,
    store,
    transform,
)
from rag_worker.logging import configure_logging
from rag_worker.models.registry import build_model_set
from rag_worker.pipelines.graphs import all_graphs
from rag_worker.publisher import RedisEventPublisher
from rag_worker.store import S3ObjectStore

log = structlog.get_logger()

INGEST_FUNCTIONS = [parse.parse, chunk.chunk, embed.embed, store.store]
QUERY_FUNCTIONS = [
    transform.transform,
    retrieve.retrieve,
    rerank.rerank,
    generate.generate,
    maintenance.drop_collection,
    maintenance.delete_points,
]


async def report_graphs(ctx: dict[str, Any]) -> None:
    """Best effort: PUT every pipeline graph; failures are logged, never fatal."""
    try:
        for graph in all_graphs(ctx["models"], ctx["qdrant_url"]):
            await ctx["api"].put_graph(graph)
    except Exception as e:  # noqa: BLE001
        log.warning("pipeline graphs not reported", error=str(e)[:300])


async def startup(ctx: dict[str, Any]) -> None:
    settings = get_settings()
    configure_logging(settings.log_level, f"worker-{settings.worker_queue}")
    ctx["settings"] = settings
    ctx["http"] = httpx.AsyncClient(timeout=30)
    ctx["api"] = ApiClient(ctx["http"], settings.api_internal_url, settings.internal_token)
    ctx["events"] = RedisEventPublisher(ctx["redis"])
    ctx["store"] = S3ObjectStore(settings)
    ctx["models"] = build_model_set(settings.model_backend)
    ctx["qdrant_url"] = settings.qdrant_url
    ctx["running"] = 0
    ctx["heartbeat"] = asyncio.create_task(
        heartbeat_loop(
            ctx["redis"], settings.worker_queue, settings.model_backend, lambda: ctx["running"]
        )
    )
    ctx["graphs"] = asyncio.create_task(report_graphs(ctx))
    log.info("worker started", queue=settings.worker_queue, backend=settings.model_backend)


async def shutdown(ctx: dict[str, Any]) -> None:
    for name in ("heartbeat", "graphs"):
        task = ctx.get(name)
        if task is not None:
            task.cancel()
    await ctx["http"].aclose()


_cfg = get_settings()


class WorkerSettings:
    """arq settings for the queue selected by WORKER_QUEUE."""

    functions = INGEST_FUNCTIONS if _cfg.worker_queue == "ingest" else QUERY_FUNCTIONS
    queue_name = _cfg.worker_queue
    redis_settings = RedisSettings.from_dsn(_cfg.redis_url)
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 2 if _cfg.worker_queue == "ingest" else 4
    job_timeout = 1800
    keep_result = 3600
    max_tries = 1
