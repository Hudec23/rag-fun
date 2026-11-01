from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import redis.asyncio as aioredis
import structlog
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from qdrant_client import AsyncQdrantClient

from rag_api import VERSION
from rag_api.config import get_settings
from rag_api.db.session import make_engine, make_sessionmaker
from rag_api.errors import install_error_handlers
from rag_api.events import RedisEventBus
from rag_api.logging import configure_logging
from rag_api.qdrant_read import QdrantReader
from rag_api.queue import ArqJobQueue
from rag_api.routes import (
    artifacts,
    collections,
    events,
    files,
    health,
    internal,
    qdrant,
    runs,
    settings,
)
from rag_api.routes import system as system_routes
from rag_api.s3 import S3ObjectStore
from rag_api.services import bootstrap

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    cfg = get_settings()
    configure_logging(cfg.log_level, "api")
    engine = make_engine(cfg.database_url)
    app.state.sessionmaker = make_sessionmaker(engine)
    app.state.redis = aioredis.from_url(cfg.redis_url)
    app.state.queue = ArqJobQueue(await create_pool(RedisSettings.from_dsn(cfg.redis_url)))
    app.state.events = RedisEventBus(app.state.redis)
    app.state.store = S3ObjectStore(cfg)
    app.state.qdrant = QdrantReader(AsyncQdrantClient(url=cfg.qdrant_url))
    app.state.http = httpx.AsyncClient()
    try:
        bootstrap.run_migrations(cfg.database_url)
        async with app.state.sessionmaker() as session:
            await bootstrap.seed(session, app.state.store, cfg)
    except NotImplementedError:
        log.warning("bootstrap not implemented yet")  # walking skeleton only
    log.info("api started", version=VERSION)
    yield
    await app.state.http.aclose()
    await app.state.redis.aclose()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="rag-fun api",
        version=VERSION,
        lifespan=lifespan,
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
    )
    install_error_handlers(app)
    for module in (
        health,
        system_routes,
        collections,
        files,
        runs,
        artifacts,
        events,
        qdrant,
        settings,
    ):
        app.include_router(module.router, prefix="/api/v1")
    app.include_router(internal.router)
    return app


app = create_app()
